from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import tempfile
import time
import errno
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger("rk_flash_tool.upgrade_tool")

_PID_TO_CHIP: dict[int, str] = {
    0x350A: "RK3568",
    0x350B: "RK3588",
    0x350C: "RK3562",
    0x350E: "RK3576",
    0x350F: "RK3506",
    0x330C: "RK3399",
    0x330D: "RK3326",
    0x330A: "RK3368",
    0x330B: "RK3366",
    0x320A: "RK3288",
    0x320B: "RK3229",
    0x320C: "RK3328",
    0x310B: "RK3188",
    0x310C: "RK3128",
    0x310D: "RK3126",
    0x310A: "RK3066B",
    0x300A: "RK3066",
    0x300B: "RK3168",
    0x301A: "RK3036",
    0x180A: "RK1808",
    0x110C: "RV1126",
    0x110B: "RV1109",
}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PLATFORM_KEY = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
_TOOL_BINARY = {"Darwin": "upgrade_tool", "Linux": "upgrade_tool", "Windows": "upgrade_tool.exe"}


class UpgradeToolError(Exception):
    pass


class DeviceNotFoundError(UpgradeToolError):
    pass


class ToolNotFoundError(UpgradeToolError):
    pass


class DriverInstallError(UpgradeToolError):
    pass


@dataclass
class DeviceInfo:
    dev_no: int
    vid: int
    pid: int
    location_id: int
    mode: str
    chip_model: str | None = None
    serial_no: str | None = None

    @property
    def chip_display(self) -> str:
        return self.chip_model or f"Unknown (PID=0x{self.pid:04X})"


def find_upgrade_tool(custom_path: str | None = None) -> Path:
    system = platform.system()
    tool_name = _TOOL_BINARY.get(system, "upgrade_tool")
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
        raise ToolNotFoundError(f"upgrade_tool not found: {custom_path}")

    bundled = _PROJECT_ROOT / "tools" / _PLATFORM_KEY.get(system, "") / tool_name
    if bundled.exists():
        if not os.access(bundled, os.X_OK):
            os.chmod(bundled, 0o755)
        return bundled

    raise ToolNotFoundError(f"Bundled upgrade_tool not found: {bundled}")


