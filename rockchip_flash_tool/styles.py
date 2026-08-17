from __future__ import annotations

import sys
from dataclasses import dataclass
from string import Template

from PySide6.QtGui import QColor, QPalette

# Every neutral is derived from the platform palette, so the window, the title
# bar the system draws for us, and the status bar all sit in one family. Only
# the brand accent and the device dot are ours to pick.
_ACCENT = {False: "#1e80e2", True: "#2f8ae0"}
_DEVICE_OK = {False: "#16a34a", True: "#34d399"}
_DEVICE_OFF = {False: "#dc2626", True: "#f87171"}

_WHITE = QColor("#ffffff")

# --- Type scale -------------------------------------------------------------
# Sizes are in points, not pixels: Qt converts points through the screen's
# logical DPI, so text follows a user who has asked their system for a larger
# font. Pixels ignore that request.
#
# Points are authored against macOS's 72dpi. Windows and Linux report 96dpi,
# where the same point value renders a third larger, so those two get a
# correction. It is a per-platform constant on purpose and NOT the screen's
# measured DPI: a display that genuinely deviates from its platform norm should
# still end up with bigger text, which is the whole reason for using points.
_FONT_DPI_CORRECTION = 1.0 if sys.platform == "darwin" else 72.0 / 96.0

# The only raw numbers in the scale. Everything below is a role that maps here.
_FONT_SM = 13
_FONT_MD = 14
_FONT_LG = 15


def _pt(size: float) -> str:
    return f"{size * _FONT_DPI_CORRECTION:.2f}pt"


_FONT_TOKENS = {
    "font_body": _pt(_FONT_SM),
    "font_caption": _pt(_FONT_SM),
    "font_input": _pt(_FONT_SM),
    "font_button": _pt(_FONT_SM),
    # The status line is the app's only feedback channel, so it carries the
    # same weight as the device line rather than reading as a footnote.
    "font_status": _pt(_FONT_MD),
    "font_device": _pt(_FONT_MD),
    "font_action": _pt(_FONT_MD),
    "font_title": _pt(_FONT_LG),
}

# QSS braces collide with str.format, so the palette is substituted with $tokens.
_QSS = Template(
    """
QMainWindow, QWidget {
  background: $window;
  color: $text;
}
QLabel {
  background: transparent;
  color: $text;
  font-size: $font_body;
}
QLabel[class="title"] {
  font-size: $font_title;
  font-weight: 800;
}
QLabel[class="device"] {
  font-size: $font_device;
  font-weight: 700;
}
QLabel[class="status"] {
  color: $text;
  font-size: $font_status;
  /* Lands the text on the same vertical line as the panel content above. */
  padding-left: 13px;
}
QLabel[class="caption"] {
  color: $text_muted;
  font-size: $font_caption;
  font-weight: 600;
}
QFrame[class="panel"] {
  background: $panel;
  border: 1px solid $border;
  border-radius: 10px;
}
QLineEdit {
  font-size: $font_input;
  border: 1px solid $border;
  border-radius: 8px;
  padding: 6px 10px;
  background: $input;
  color: $text;
  selection-background-color: $accent;
  selection-color: $on_accent;
}
QLineEdit:disabled {
  background: $disabled;
  color: $text_disabled;
}
QPushButton {
  border-radius: 8px;
  padding: 7px 14px;
  background: $button;
  color: $text;
  border: 1px solid $border;
  font-size: $font_button;
}
QPushButton:hover {
  background: $button_hover;
}
QPushButton:pressed {
  background: $button_pressed;
}
QPushButton:focus {
  border: 1px solid $accent;
}
/* One chip per attached board. Selection is the accent, never the device
   green: the dot means "a board is live", the fill means "this is the one we
   will write to", and the two must not be read as the same signal. */
/* The row holding them is a plain QWidget, which the rule at the top of this
   sheet would otherwise paint in the window colour on top of the panel. */
QWidget[class="bare"] {
  background: transparent;
}
QPushButton[class="chip"] {
  padding: 5px 14px;
  border-radius: 13px;
  font-weight: 600;
}
QPushButton[class="chip"]:checked {
  background: $accent;
  color: $on_accent;
  border: 1px solid $accent_border;
}
QPushButton[class="chip"]:checked:hover {
  background: $accent_hover;
}
QPushButton[class="primary"] {
  background: $accent;
  color: $on_accent;
  font-size: $font_action;
  font-weight: 700;
  border: 1px solid $accent_border;
}
QPushButton[class="primary"]:hover {
  background: $accent_hover;
}
QPushButton[class="primary"]:pressed {
  background: $accent_pressed;
}
QPushButton[class="primary"]:focus {
  border: 1px solid $on_accent;
}
QPushButton:disabled {
  background: $disabled;
  color: $text_disabled;
  border: 1px solid $disabled_border;
}
"""
)


@dataclass(frozen=True)
class Theme:
    qss: str
    device_ok: str
    device_off: str


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    )


def theme(palette: QPalette, dark: bool) -> Theme:
    window = palette.color(QPalette.ColorRole.Window)
    base = palette.color(QPalette.ColorRole.Base)
    ink = palette.color(QPalette.ColorRole.WindowText)
    accent = QColor(_ACCENT[dark])

    # Raised surfaces move toward white in both schemes; on light the platform
    # already hands us a white Base for them.
    panel = _mix(window, _WHITE, 0.06) if dark else base
    button = _mix(window, _WHITE, 0.12) if dark else base

    tokens = {
        "window": window.name(),
        "panel": panel.name(),
        "border": _mix(window, ink, 0.14).name(),
        "input": base.name(),
        "text": _mix(ink, window, 0.12).name(),
        "text_muted": _mix(ink, window, 0.38).name(),
        "button": button.name(),
        "button_hover": (_mix(window, _WHITE, 0.20) if dark else _mix(base, window, 0.45)).name(),
        "button_pressed": (_mix(window, _WHITE, 0.04) if dark else _mix(window, ink, 0.06)).name(),
        "disabled": window.name(),
        "disabled_border": _mix(window, ink, 0.07).name(),
        "text_disabled": _mix(ink, window, 0.68).name(),
        "accent": accent.name(),
        "accent_border": accent.darker(112).name(),
        "accent_hover": accent.lighter(108).name(),
        "accent_pressed": accent.darker(118).name(),
        "on_accent": "#ffffff",
        **_FONT_TOKENS,
    }
    return Theme(
        qss=_QSS.substitute(tokens),
        device_ok=_DEVICE_OK[dark],
        device_off=_DEVICE_OFF[dark],
    )
