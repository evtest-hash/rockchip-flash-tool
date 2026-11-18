from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QCoreApplication

from rockchip_flash_tool import resources
from rockchip_flash_tool.chip_db import find_loader
from rockchip_flash_tool.image_format import ImageFormat, ImageInfo, detect_image_format
from rockchip_flash_tool.upgrade_tool import (
    AmbiguousDeviceError,
    DeviceInfo,
    DeviceNotFoundError,
    UpgradeTool,
    UpgradeToolError,
)

ProgressCallback = Callable[[str], None]


def _translate(text: str, **values) -> str:
    """Apply named placeholders to an already-translated message."""
    return text % values if values else text


class FlashError(Exception):
    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message)
        self.suggestion = suggestion


class Flasher:
    def __init__(self, tool_path: str | None = None):
        self._tool = UpgradeTool(tool_path)
        self._progress_cb: ProgressCallback | None = None

    @property
    def upgrade_tool(self) -> UpgradeTool:
        return self._tool

    def set_progress_callback(self, cb: ProgressCallback) -> None:
        self._progress_cb = cb

    def _emit(self, message: str) -> None:
        if self._progress_cb:
            self._progress_cb(message)

    def list_devices(self) -> list[DeviceInfo]:
        return self._tool.list_devices()

    def select_device(self, device_id: str | None) -> None:
        self._tool.select(device_id)

    def detect_device(self) -> DeviceInfo:
        self._emit(QCoreApplication.translate("Flasher", "Scanning for Rockchip devices..."))
        try:
            dev = self._tool.get_device()
        except AmbiguousDeviceError as e:
            raise FlashError(
                str(e),
                QCoreApplication.translate(
                    "Flasher", "Move one board to a different USB port, then refresh."
                ),
            )
        except DeviceNotFoundError as e:
            raise FlashError(
                str(e),
                QCoreApplication.translate(
                    "Flasher", "Please connect the board and enter Loader/Maskrom mode."
                ),
            )
        self._emit(
            _translate(
                QCoreApplication.translate("Flasher", "Found %(chip)s in %(mode)s mode"),
                chip=dev.chip_display,
                mode=dev.mode,
            )
        )
        return dev

    def flash(self, image_path: str | Path, chip_model: str | None = None) -> bool:
        image_path = Path(image_path)

        try:
            dev = self.detect_device()
            if chip_model:
                dev.chip_model = chip_model
            if not dev.chip_model:
                raise FlashError(
                    QCoreApplication.translate("Flasher", "Could not determine chip model.")
                )

            self._emit(QCoreApplication.translate("Flasher", "Analyzing image format..."))
            info = detect_image_format(image_path)
            # An RK package is identified by a magic at offset 0, so anything
            # that is not one cannot be fed to UF -- it goes out sector by
            # sector with WL. The same flag decides the reset below, because UF
            # resets the board itself and WL leaves it where it was; deriving
            # the two from one predicate keeps them from drifting apart.
            raw_write = not info.format.is_rk_format
            if info.format == ImageFormat.UNKNOWN:
                self._emit(
                    QCoreApplication.translate(
                        "Flasher", "No partition table found; writing as a raw image."
                    )
                )

            if not raw_write:
                self._emit(
                    QCoreApplication.translate(
                        "Flasher", "RK firmware detected, flashing via UF directly."
                    )
                )
            elif dev.mode.lower() == "maskrom":
                self._handle_maskrom(dev)
            else:
                self._emit(
                    QCoreApplication.translate(
                        "Flasher", "Loader mode detected, flashing raw image directly."
                    )
                )

            self._emit(QCoreApplication.translate("Flasher", "Starting flash..."))
            ok = self._do_flash(info, raw_write)
            if not ok:
                raise FlashError(
                    QCoreApplication.translate("Flasher", "Flashing failed."),
                    QCoreApplication.translate(
                        "Flasher", "Please reconnect the board and retry."
                    ),
                )
            if raw_write:
                self._emit(QCoreApplication.translate("Flasher", "Resetting device..."))
                if not self._tool.reset_device():
                    self._emit(
                        QCoreApplication.translate(
                            "Flasher",
                            "Device reset did not confirm; power-cycle the board.",
                        )
                    )
            self._emit(
                QCoreApplication.translate("Flasher", "Flash completed successfully.")
            )
            return True
        except UpgradeToolError as e:
            raise FlashError(
                str(e),
                QCoreApplication.translate(
                    "Flasher", "Check tool files and USB connection."
                ),
            )

    def _handle_maskrom(self, device: DeviceInfo) -> None:
        self._emit(
            QCoreApplication.translate("Flasher", "Maskrom mode: downloading bootloader...")
        )
        loader = find_loader(device.chip_model, resources.rkbin_dir()) if device.chip_model else None
        if not loader:
            raise FlashError(
                _translate(
                    QCoreApplication.translate(
                        "Flasher", "No bootloader found for %(chip)s."
                    ),
                    chip=device.chip_display,
                ),
                QCoreApplication.translate(
                    "Flasher", "Make sure vendor/rkbin contains a matching loader."
                ),
            )
        self._emit(
            _translate(
                QCoreApplication.translate("Flasher", "Downloading %(name)s"),
                name=loader.name,
            )
        )
        if not self._tool.download_boot(loader):
            raise FlashError(
                QCoreApplication.translate("Flasher", "Bootloader download failed.")
            )
        time.sleep(2)

    def _do_flash(self, info: ImageInfo, raw_write: bool) -> bool:
        def on_tool_progress(pct: int | None, line: str) -> None:
            self._emit(
                line or QCoreApplication.translate("Flasher", "Flashing...")
            )

        if raw_write:
            return self._tool.write_image(info.path, progress_callback=on_tool_progress)
        return self._tool.upgrade_firmware(info.path, progress_callback=on_tool_progress)