class UpgradeTool:
    def __init__(self, tool_path: str | None = None):
        self._tool = find_upgrade_tool(tool_path)
        self._cwd = self._tool.parent
        self._ensure_windows_stdout_nobuffer()

    @property
    def tool_path(self) -> Path:
        return self._tool

    def _ensure_windows_stdout_nobuffer(self) -> None:
        if os.name != "nt":
            return
        cfg = self._cwd / "config.ini"
        if not cfg.exists():
            return
        try:
            lines = cfg.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:  # noqa: BLE001
            return

        changed = False
        new_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("stdout_buffer_off="):
                # Keep tool in default no-buffer stdout mode for real-time progress.
                new_lines.append("#stdout_buffer_off=")
                changed = True
                continue
            new_lines.append(line)
        if not changed:
            return
        try:
            cfg.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            logger.info("Adjusted config.ini: disable stdout_buffer_off for streaming output.")
        except Exception:  # noqa: BLE001
            return

    @staticmethod
    def _windows_no_console_kwargs() -> dict:
        if os.name != "nt":
            return {}
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return {
            "startupinfo": startupinfo,
        }

    def _run(
        self,
        *args: str,
        timeout: int = 60,
        progress_callback: Callable[[int | None, str], None] | None = None,
    ) -> subprocess.CompletedProcess:
        cmd = [str(self._tool)] + list(args)
        no_console = self._windows_no_console_kwargs()
        if progress_callback is None:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._cwd,
                **no_console,
            )

        ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        osc_re = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")

        def normalize_line(text: str) -> str:
            text = osc_re.sub("", text)
            return ansi_re.sub("", text).replace("\x00", "").strip()

        # Windows: use a PowerShell file relay to avoid pipe-buffered flush-at-end behavior.
        if os.name == "nt":
            conpty_result = self._run_windows_conpty(cmd, timeout, progress_callback, normalize_line)
            if conpty_result is not None and conpty_result.returncode == 0:
                return conpty_result
            if conpty_result is not None:
                logger.warning("ConPTY execution failed (rc=%s), falling back.", conpty_result.returncode)

            ps_result = self._run_windows_file_relay(cmd, timeout, progress_callback, normalize_line)
            if ps_result is not None and ps_result.returncode == 0:
                return ps_result
            if ps_result is not None:
                logger.warning("PowerShell relay execution failed (rc=%s), falling back.", ps_result.returncode)

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self._cwd,
                bufsize=0,
                **no_console,
            )
            if proc.stdout is None:
                raise UpgradeToolError("Failed to capture upgrade_tool output on Windows.")

            start = time.time()
            output_parts = bytearray()
            segment = bytearray()
            while True:
                if (time.time() - start) > timeout:
                    proc.kill()
                    raise UpgradeToolError(f"Command timed out: {' '.join(cmd)}")

                b = proc.stdout.read(1)
                if not b:
                    if proc.poll() is not None:
                        break
                    continue

                output_parts.extend(b)
                if b == b"\b":
                    if segment:
                        segment = segment[:-1]
                    continue

                segment.extend(b)

                if b in (b"\r", b"\n"):
                    line_text = segment.decode("utf-8", errors="ignore")
                    if not line_text.strip():
                        # Some tool output on Windows may be GBK/ANSI.
                        line_text = segment.decode("gbk", errors="ignore")
                    line = normalize_line(line_text)
                    if line:
                        progress_callback(None, line)
                    segment = bytearray()

            if segment:
                line_text = segment.decode("utf-8", errors="ignore")
                if not line_text.strip():
                    line_text = segment.decode("gbk", errors="ignore")
                line = normalize_line(line_text)
                if line:
                    progress_callback(None, line)

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=proc.wait(),
                stdout=output_parts.decode("utf-8", errors="ignore"),
                stderr="",
            )

        import pty
        import select

        master_fd, slave_fd = pty.openpty()
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=self._cwd,
            close_fds=True,
            **no_console,
        )
        os.close(slave_fd)

        start = time.time()
        output: list[str] = []
        segment = ""

        while True:
            if (time.time() - start) > timeout:
                proc.kill()
                os.close(master_fd)
                raise UpgradeToolError(f"Command timed out: {' '.join(cmd)}")
            ready, _, _ = select.select([master_fd], [], [], 0.05)
            if not ready:
                if proc.poll() is not None:
                    break
                continue
            try:
                chunk = os.read(master_fd, 4096)
            except OSError as e:
                # PTY on Linux/macOS may raise EIO when child exits; treat as EOF.
                if e.errno == errno.EIO and proc.poll() is not None:
                    break
                raise
            if not chunk:
                if proc.poll() is not None:
                    break
                continue
            text = chunk.decode(errors="ignore")
            output.append(text)
            for ch in text:
                segment += ch
                if ch in ("\r", "\n"):
                    line = normalize_line(segment)
                    if line:
                        progress_callback(None, line)
                    segment = ""

        os.close(master_fd)
        return subprocess.CompletedProcess(args=cmd, returncode=proc.wait(), stdout="".join(output), stderr="")

    def _run_windows_conpty(
        self,
        cmd: list[str],
        timeout: int,
        progress_callback: Callable[[int | None, str], None],
        normalize_line: Callable[[str], str],
    ) -> subprocess.CompletedProcess | None:
        if os.name != "nt":
            return None
        if not cmd:
            return None

        try:
            from winpty import PtyProcess  # type: ignore[import-not-found]
        except Exception as e:  # noqa: BLE001
            logger.info("winpty unavailable, fallback from ConPTY: %s", e)
            return None

        cmdline = subprocess.list2cmdline(cmd)
        try:
            proc = PtyProcess.spawn(cmdline, cwd=str(self._cwd))
        except Exception as e:  # noqa: BLE001
            logger.warning("ConPTY spawn failed, fallback to relay/direct mode: %s", e)
            return None

        start = time.time()
        output: list[str] = []
        segment = ""

        try:
            while True:
                if (time.time() - start) > timeout:
                    try:
                        proc.close()
                    except Exception:  # noqa: BLE001
                        pass
                    raise UpgradeToolError(f"Command timed out: {' '.join(cmd)}")

                try:
                    chunk = proc.read(4096)
                except EOFError:
                    break
                except Exception:  # noqa: BLE001
                    if hasattr(proc, "isalive") and not proc.isalive():
                        break
                    time.sleep(0.03)
                    continue

                if not chunk:
                    if hasattr(proc, "isalive") and not proc.isalive():
                        break
                    time.sleep(0.03)
                    continue

                output.append(chunk)
                for ch in chunk:
                    segment += ch
                    if ch in ("\r", "\n"):
                        line = normalize_line(segment)
                        if line:
                            progress_callback(None, line)
                        segment = ""
        finally:
            if segment:
                line = normalize_line(segment)
                if line:
                    progress_callback(None, line)
            try:
                rc = int(getattr(proc, "exitstatus", 0) or 0)
            except Exception:  # noqa: BLE001
                rc = 0
            try:
                proc.close()
            except Exception:  # noqa: BLE001
                pass

        return subprocess.CompletedProcess(args=cmd, returncode=rc, stdout="".join(output), stderr="")

    def _run_windows_file_relay(
        self,
        cmd: list[str],
        timeout: int,
        progress_callback: Callable[[int | None, str], None],
        normalize_line: Callable[[str], str],
    ) -> subprocess.CompletedProcess | None:
        if os.name != "nt":
            return None
        if not cmd:
            return None

        def ps_quote(s: str) -> str:
            return "'" + s.replace("'", "''") + "'"

        relay_path = Path(tempfile.gettempdir()) / f"rk_flash_tool_{int(time.time() * 1000)}.log"
        relay_ps = (
            f"$out={ps_quote(str(relay_path))}; "
            "if (Test-Path $out) { Remove-Item -Force $out }; "
            "$OutputEncoding=[Console]::OutputEncoding=[System.Text.UTF8Encoding]::UTF8; "
            f"& {ps_quote(cmd[0])} {' '.join(ps_quote(a) for a in cmd[1:])} 2>&1 | "
            "ForEach-Object { $_.ToString() | Out-File -FilePath $out -Append -Encoding utf8 }; "
            "exit $LASTEXITCODE"
        )

        no_console = self._windows_no_console_kwargs()
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", relay_ps],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=self._cwd,
                **no_console,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("PowerShell relay unavailable, fallback to direct mode: %s", e)
            return None

        start = time.time()
        pos = 0
        partial = ""
        collected: list[str] = []

        def drain_new() -> None:
            nonlocal pos, partial
            if not relay_path.exists():
                return
            try:
                with relay_path.open("rb") as f:
                    f.seek(pos)
                    chunk = f.read()
                    pos = f.tell()
            except Exception:  # noqa: BLE001
                return
            if not chunk:
                return
            text = chunk.decode("utf-8", errors="ignore")
            text = partial + text
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            lines = text.split("\n")
            partial = lines.pop() if lines else ""
            for line in lines:
                line = normalize_line(line)
                if not line:
                    continue
                collected.append(line)
                progress_callback(None, line)

        while True:
            if (time.time() - start) > timeout:
                proc.kill()
                raise UpgradeToolError(f"Command timed out: {' '.join(cmd)}")
            drain_new()
            if proc.poll() is not None:
                break
            time.sleep(0.03)

        drain_new()
        if partial:
            line = normalize_line(partial)
            if line:
                collected.append(line)
                progress_callback(None, line)

        rc = proc.wait()
        try:
            relay_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

        return subprocess.CompletedProcess(args=cmd, returncode=rc, stdout="\n".join(collected), stderr="")

    @staticmethod
    def _ok(output: str, *keywords: str) -> bool:
        lower = output.lower()
        return any(k.lower() in lower for k in keywords)

    def is_windows_driver_installed(self) -> bool:
        if os.name != "nt":
            return True
        try:
            out = subprocess.run(
                ["pnputil", "/enum-drivers"],
                capture_output=True,
                text=True,
                timeout=30,
                **self._windows_no_console_kwargs(),
            )
        except Exception:  # noqa: BLE001
            return False
        text = ((out.stdout or "") + (out.stderr or "")).lower()
        return "rockusb.inf" in text

    def install_windows_driver(self) -> None:
        if os.name != "nt":
            return
        from rk_flash_tool.win_driver import DriverPackageError, install_elevated

        try:
            install_elevated()
        except DriverPackageError as e:
            raise DriverInstallError(str(e)) from e

    def list_devices(self) -> list[DeviceInfo]:
        out = self._run("LD")
        return self._parse_device_list((out.stdout or "") + (out.stderr or ""))

    def get_device(self) -> DeviceInfo:
        devices = self.list_devices()
        if not devices:
            raise DeviceNotFoundError("No Rockchip device detected.")
        return devices[0]

    @staticmethod
    def _parse_device_list(output: str) -> list[DeviceInfo]:
        pattern = re.compile(
            r"DevNo=(\d+)\s+Vid=0x([0-9a-fA-F]+),\s*Pid=0x([0-9a-fA-F]+),\s*LocationID=(\w+)\s+(?:Mode=)?(Maskrom|Loader)(?:\s+SerialNo=(\w+))?",
            re.IGNORECASE,
        )
        devices: list[DeviceInfo] = []
        for m in pattern.finditer(output):
            pid = int(m.group(3), 16)
            devices.append(
                DeviceInfo(
                    dev_no=int(m.group(1)),
                    vid=int(m.group(2), 16),
                    pid=pid,
                    location_id=int(m.group(4), 16),
                    mode=m.group(5).capitalize(),
                    chip_model=_PID_TO_CHIP.get(pid),
                    serial_no=m.group(6),
                )
            )
        return devices

    def download_boot(self, loader_path: str | Path) -> bool:
        loader = Path(loader_path)
        if not loader.exists():
            raise UpgradeToolError(f"Loader not found: {loader}")
        out = self._run("DB", str(loader), timeout=120)
        text = (out.stdout or "") + (out.stderr or "")
        if self._ok(text, "download boot ok", "download boot success") or out.returncode == 0:
            return True
        time.sleep(1)
        verify = self._run("LD", timeout=10)
        return "Loader" in ((verify.stdout or "") + (verify.stderr or ""))

    def upgrade_firmware(self, firmware_path: str | Path, progress_callback: Callable[[int | None, str], None] | None = None) -> bool:
        p = Path(firmware_path)
        if not p.exists():
            raise UpgradeToolError(f"Firmware not found: {p}")
        out = self._run("UF", str(p), timeout=1200, progress_callback=progress_callback)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "upgrade firmware ok", "upgrade ok", "success") or out.returncode == 0

    def write_image(self, image_path: str | Path, progress_callback: Callable[[int | None, str], None] | None = None) -> bool:
        p = Path(image_path)
        if not p.exists():
            raise UpgradeToolError(f"Image not found: {p}")
        out = self._run("WL", "0", str(p), timeout=1200, progress_callback=progress_callback)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "write lba ok", "download image ok", "success") or out.returncode == 0

    def reset_device(self) -> bool:
        out = self._run("RD", timeout=30)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "reset device ok", "reset ok", "success") or out.returncode == 0
