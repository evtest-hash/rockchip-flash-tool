from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from rk_flash_tool.chip_db import ChipDatabase
from rk_flash_tool.image_format import ImageFormat, ImageInfo, detect_image_format, validate_firmware_for_chip
from rk_flash_tool.upgrade_tool import DeviceInfo, DeviceNotFoundError, UpgradeTool, UpgradeToolError


class FlashStage(Enum):
    DETECT_DEVICE = "Detecting device"
    DETECT_FORMAT = "Analyzing firmware"
    DOWNLOAD_BOOT = "Downloading bootloader"
    FLASH = "Flashing"
    DONE = "Done"


@dataclass
class FlashProgress:
    stage: FlashStage
    message: str
    progress_pct: int = 0


ProgressCallback = Callable[[FlashProgress], None]


class FlashError(Exception):
    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message)
        self.suggestion = suggestion


class Flasher:
    def __init__(self, tool_path: str | None = None):
        self._tool = UpgradeTool(tool_path)
        self._chip_db = ChipDatabase()
        self._progress_cb: ProgressCallback | None = None
        self._cancelled = False

    @property
    def upgrade_tool(self) -> UpgradeTool:
        return self._tool

    def set_progress_callback(self, cb: ProgressCallback) -> None:
        self._progress_cb = cb

    def cancel(self) -> None:
        self._cancelled = True

    def _emit(self, stage: FlashStage, message: str, pct: int = 0) -> None:
        if self._progress_cb:
            self._progress_cb(FlashProgress(stage, message, pct))

    def _check_cancel(self) -> None:
        if self._cancelled:
            raise FlashError("Operation cancelled by user.")

    def detect_device(self) -> DeviceInfo:
        self._emit(FlashStage.DETECT_DEVICE, "Scanning for Rockchip devices...", 5)
        try:
            dev = self._tool.get_device()
        except DeviceNotFoundError as e:
            raise FlashError(str(e), "Please connect the board and enter Loader/Maskrom mode.")
        if not dev.chip_model:
            cfg = self._chip_db.get_by_pid(dev.pid)
            if cfg:
                dev.chip_model = cfg.model
        self._emit(FlashStage.DETECT_DEVICE, f"Found {dev.chip_display} in {dev.mode} mode", 10)
        return dev

    def flash(self, image_path: str | Path, chip_model: str | None = None) -> bool:
        self._cancelled = False
        image_path = Path(image_path)

        try:
            dev = self.detect_device()
            self._check_cancel()
            if chip_model:
                dev.chip_model = chip_model
            if not dev.chip_model:
                raise FlashError("Could not determine chip model.")

            self._emit(FlashStage.DETECT_FORMAT, "Analyzing image format...", 15)
            info = detect_image_format(image_path)
            is_valid, msg = validate_firmware_for_chip(info, dev.chip_model)
            if not is_valid:
                self._emit(FlashStage.DETECT_FORMAT, msg, 15)
            self._check_cancel()

            if info.format.is_rk_format:
                self._emit(FlashStage.FLASH, "RK firmware detected, flashing via UF directly.", 45)
            elif dev.mode.lower() == "maskrom":
                self._handle_maskrom(dev, image_path.parent)
            else:
                self._emit(FlashStage.FLASH, "Loader mode detected, flashing raw image directly.", 45)

            self._emit(FlashStage.FLASH, "Starting flash...", 50)
            ok = self._do_flash(info)
            if not ok:
                raise FlashError("Flashing failed.", "Please reconnect the board and retry.")
            if info.format == ImageFormat.RAW:
                self._emit(FlashStage.FLASH, "Resetting device...", 98)
                if not self._tool.reset_device():
                    self._emit(FlashStage.FLASH, "Device reset did not confirm; power-cycle the board.", 99)
            self._emit(FlashStage.DONE, "Flash completed successfully.", 100)
            return True
        except UpgradeToolError as e:
            raise FlashError(str(e), "Check tool files and USB connection.")

    def _handle_maskrom(self, device: DeviceInfo, firmware_dir: Path) -> None:
        self._emit(FlashStage.DOWNLOAD_BOOT, "Maskrom mode: downloading bootloader...", 35)
        loader = self._resolve_loader(device.chip_model, firmware_dir)
        if not loader:
            raise FlashError(
                f"No bootloader found for {device.chip_display}.",
                "Make sure rkbin contains a matching loader.",
            )
        self._emit(FlashStage.DOWNLOAD_BOOT, f"Downloading {loader.name}", 40)
        if not self._tool.download_boot(loader):
            raise FlashError("Bootloader download failed.")
        time.sleep(2)

    def _resolve_loader(self, chip_model: str | None, firmware_dir: Path) -> Path | None:
        if not chip_model:
            return None
        rkbin_dir = Path(__file__).resolve().parent.parent / "rkbin"
        for d in [rkbin_dir, firmware_dir, Path.home() / ".rk-flash-tool" / "tools"]:
            found = self._chip_db.find_loader(chip_model, d)
            if found:
                return found
        return None

    def _do_flash(self, info: ImageInfo) -> bool:
        def on_tool_progress(pct: int | None, line: str) -> None:
            self._emit(FlashStage.FLASH, line or "Flashing...", 0)

        if info.format.is_rk_format:
            return self._tool.upgrade_firmware(info.path, progress_callback=on_tool_progress)
        if info.format == ImageFormat.RAW:
            return self._tool.write_image(info.path, progress_callback=on_tool_progress)
        # unknown: try UF first, fallback WL
        if self._tool.upgrade_firmware(info.path, progress_callback=on_tool_progress):
            return True
        return self._tool.write_image(info.path, progress_callback=on_tool_progress)
