from __future__ import annotations

import atexit
import os
import re
import shutil
import subprocess
import tempfile
import time
import errno
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rockchip_flash_tool import resources

_PID_TO_CHIP: dict[int, str] = {
    0x350A: "RK3568",
    0x350B: "RK3588",
    0x350C: "RK3562",
    # xrock puts RK3562 at 0x350D; both are mapped so either reading works.
    0x350D: "RK3562",
    0x350E: "RK3576",
    0x350F: "RK3506",
    0x330C: "RK3399",
    0x330D: "PX30",
    0x330A: "RK3368",
    0x330E: "RK3308",
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
    0x110C: "RV1106",
    0x110B: "RV1109",
}


class UpgradeToolError(Exception):
    pass


class DeviceNotFoundError(UpgradeToolError):
    pass


class AmbiguousDeviceError(UpgradeToolError):
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

    @property
    def key(self) -> str:
        # What `-s` matches on. LD prints it as %x and -s parses base 16, so the
        # tool's own text round-trips; its width is platform-dependent, so never
        # pad it.
        return f"{self.location_id:x}"


def find_upgrade_tool(custom_path: str | None = None) -> Path:
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
        raise ToolNotFoundError(f"upgrade_tool not found: {custom_path}")

    bundled = resources.upgrade_tool_path()
    if bundled.exists():
        if not os.access(bundled, os.X_OK):
            os.chmod(bundled, 0o755)
        return bundled

    raise ToolNotFoundError(f"Bundled upgrade_tool not found: {bundled}")


