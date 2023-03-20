from __future__ import annotations

from bell.avr.mqtt.qt_widget import MQTTWidget
from PySide6 import QtCore, QtGui, QtWidgets

from app.lib.qt_icon import set_icon


class BaseTabWidget(MQTTWidget):
    pop_in: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        set_icon(self)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.pop_in.emit(self)
        return super().closeEvent(event)
