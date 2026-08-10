from __future__ import annotations

import os
import traceback
import platform
from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, QThread, QTimer, Signal, Slot, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from rockchip_flash_tool import __app_name__, __version__
from rockchip_flash_tool.flasher import FlashError, Flasher
from rockchip_flash_tool.image_format import detect_image_format
from rockchip_flash_tool.styles import Theme, theme
from rockchip_flash_tool.upgrade_tool import DriverInstallError, ToolNotFoundError

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
            self.finished.emit(ok, "Flash completed successfully." if ok else "Flash failed.")
        except FlashError as e:
            msg = str(e) + (f"\n\nSuggestion:\n{e.suggestion}" if e.suggestion else "")
            self.finished.emit(False, msg)
        except Exception as e:  # noqa: BLE001
            self.finished.emit(False, f"Unexpected error: {e}\n\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._flasher: Flasher | None = None
        self._worker: FlashWorker | None = None
        self._tool_available = False
        self._settings = QSettings(__app_name__, __app_name__)
        # Kept so the dot can be repainted when the system flips light/dark.
        self._device_connected = False
        self._device_text = "No device connected"
        self._status_idle = "Ready"
        self._theme: Theme = self._current_theme()

        self._setup_ui()
        self._try_init_tool()
        self._setup_polling()
        if platform.system() == "Windows" and not SMOKE_LAUNCH:
            # Deferred so the main window is painted before the dialog can appear.
            QTimer.singleShot(0, self._startup_driver_check)

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        # 371 = the old 360 plus the 11px the taller status bar takes, so the
        # content area above it keeps its original height.
        self.setFixedSize(860, 371)
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
        dtitle = QLabel("Device")
        dtitle.setProperty("class", "title")
        dlayout.addWidget(dtitle)
        drow = QHBoxLayout()
        self._lbl_device = QLabel("")
        self._lbl_device.setProperty("class", "device")
        self._set_device_label(False, "No device connected")
        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.clicked.connect(self._on_refresh)
        drow.addWidget(self._lbl_device, 1)
        drow.addWidget(self._btn_refresh)
        dlayout.addLayout(drow)
        root.addWidget(device_group)

        # Firmware
        fw_group = QFrame()
        fw_group.setProperty("class", "panel")
        flayout = QVBoxLayout(fw_group)
        flayout.setContentsMargins(12, 10, 12, 10)
        flayout.setSpacing(8)
        ftitle = QLabel("Firmware")
        ftitle.setProperty("class", "title")
        flayout.addWidget(ftitle)
        row = QHBoxLayout()
        self._edit_firmware = QLineEdit()
        self._edit_firmware.setPlaceholderText("Select firmware image file...")
        self._edit_firmware.setReadOnly(True)
        self._btn_browse = QPushButton("Browse")
        self._btn_browse.clicked.connect(self._on_browse_firmware)
        row.addWidget(self._edit_firmware, 1)
        row.addWidget(self._btn_browse)
        flayout.addLayout(row)
        self._lbl_fw_info = QLabel("Format: —  |  Size: —")
        self._lbl_fw_info.setProperty("class", "caption")
        flayout.addWidget(self._lbl_fw_info)
        root.addWidget(fw_group)

        # Actions
        actions = QHBoxLayout()
        actions.addStretch()
        self._btn_flash = QPushButton("Start Flash")
        self._btn_flash.setProperty("class", "primary")
        self._btn_flash.clicked.connect(self._on_flash)
        actions.addWidget(self._btn_flash)
        root.addLayout(actions)

        # The bar carries a label rather than using showMessage(): the message
        # text cannot be indented to line up with the panels (neither
        # contentsMargins nor a QSS padding moves it off 7px), and an expiring
        # timed message blanks the bar instead of restoring the previous one.
        self._status = QStatusBar()
        self._status.setSizeGripEnabled(False)
        self._lbl_status = QLabel()
        self._lbl_status.setProperty("class", "status")
        self._status.addWidget(self._lbl_status, 1)
        self.setStatusBar(self._status)

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._restore_status)
        self._set_status("Ready")

    def _try_init_tool(self) -> None:
        try:
            self._flasher = Flasher()
            self._tool_available = True
            self._set_status("Ready")
            self._poll_device()
        except ToolNotFoundError:
            self._tool_available = False
            self._btn_flash.setEnabled(False)
            self._set_status("upgrade_tool not found")

    def _setup_polling(self) -> None:
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_device)
        self._timer.start(3000)

    def _set_status(self, text: str, timeout: int = 0) -> None:
        """Show `text`; a positive `timeout` reverts to the standing status."""
        if timeout <= 0:
            self._status_idle = text
        self._lbl_status.setText(text)
        self._status_timer.stop()
        if timeout > 0:
            self._status_timer.start(timeout)

    @Slot()
    def _restore_status(self) -> None:
        self._lbl_status.setText(self._status_idle)

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
        self._set_device_label(self._device_connected, self._device_text)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        # The scheme signal and the palette event do not arrive in a fixed
        # order, and the palette is what the theme is derived from.
        if event.type() == QEvent.Type.PaletteChange:
            self._apply_theme()

    def _set_device_label(self, connected: bool, text: str) -> None:
        self._device_connected = connected
        self._device_text = text
        dot_color = self._theme.device_ok if connected else self._theme.device_off
        self._lbl_device.setText(f'<span style="color:{dot_color};">●</span> {text}')

    def _fw_info_text(self, fmt: str, size: str) -> str:
        return f"Format: {fmt}  |  Size: {size}"

    @Slot()
    def _poll_device(self) -> None:
        if not self._tool_available or (self._worker and self._worker.isRunning()):
            return
        try:
            dev = self._flasher.detect_device()
            parts = ["Connected", dev.chip_display, dev.mode]
            if dev.serial_no:
                parts.append(f"SN {dev.serial_no}")
            self._set_device_label(True, "  ·  ".join(parts))
        except Exception:  # noqa: BLE001
            self._set_device_label(False, "No device connected")

    @Slot()
    def _on_refresh(self) -> None:
        self._set_status("Scanning for devices...", 3000)
        self._poll_device()

    @Slot()
    def _on_browse_firmware(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware",
            self._last_firmware_dir(),
            "Images (*.img *.bin *.raw);;All Files (*)",
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
        try:
            info = detect_image_format(path)
            self._lbl_fw_info.setText(self._fw_info_text(info.format.display_name, info.size_display))
            self._set_status(f"Firmware loaded: {Path(path).name}", 3000)
        except Exception as e:  # noqa: BLE001
            self._lbl_fw_info.setText(self._fw_info_text("Error", "—"))
            self._set_status(f"Firmware parse error: {e}", 5000)

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
            QMessageBox.warning(self, "Error", "upgrade_tool not found.")
            return
        fw = self._edit_firmware.text().strip()
        if not fw:
            QMessageBox.warning(self, "No Firmware", "Please select firmware first.")
            return
        if not Path(fw).exists():
            QMessageBox.warning(self, "File Not Found", fw)
            return

        self._btn_flash.setEnabled(False)
        self._btn_browse.setEnabled(False)
        self._btn_refresh.setEnabled(False)
        self._set_status("Starting flash...")

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
            "Rockchip Driver Required",
            (
                "Rockchip USB driver is not detected on this Windows system.\n\n"
                "You must install it before flashing.\n\n"
                "Install driver now?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret != QMessageBox.StandardButton.Yes:
            self._set_status("Driver is required before flashing.", 5000)
            return False

        try:
            self._set_status("Installing Rockchip driver...")
            tool.install_windows_driver()
        except DriverInstallError as e:
            QMessageBox.critical(self, "Driver Install Failed", str(e))
            return False
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(
                self, "Driver Install Failed", f"Unexpected error: {e}"
            )
            return False

        if not tool.is_windows_driver_installed():
            QMessageBox.warning(
                self,
                "Driver Not Detected",
                (
                    "Driver installation finished, but Rockchip driver is still not detected.\n\n"
                    "Please reopen this app after installing the driver as Administrator."
                ),
            )
            return False

        self._set_status("Rockchip driver ready.", 4000)
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
        self._btn_flash.setEnabled(True)
        self._btn_browse.setEnabled(True)
        self._btn_refresh.setEnabled(True)
        self._set_status("Flash completed." if ok else "Flash failed.", 8000)
        if ok:
            QMessageBox.information(self, "Success", "Flash completed.")
        else:
            QMessageBox.critical(self, "Flash Failed", msg)