class UpgradeTool:
    def __init__(self, tool_path: str | None = None):
        self._tool = find_upgrade_tool(tool_path)
        self._cwd = self._tool.parent
        self._device_id: str | None = None
        # upgrade_tool hardcodes its work directory as ~/upgrade_tool (built
        # from $HOME on POSIX, %USERPROFILE% on Windows) and recreates it on
        # every run; there is no flag to turn that off, and config only moves
        # the log subdirectory, never the folder itself. Redirect the child's
        # home to a private temp dir so the user's real home stays clean, and
        # drop the sandbox at exit.
        home_sandbox = tempfile.mkdtemp(prefix="rockchip_upgrade_tool_home_")
        self._tool_env: dict[str, str] = os.environ.copy()
        self._tool_env["HOME"] = home_sandbox
        self._tool_env["USERPROFILE"] = home_sandbox
        atexit.register(shutil.rmtree, home_sandbox, True)
        self._ensure_windows_stdout_nobuffer()

    @property
    def tool_path(self) -> Path:
        return self._tool

    def select(self, device_id: str | None) -> None:
        # Pin later commands to one board by DeviceInfo.key. None falls back to
        # whichever the tool enumerates first, which reorders across a
        # re-enumeration.
        self._device_id = device_id

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
            return
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
        pin: bool = True,
    ) -> subprocess.CompletedProcess:
        # The selector goes before the command: the tool reads "-s" at argv[1]
        # and its value at argv[2], then shifts argv by two. Anywhere else it is
        # just a command argument.
        selector = ["-s", self._device_id] if pin and self._device_id else []
        cmd = [str(self._tool)] + selector + list(args)
        no_console = self._windows_no_console_kwargs()
        if progress_callback is None:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._cwd,
                env=self._tool_env,
                **no_console,
            )

        ansi_re = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        osc_re = re.compile(r"\x1B\].*?(?:\x07|\x1B\\)")

        def normalize_line(text: str) -> str:
            text = osc_re.sub("", text)
            return ansi_re.sub("", text).replace("\x00", "").strip()

        # The POSIX branch below gets its PTY from the stdlib. Windows has no pty
        # module, so it comes from elsewhere -- in three tiers, each losing only
        # progress fidelity, never the ability to flash:
        #   1. pywinpty (ConPTY/WinPTY): a real PTY, so the tool leaves stdout
        #      unbuffered and \r progress arrives live. Measured as UNAVAILABLE in
        #      the shipped layout: spawn() is handed a list2cmdline() string and
        #      shlex-splits it with posix=False, so the quotes it added around
        #      "...\Rockchip Flash Tool\_internal\..." stay inside the token and
        #      the executable lookup fails. It only works when the install path
        #      has no spaces. Passing the argv list to spawn() instead fixes it,
        #      but that moves flashing onto a different tier, so it needs a run
        #      against a real board first.
        #   2. PowerShell relay: what actually carries the shipped Windows app.
        #      Writes to a file this side tails, dodging pipe buffering.
        #   3. Raw pipe: last resort if even PowerShell will not start. Output can
        #      arrive in one burst at the end, but the flash still completes.
        #
        # None is the "this tier is unavailable" signal. A non-zero exit code is
        # the *command's* result, not the channel's: retrying on it re-ran a whole
        # UF against the board, up to three times, on every genuine failure.
        if os.name == "nt":
            conpty_result = self._run_windows_conpty(cmd, timeout, progress_callback, normalize_line)
            if conpty_result is not None:
                return conpty_result

            ps_result = self._run_windows_file_relay(cmd, timeout, progress_callback, normalize_line)
            if ps_result is not None:
                return ps_result

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self._cwd,
                bufsize=0,
                env=self._tool_env,
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
            env=self._tool_env,
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
            return None

        cmdline = subprocess.list2cmdline(cmd)
        try:
            proc = PtyProcess.spawn(cmdline, cwd=str(self._cwd), env=self._tool_env)
        except Exception as e:  # noqa: BLE001
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

        relay_path = Path(tempfile.gettempdir()) / f"rockchip_flash_tool_{int(time.time() * 1000)}.log"
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
                env=self._tool_env,
                **no_console,
            )
        except Exception as e:  # noqa: BLE001
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
        from rockchip_flash_tool.win_driver import DriverPackageError, install_elevated

        try:
            install_elevated()
        except DriverPackageError as e:
            raise DriverInstallError(str(e)) from e

    def list_devices(self) -> list[DeviceInfo]:
        # Unpinned: LD runs before device selection and always lists everything.
        out = self._run("LD", pin=False)
        return self._parse_device_list((out.stdout or "") + (out.stderr or ""))

    def get_device(self) -> DeviceInfo:
        devices = self.list_devices()
        if not devices:
            raise DeviceNotFoundError("No Rockchip device detected.")
        if self._device_id is None:
            return devices[0]
        matches = [dev for dev in devices if dev.key == self._device_id]
        if not matches:
            raise DeviceNotFoundError(f"Device @{self._device_id} is no longer connected.")
        # LocationID masks every USB hub level to 4 bits, so distinct port paths
        # can alias. `-s` answers that by taking the first match; refuse instead.
        if len(matches) > 1:
            raise AmbiguousDeviceError(
                f"{len(matches)} devices report LocationID {self._device_id}."
            )
        return matches[0]

    @staticmethod
    def _parse_device_list(output: str) -> list[DeviceInfo]:
        pattern = re.compile(
            r"DevNo=(\d+)\s+Vid=0x([0-9a-fA-F]+),\s*Pid=0x([0-9a-fA-F]+),\s*LocationID=(\w+)\s+(?:Mode=)?(Maskrom|Loader)(?:\s+SerialNo=(\w+))?",
            re.IGNORECASE,
        )
        devices: list[DeviceInfo] = []
        for m in pattern.finditer(output):
            pid = int(m.group(3), 16)
            mode = m.group(5).capitalize()
            # A board in Maskrom has no serial number to report, and the tool
            # fills the field with whatever its platform build uses -- an empty
            # string on macOS, the literal "rockchip" on Windows. Neither is a
            # serial, so nothing downstream should be told it has one.
            serial_no = m.group(6) if mode != "Maskrom" else None
            devices.append(
                DeviceInfo(
                    dev_no=int(m.group(1)),
                    vid=int(m.group(2), 16),
                    pid=pid,
                    location_id=int(m.group(4), 16),
                    mode=mode,
                    chip_model=_PID_TO_CHIP.get(pid),
                    serial_no=serial_no,
                )
            )
        return devices

    def download_boot(self, loader_path: str | Path) -> bool:
        loader = Path(loader_path)
        if not loader.exists():
            raise UpgradeToolError(f"Loader not found: {loader}")
        out = self._run("DB", str(loader), timeout=120)
        text = (out.stdout or "") + (out.stderr or "")
        # No second opinion from LD: it cannot give one. A board running its spl
        # loader still lists as Mode=Maskrom, so a successful DB reads as a
        # failure, and the listing covers every board, so another one sitting in
        # Loader reads as a success for this one. DB saying neither "ok" nor
        # exit 0 is the strongest signal available.
        return self._ok(text, "download boot ok", "download boot success") or out.returncode == 0

    def upgrade_firmware(self, firmware_path: str | Path, progress_callback: Callable[[int | None, str], None] | None = None) -> bool:
        p = Path(firmware_path)
        if not p.exists():
            raise UpgradeToolError(f"Firmware not found: {p}")
        out = self._run("UF", str(p), timeout=1200, progress_callback=progress_callback)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "upgrade firmware ok") or out.returncode == 0

    def write_image(self, image_path: str | Path, progress_callback: Callable[[int | None, str], None] | None = None) -> bool:
        p = Path(image_path)
        if not p.exists():
            raise UpgradeToolError(f"Image not found: {p}")
        out = self._run("WL", "0", str(p), timeout=1200, progress_callback=progress_callback)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "download image ok") or out.returncode == 0

    def reset_device(self) -> bool:
        out = self._run("RD", timeout=30)
        text = (out.stdout or "") + (out.stderr or "")
        return self._ok(text, "reset device ok") or out.returncode == 0
