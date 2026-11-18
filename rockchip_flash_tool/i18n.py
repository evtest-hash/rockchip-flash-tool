"""Language selection and Qt translator installation.

The app's own strings live in one .qm catalog; Qt's standard dialog strings
come from qtbase_<lang>.qm shipped with PySide6. English is the source
language and needs no translator.
"""

from __future__ import annotations

import logging
import os

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QTranslator

from rockchip_flash_tool import resources

LANGUAGE_ENV = "ROCKCHIP_FLASH_TOOL_LANG"
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"en", "zh_CN"}

_log = logging.getLogger(__name__)


def system_language() -> str:
    for tag in QLocale.system().uiLanguages():
        if tag.lower().startswith("zh"):
            return "zh_CN"
    return DEFAULT_LANGUAGE


def resolve_language() -> str:
    override = os.getenv(LANGUAGE_ENV, "").strip()
    if override in SUPPORTED_LANGUAGES:
        return override
    return system_language()


def apply_language(app: QCoreApplication, language: str) -> None:
    """Install the catalog for `language`, replacing any previous one."""
    for translator in app.findChildren(QTranslator):
        app.removeTranslator(translator)
        translator.deleteLater()

    if language == DEFAULT_LANGUAGE:
        return

    # Load the app catalog first: without it the interface would be a mix of
    # translated Qt buttons and English application text.
    app_translator = QTranslator(app)
    catalog = resources.i18n_dir() / f"rockchip_flash_tool_{language}.qm"
    if not app_translator.load(str(catalog)):
        _log.warning("App translation not found: %s", catalog)
        app_translator.deleteLater()
        return

    qt_translator = QTranslator(app)
    qt_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_translator.load(f"qtbase_{language}", qt_dir):
        app.installTranslator(qt_translator)
    else:
        _log.warning("Qt translation not found: qtbase_%s in %s", language, qt_dir)
        qt_translator.deleteLater()

    app.installTranslator(app_translator)
