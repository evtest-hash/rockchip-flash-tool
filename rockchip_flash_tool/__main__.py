from __future__ import annotations

import os
import sys

# Elevated child process: handle before Qt is imported so it stays lightweight.
if sys.platform.startswith("win") and "--install-rockusb-driver" in sys.argv:
    from rockchip_flash_tool.win_driver import ELEVATED_FLAG, elevated_main

    sys.exit(elevated_main(sys.argv[sys.argv.index(ELEVATED_FLAG):]))

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from rockchip_flash_tool import __app_name__, resources
from rockchip_flash_tool.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName(__app_name__)
    icon_path = resources.icon_path() if sys.platform.startswith("win") else None
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    w = MainWindow()
    if icon_path:
        w.setWindowIcon(QIcon(str(icon_path)))
    w.show()
    auto_exit_ms = os.getenv("ROCKCHIP_FLASH_TOOL_AUTO_EXIT_MS", "").strip()
    if auto_exit_ms:
        try:
            QTimer.singleShot(max(0, int(auto_exit_ms)), app.quit)
        except ValueError:
            pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
