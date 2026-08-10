"""Windows-only. Import lazily; ctypes.wintypes is unavailable on other platforms."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

from rk_flash_tool import resources

ELEVATED_FLAG = "--install-rockusb-driver"

# The elevated child is hidden and has no console, so its exit code is the only
# channel back. Anything other than these two is the verbatim Win32 error from
# DiInstallDriverW; the sentinel is picked so it cannot be mistaken for one.
EXIT_OK = 0
EXIT_BAD_ARGS = 0x0E03

_EXIT_MESSAGES = {
    EXIT_BAD_ARGS: "Internal error: invalid driver installation request.",
}

_DRIVER_ROOT = resources.windows_driver_dir()
_ERROR_CANCELLED = 1223
_WAIT_OBJECT_0 = 0


class SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


class OSVERSIONINFOEXW(ctypes.Structure):
    _fields_ = [
        ("dwOSVersionInfoSize", wintypes.DWORD),
        ("dwMajorVersion", wintypes.DWORD),
        ("dwMinorVersion", wintypes.DWORD),
        ("dwBuildNumber", wintypes.DWORD),
        ("dwPlatformId", wintypes.DWORD),
        ("szCSDVersion", wintypes.WCHAR * 128),
        ("wServicePackMajor", wintypes.WORD),
        ("wServicePackMinor", wintypes.WORD),
        ("wSuiteMask", wintypes.WORD),
        ("wProductType", ctypes.c_byte),
        ("wReserved", ctypes.c_byte),
    ]


class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", wintypes.WORD),
        ("wReserved", wintypes.WORD),
        ("dwPageSize", wintypes.DWORD),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.POINTER(wintypes.DWORD)),
        ("dwNumberOfProcessors", wintypes.DWORD),
        ("dwProcessorType", wintypes.DWORD),
        ("dwAllocationGranularity", wintypes.DWORD),
        ("wProcessorLevel", wintypes.WORD),
        ("wProcessorRevision", wintypes.WORD),
    ]


class DriverPackageError(Exception):
    pass


def _os_version() -> tuple[int, int]:
    # RtlGetVersion is not subject to the manifest-based version lie of GetVersionEx.
    info = OSVERSIONINFOEXW()
    info.dwOSVersionInfoSize = ctypes.sizeof(info)
    ctypes.WinDLL("ntdll").RtlGetVersion(ctypes.byref(info))
    return info.dwMajorVersion, info.dwMinorVersion


def _native_arch() -> str:
    si = SYSTEM_INFO()
    ctypes.WinDLL("kernel32").GetNativeSystemInfo(ctypes.byref(si))
    return {0: "x86", 9: "x64", 12: "arm64"}.get(si.wProcessorArchitecture, "unknown")


def resolve_inf_path() -> Path:
    """Pick the rockusb.inf matching the running OS. No implicit default."""
    arch = _native_arch()
    if arch not in ("x64", "x86"):
        raise DriverPackageError(f"Unsupported processor architecture: {arch}")

    major, minor = _os_version()
    if major >= 10:
        osdir = "win10"
    else:
        osdir = {(6, 1): "win7", (6, 2): "win8", (6, 3): "win81"}.get((major, minor), "")
    if not osdir:
        raise DriverPackageError(f"Unsupported Windows version: {major}.{minor}")

    path = _DRIVER_ROOT / arch / osdir / "rockusb.inf"
    if not path.is_file():
        raise DriverPackageError(f"Driver package incomplete: {path}")
    return path


def install_elevated(timeout_ms: int = 600_000) -> None:
    """Relaunch this executable elevated to install the driver. Raises on failure."""
    inf = resolve_inf_path()

    if getattr(sys, "frozen", False):
        params = f'{ELEVATED_FLAG} "{inf}"'
    else:
        params = f'-m rk_flash_tool {ELEVATED_FLAG} "{inf}"'

    sei = SHELLEXECUTEINFOW()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = 0x00000040 | 0x00000100  # NOCLOSEPROCESS | NOASYNC
    sei.lpVerb = "runas"
    sei.lpFile = sys.executable
    sei.lpParameters = params
    sei.nShow = 0  # SW_HIDE

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    # Explicit prototypes: HANDLE struct fields read back as Python ints and would
    # otherwise be marshalled as 32-bit, truncating the handle on x64.
    shell32.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFOW)]
    shell32.ShellExecuteExW.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    if not shell32.ShellExecuteExW(ctypes.byref(sei)):
        err = ctypes.get_last_error()
        if err == _ERROR_CANCELLED:
            raise DriverPackageError("Driver installation cancelled.")
        raise DriverPackageError(f"Failed to request administrator privileges (0x{err:08X}).")

    code = wintypes.DWORD(EXIT_INSTALL_FAILED)
    try:
        if kernel32.WaitForSingleObject(sei.hProcess, timeout_ms) != _WAIT_OBJECT_0:
            kernel32.TerminateProcess(sei.hProcess, 1)
            raise DriverPackageError("Driver installation timed out.")
        if not kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(code)):
            raise DriverPackageError(
                f"Could not read installer exit code (0x{ctypes.get_last_error():08X})."
            )
    finally:
        kernel32.CloseHandle(sei.hProcess)

    if code.value != EXIT_OK:
        raise DriverPackageError(
            _EXIT_MESSAGES.get(
                code.value,
                f"Windows rejected the driver installation (0x{code.value:08X}).",
            )
        )


def run_elevated_install(inf_arg: str) -> int:
    """Entry point for the elevated child process. Returns its exit code."""
    try:
        inf = Path(inf_arg).resolve()
    except OSError:
        return EXIT_BAD_ARGS

    if not inf.is_file() or _DRIVER_ROOT.resolve() not in inf.parents:
        return EXIT_BAD_ARGS

    newdev = ctypes.WinDLL("newdev", use_last_error=True)
    newdev.DiInstallDriverW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.BOOL),
    ]
    newdev.DiInstallDriverW.restype = wintypes.BOOL

    reboot = wintypes.BOOL(False)
    ctypes.set_last_error(0)
    if not newdev.DiInstallDriverW(None, str(inf), 0, ctypes.byref(reboot)):
        # Reported verbatim so the parent can show the actual Win32 error.
        return ctypes.get_last_error() or EXIT_BAD_ARGS
    return EXIT_OK


def elevated_main(argv: list[str]) -> int:
    if len(argv) < 2:
        return EXIT_BAD_ARGS
    try:
        return run_elevated_install(argv[1])
    except Exception:  # noqa: BLE001
        return EXIT_BAD_ARGS
