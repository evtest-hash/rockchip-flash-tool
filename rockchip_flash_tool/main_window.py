from __future__ import annotations

import os
import traceback
import platform
from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, QThread, QTimer, Signal, Slot, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QGuiApplication
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from rockchip_flash_tool import __app_name__, __version__
from rockchip_flash_tool.flasher import FlashError, Flasher
from rockchip_flash_tool.image_format import ImageFormat, ImageInfo, detect_image_format
from rockchip_flash_tool.styles import Theme, theme
from rockchip_flash_tool.upgrade_tool import (
    DeviceInfo,
    DriverInstallError,
    ToolNotFoundError,
)

# The artifact smoke tests launch the app with an auto-quit timer. A modal
# dialog would run its own event loop and ignore QApplication.quit(), hanging
# the run, so no dialog may open in this mode.
SMOKE_LAUNCH = bool(os.getenv("ROCKCHIP_FLASH_TOOL_AUTO_EXIT_MS", "").strip())

_LAST_DIR_KEY = "firmware/last_dir"


class FlashWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, flasher: Flasher, image_path: str):
        super().__init__()
        self._flasher = flasher
        self._image_path = image_path

    def run(self) -> None:
        self._flasher.set_progress_callback(self.progress.emit)
        try:
            ok = self._flasher.flash(self._image_path)
            self.finished.emit(
                ok,
                self.tr("Flash completed successfully.")
                if ok
                else self.tr("Flash failed."),
            )
        except FlashError as e:
            msg = str(e)
            if e.suggestion:
                msg += self.tr("\n\nSuggestion:\n%(suggestion)s") % {
                    "suggestion": e.suggestion
                }
            self.finished.emit(False, msg)
        except Exception as e:  # noqa: BLE001
            self.finished.emit(
                False,
                self.tr("Unexpected error: %(error)s\n\n%(traceback)s")
                % {"error": e, "traceback": traceback.format_exc()},
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._flasher: Flasher | None = None
        self._worker: FlashWorker | None = None
        self._tool_available = False
        self._settings = QSettings(__app_name__, __app_name__)
        self._fw_info: ImageInfo | None = None
        self._fw_parse_error = False
        # Kept so the dot can be repainted when the system flips light/dark.
        self._device_connected = False
        self._device_text = self.tr("No device connected")
        # None, not [], so the first render of an empty list is not skipped.
        self._device_shown: list[tuple[str, str]] | None = None
        self._devices: list[DeviceInfo] = []
        self._selected_key: str | None = None
        self._status_idle = self.tr("Ready")
        self._theme: Theme = self._current_theme()

        self._setup_ui()
        self._try_init_tool()
        self._setup_polling()
        if platform.system() == "Windows" and not SMOKE_LAUNCH:
            # Deferred so the main window is painted before the dialog can appear.
            QTimer.singleShot(0, self._startup_driver_check)

    def _setup_ui(self) -> None:
        # The device panel gained a caption row (+26) and the separate status
        # bar went away, its text moving up beside the action button (-32).
        self.setFixedSize(860, 365)
        self.setAcceptDrops(True)
        self.setStyleSheet(self._theme.qss)
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._apply_theme)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(14, 12, 14, 10)

        # Device
        device_group = QFrame()
        device_group.setProperty("class", "panel")
        dlayout = QVBoxLayout(device_group)
        dlayout.setContentsMargins(12, 10, 12, 10)
        dlayout.setSpacing(8)
        self._lbl_title_device = QLabel()
        self._lbl_title_device.setProperty("class", "title")
        dlayout.addWidget(self._lbl_title_device)
        drow = QHBoxLayout()
        drow.setSpacing(8)
        self._lbl_dot = QLabel("")
        self._lbl_dot.setProperty("class", "device")
        self._lbl_device = QLabel("")
        self._lbl_device.setProperty("class", "device")
        # Swapped in for the label once there is more than one board, so the
        # choice is on screen instead of behind a click.
        self._chips = QWidget()
        self._chips.setProperty("class", "bare")
        self._chips_row = QHBoxLayout(self._chips)
        self._chips_row.setContentsMargins(0, 0, 0, 0)
        self._chips_row.setSpacing(6)
        self._chip_group = QButtonGroup(self)
        self._chip_group.idClicked.connect(self._choose_device_at)
        self._chips.hide()
        self._btn_refresh = QPushButton()
        self._btn_refresh.clicked.connect(self._on_refresh)
        drow.addWidget(self._lbl_dot)
        drow.addWidget(self._lbl_device)
        drow.addWidget(self._chips)
        drow.addStretch(1)
        drow.addWidget(self._btn_refresh)
        dlayout.addLayout(drow)
        # Identity is on the row, state is here, so neither the label nor a chip
        # has to carry a 16-digit serial.
        self._lbl_dev_detail = QLabel("")
        self._lbl_dev_detail.setProperty("class", "caption")
        dlayout.addWidget(self._lbl_dev_detail)
        root.addWidget(device_group)

        # Firmware
        fw_group = QFrame()
        fw_group.setProperty("class", "panel")
        flayout = QVBoxLayout(fw_group)
        flayout.setContentsMargins(12, 10, 12, 10)
        flayout.setSpacing(8)
        self._lbl_title_fw = QLabel()
        self._lbl_title_fw.setProperty("class", "title")
        flayout.addWidget(self._lbl_title_fw)
        row = QHBoxLayout()
        self._edit_firmware = QLineEdit()
        self._edit_firmware.setReadOnly(True)
        self._btn_browse = QPushButton()
        self._btn_browse.clicked.connect(self._on_browse_firmware)
        row.addWidget(self._edit_firmware, 1)
        row.addWidget(self._btn_browse)
        flayout.addLayout(row)
        self._lbl_fw_info = QLabel()
        self._lbl_fw_info.setProperty("class", "caption")
        flayout.addWidget(self._lbl_fw_info)
        root.addWidget(fw_group)

        # One strip, not two: the status used to sit in a QStatusBar of its own
        # below the action row, so pressing the button on the right and reading
        # what happened on the left were separate places to look, with an empty
        # row between them.
        actions = QHBoxLayout()
        self._lbl_status = QLabel()
        self._lbl_status.setProperty("class", "status")
        # Ignored, so a long tool line clips instead of pushing the button off.
        self._lbl_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._btn_flash = QPushButton()
        self._btn_flash.setProperty("class", "primary")
        self._btn_flash.clicked.connect(self._on_flash)
        actions.addWidget(self._lbl_status, 1)
        actions.addWidget(self._btn_flash)
        root.addLayout(actions)

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._restore_status)

        # Fusion, unlike the macOS style, puts buttons in the tab chain, so
        # activating the window handed focus to Refresh -- the first one built --
        # and the sheet's :focus rule ringed it, pointing the eye at a secondary
        # control every time the app was opened. Park focus here instead; Tab
        # still reaches everything.
        central.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        central.setFocus()

        # Last: it fills every label from the current language and settles the
        # flash button, which is built above.
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        """Apply every user-facing string in the current language."""
        product_name = self.tr("Rockchip Flash Tool")
        self.setWindowTitle(f"{product_name} v{__version__}")
        self._lbl_title_device.setText(self.tr("Device"))
        self._lbl_title_fw.setText(self.tr("Firmware"))
        self._btn_refresh.setText(self.tr("Refresh"))
        self._btn_browse.setText(self.tr("Browse"))
        self._btn_flash.setText(self.tr("Start Flash"))
        self._edit_firmware.setPlaceholderText(self.tr("Select firmware image file…"))

        self._status_idle = self.tr("Ready")
        self._show_status(self._status_idle)
        self._device_text = self.tr("No device connected")
        # Device text is state-driven; clear the cache so an empty list repaints
        # with the current strings too.
        self._device_shown = None
        self._render_fw_info()
        self._render_devices(self._devices)

    def _format_name(self, fmt: ImageFormat) -> str:
        return {
            ImageFormat.RKFW: self.tr("Rockchip Firmware (RKFW)"),
            ImageFormat.RKAF: self.tr("Rockchip Firmware (RKAF)"),
            ImageFormat.RAW: self.tr("Raw Disk Image"),
            ImageFormat.UNKNOWN: self.tr("Unknown"),
        }[fmt]

    def _render_fw_info(self) -> None:
        if self._fw_info is not None:
            self._lbl_fw_info.setText(
                self._fw_info_text(
                    self._format_name(self._fw_info.format),
                    self._fw_info.size_display,
                )
            )
        elif self._fw_parse_error:
            self._lbl_fw_info.setText(self._fw_info_text(self.tr("Parse error"), "—"))
        else:
            self._lbl_fw_info.setText(self._fw_info_text("—", "—"))

    def _try_init_tool(self) -> None:
        try:
            self._flasher = Flasher()
            self._tool_available = True
            self._set_status(self.tr("Ready"))
            self._poll_device()
        except ToolNotFoundError:
            self._tool_available = False
            self._set_status(self.tr("upgrade_tool not found"))

    def _setup_polling(self) -> None:
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_device)
        self._timer.start(3000)

    def _show_status(self, text: str) -> None:
        # upgrade_tool emits whatever length of line it likes, and the window is
        # a fixed width shared with the button beside it.
        metrics = self._lbl_status.fontMetrics()
        width = max(self._lbl_status.width(), 120)
        self._lbl_status.setText(metrics.elidedText(text, Qt.TextElideMode.ElideRight, width))

    def _set_status(self, text: str, timeout: int = 0) -> None:
        """Show `text`; a positive `timeout` reverts to the standing status."""
        if timeout <= 0:
            self._status_idle = text
        self._show_status(text)
        self._status_timer.stop()
        if timeout > 0:
            self._status_timer.start(timeout)

    @Slot()
    def _restore_status(self) -> None:
        self._show_status(self._status_idle)

    def _current_theme(self) -> Theme:
        scheme = QGuiApplication.styleHints().colorScheme()
        return theme(QGuiApplication.palette(), scheme == Qt.ColorScheme.Dark)

    @Slot()
    def _apply_theme(self) -> None:
        new = self._current_theme()
        # Also the recursion guard: restyling re-emits PaletteChange.
        if new == self._theme:
            return
        self._theme = new
        self.setStyleSheet(new.qss)
        self._paint_dot()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        # The scheme signal and the palette event do not arrive in a fixed
        # order, and the palette is what the theme is derived from.
        if event.type() == QEvent.Type.PaletteChange:
            self._apply_theme()

    def _paint_dot(self) -> None:
        self._device_connected = self._selected_key is not None
        color = self._theme.device_ok if self._device_connected else self._theme.device_off
        self._lbl_dot.setText(f'<span style="color:{color};">●</span>')

    @staticmethod
    def _chip_labels(devices: list[DeviceInfo]) -> list[str]:
        # The port id is upgrade_tool's LocationID verbatim -- what LD prints,
        # what -s takes, what its log records. It is a USB hub path, but the
        # packing is lossy and differs per platform, so it is never reformatted.
        return [f"{d.chip_display}  @{d.key}" for d in devices]

    def _device_line(self, dev: DeviceInfo | None) -> str:
        if dev is None:
            return self.tr("No device connected")
        parts = [self.tr("Connected"), dev.chip_display, dev.mode, f"@{dev.key}"]
        if dev.serial_no:
            parts.append(self.tr("SN %(serial)s") % {"serial": dev.serial_no})
        return "  ·  ".join(parts)

    def _device_detail(self, dev: DeviceInfo | None) -> str:
        if dev is None:
            mode = port = serial = "—"
        else:
            mode, port, serial = dev.mode, dev.key, dev.serial_no or "—"
        # Spelled out here even though the chip already carries it: the bare
        # @1112 on a chip does not say what kind of number it is.
        return self.tr(
            "Mode: %(mode)s   |   USB port ID: %(port)s   |   Serial: %(serial)s"
        ) % {"mode": mode, "port": port, "serial": serial}

    def _render_devices(self, devices: list[DeviceInfo]) -> None:
        # Compare everything shown, chips and caption both, so a Maskrom->Loader
        # switch refreshes the caption; and skip the work entirely when a poll
        # brings no news.
        shown = [(lbl, self._device_detail(d)) for lbl, d in zip(self._chip_labels(devices), devices)]
        if shown == self._device_shown:
            return
        self._device_shown = shown
        self._devices = devices

        # Selection follows the key, never the position: boards change places.
        keys = [d.key for d in devices]
        if self._selected_key not in keys:
            self._selected_key = keys[0] if keys else None

        for button in self._chip_group.buttons():
            self._chip_group.removeButton(button)
            button.deleteLater()
        while self._chips_row.count():
            self._chips_row.takeAt(0)
        for index, (label, _) in enumerate(shown):
            chip = QPushButton(label)
            chip.setProperty("class", "chip")
            chip.setCheckable(True)
            self._chip_group.addButton(chip, index)
            self._chips_row.addWidget(chip)

        self._repaint_device_row()
        self._sync_controls()

    def _repaint_device_row(self) -> None:
        dev = self._selected_device()
        many = len(self._devices) > 1
        self._chips.setVisible(many)
        self._lbl_device.setVisible(not many)
        if not many:
            self._device_text = self._device_line(dev)
            self._lbl_device.setText(self._device_text)
        else:
            for index, board in enumerate(self._devices):
                button = self._chip_group.button(index)
                if button is not None:
                    button.setChecked(board.key == self._selected_key)
        self._lbl_dev_detail.setText(self._device_detail(dev))
        self._paint_dot()

    def _selected_device(self) -> DeviceInfo | None:
        return next((d for d in self._devices if d.key == self._selected_key), None)

    @Slot(int)
    def _choose_device_at(self, index: int) -> None:
        if 0 <= index < len(self._devices):
            self._choose_device(self._devices[index].key)

    def _choose_device(self, key: str) -> None:
        self._selected_key = key
        self._repaint_device_row()
        self._sync_controls()

    def _sync_controls(self, busy: bool = False) -> None:
        ready = not busy and self._selected_key is not None
        self._btn_browse.setEnabled(not busy)
        self._btn_refresh.setEnabled(not busy)
        self._chips.setEnabled(not busy)
        self._btn_flash.setEnabled(ready and self._tool_available)

    def _fw_info_text(self, fmt: str, size: str) -> str:
        return self.tr("Format: %(format)s  |  Size: %(size)s") % {
            "format": fmt,
            "size": size,
        }

    @Slot()
    def _poll_device(self) -> None:
        if not self._tool_available or (self._worker and self._worker.isRunning()):
            return
        try:
            devices = self._flasher.list_devices()
        except Exception as e:  # noqa: BLE001
            # Say so: a failing scan otherwise looks like an unplugged board.
            devices = []
            self._set_status(
                self.tr("Device scan failed: %(error)s") % {"error": e}, 5000
            )
        self._render_devices(devices)

    @Slot()
    def _on_refresh(self) -> None:
        self._set_status(self.tr("Scanning for devices..."), 3000)
        self._poll_device()

    @Slot()
    def _on_browse_firmware(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select Firmware"),
            self._last_firmware_dir(),
            self.tr("Images (*.img *.bin *.raw);;All Files (*)"),
        )
        if not path:
            return
        self._load_firmware(path)

    def _last_firmware_dir(self) -> str:
        saved = str(self._settings.value(_LAST_DIR_KEY, "") or "")
        return saved if saved and Path(saved).is_dir() else str(Path.home())

    def _load_firmware(self, path: str) -> None:
        self._edit_firmware.setText(path)
        self._settings.setValue(_LAST_DIR_KEY, str(Path(path).parent))
        self._fw_info = None
        self._fw_parse_error = False
        try:
            info = detect_image_format(path)
            self._fw_info = info
            self._render_fw_info()
            self._set_status(
                self.tr("Firmware loaded: %(name)s") % {"name": Path(path).name}, 3000
            )
        except Exception as e:  # noqa: BLE001
            self._fw_parse_error = True
            self._render_fw_info()
            self._set_status(
                self.tr("Firmware parse error: %(error)s") % {"error": e}, 5000
            )

    def _dropped_firmware(self, event: QDragEnterEvent | QDropEvent) -> str | None:
        if self._worker and self._worker.isRunning():
            return None
        mime = event.mimeData()
        if not mime.hasUrls():
            return None
        urls = [u for u in mime.urls() if u.isLocalFile()]
        if len(urls) != 1:
            return None
        path = urls[0].toLocalFile()
        return path if Path(path).is_file() else None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._dropped_firmware(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        path = self._dropped_firmware(event)
        if not path:
            event.ignore()
            return
        event.acceptProposedAction()
        self._load_firmware(path)

    @Slot()
    def _on_flash(self) -> None:
        if not self._tool_available:
            QMessageBox.warning(self, self.tr("Error"), self.tr("upgrade_tool not found."))
            return
        fw = self._edit_firmware.text().strip()
        if not fw:
            QMessageBox.warning(
                self, self.tr("No Firmware"), self.tr("Please select firmware first.")
            )
            return
        if not Path(fw).exists():
            QMessageBox.warning(self, self.tr("File Not Found"), fw)
            return
        if self._selected_key is None:
            QMessageBox.warning(
                self, self.tr("No Device"), self.tr("Please select a device first.")
            )
            return

        # Pins DB, UF/WL and RD to this board, including across the
        # Maskrom->Loader switch in the middle.
        self._flasher.select_device(self._selected_key)

        self._sync_controls(busy=True)
        self._set_status(self.tr("Starting flash..."))

        self._worker = FlashWorker(self._flasher, fw)
        # Force queued delivery to the UI thread on Windows.
        self._worker.progress.connect(self._on_flash_progress, Qt.ConnectionType.QueuedConnection)
        self._worker.finished.connect(self._on_flash_finished)
        self._worker.start()

    @Slot()
    def _startup_driver_check(self) -> None:
        if not self._tool_available:
            return
        if self._ensure_windows_driver():
            self._poll_device()

    def _ensure_windows_driver(self) -> bool:
        if not self._flasher:
            return False
        tool = self._flasher.upgrade_tool
        try:
            if tool.is_windows_driver_installed():
                return True
        except Exception:  # noqa: BLE001
            # Fall through and still offer manual install.
            pass

        ret = QMessageBox.question(
            self,
            self.tr("Rockchip Driver Required"),
            self.tr(
                "Rockchip USB driver is not detected on this Windows system.\n\n"
                "You must install it before flashing.\n\n"
                "Install driver now?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret != QMessageBox.StandardButton.Yes:
            self._set_status(self.tr("Driver is required before flashing."), 5000)
            return False

        try:
            self._set_status(self.tr("Installing Rockchip driver..."))
            tool.install_windows_driver()
        except DriverInstallError as e:
            if e.cancelled:
                QMessageBox.information(self, self.tr("Driver Installation"), str(e))
                self._set_status(self.tr("Driver installation cancelled."), 5000)
            else:
                QMessageBox.critical(self, self.tr("Driver Install Failed"), str(e))
            return False
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(
                self,
                self.tr("Driver Install Failed"),
                self.tr("Unexpected error: %(error)s") % {"error": e},
            )
            return False

        if not tool.is_windows_driver_installed():
            QMessageBox.warning(
                self,
                self.tr("Driver Not Detected"),
                self.tr(
                    "Driver installation finished, but Rockchip driver is still not detected.\n\n"
                    "Please reopen this app after installing the driver as Administrator."
                ),
            )
            return False

        self._set_status(self.tr("Rockchip driver ready."), 4000)
        return True

    @Slot(str)
    def _on_flash_progress(self, message: str) -> None:
        self._set_status(message)

    @Slot(bool, str)
    def _on_flash_finished(self, ok: bool, msg: str) -> None:
        # Drop the callback before anything else: it points at this worker's
        # signal, and the message boxes below run a nested event loop in which
        # the poll timer fires. Keep the worker referenced -- releasing it here
        # would destroy a QThread whose thread has not returned from run() yet.
        self._flasher.set_progress_callback(None)
        self._sync_controls()
        # Flash progress is shown without a timeout, which makes each line the
        # standing status; put that back to Ready so the result message below
        # expires into it rather than into a stale progress line.
        self._status_idle = self.tr("Ready")
        self._set_status(
            self.tr("Flash completed.") if ok else self.tr("Flash failed."), 8000
        )
        if ok:
            QMessageBox.information(
                self, self.tr("Success"), self.tr("Flash completed.")
            )
        else:
            QMessageBox.critical(self, self.tr("Flash Failed"), msg)
