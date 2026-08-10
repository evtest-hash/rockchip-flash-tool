STYLESHEET = """
QMainWindow, QWidget {
  background: #f4f5f7;
  color: #1f2328;
}
QFrame[class="panel"] {
  background: #ffffff;
  border: 1px solid #dcdfe4;
  border-radius: 10px;
}
QLineEdit {
  border: 1px solid #cfd4dc;
  border-radius: 8px;
  padding: 6px 10px;
  background: #ffffff;
  color: #1f2328;
  selection-background-color: #1e80e2;
  selection-color: #ffffff;
}
QLineEdit:disabled {
  background: #f2f4f7;
  color: #5c6675;
}
QLabel {
  color: #1f2328;
  font-size: 12px;
}
QPushButton {
  border-radius: 8px;
  padding: 7px 14px;
  background: #eceff3;
  color: #1f2328;
  border: 1px solid #d3d9e2;
  font-size: 12px;
}
QPushButton[class="primary"] {
  background: #1e80e2;
  color: white;
  font-weight: 600;
  border: 1px solid #1a72ca;
}
QPushButton[class="secondary"] {
  background: #eceff3;
  color: #1f2328;
}
QPushButton[class="secondary"]:enabled {
  color: #111827;
  background: #e9edf2;
}
QPushButton:disabled {
  background: #f0f2f5;
  color: #9aa3af;
  border: 1px solid #e1e5ea;
}
QStatusBar {
  background: #171a20;
  color: #e5e7eb;
  border-top: 1px solid #2a2f37;
}
"""
