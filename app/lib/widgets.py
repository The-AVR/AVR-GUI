import contextlib
import os
from typing import Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from app.lib.color_config import ColorConfig
from app.lib.directory_config import IMG_DIR


class IntLineEdit(QtWidgets.QLineEdit):
    def __init__(
        self, *args: Any, min_value: int = 0, max_value: int = 1000000, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self.min_value = min_value
        self.max_value = max_value

        self.setValidator(QtGui.QIntValidator(self.min_value, self.max_value, self))


class DoubleLineEdit(QtWidgets.QLineEdit):
    def __init__(
        self,
        *args: Any,
        min_value: float = 0.0,
        max_value: float = 100.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.min_value = min_value
        self.max_value = max_value

        self.setValidator(
            QtGui.QDoubleValidator(self.min_value, self.max_value, 2, self)
        )


class DisplayLineEdit(QtWidgets.QLineEdit):
    def __init__(
        self, *args: Any, round_digits: Optional[int] = 4, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        self.round_digits = round_digits

        self.setReadOnly(True)
        self.setStyleSheet(
            f"background-color: {ColorConfig.DISPLAY_LINE_EDIT_BACKGROUND_COLOR.hex}"
        )
        self.setMaximumWidth(100)

    def setText(self, arg__1: str) -> None:
        # round incoming float values
        if self.round_digits is not None:
            with contextlib.suppress(ValueError):
                arg__1 = str(round(float(arg__1), self.round_digits))

        return super().setText(arg__1)


class StatusLabel(QtWidgets.QWidget):
    # Combination of 2 QLabels to add a status icon
    def __init__(self, text: str):
        super().__init__()

        # create a horizontal layout
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # create a label for the icon
        self.icon = QtWidgets.QLabel()
        self.icon.setFixedWidth(20)
        layout.addWidget(self.icon)
        self.set_health(False)

        # add text label
        layout.addWidget(QtWidgets.QLabel(text))

    def set_health(self, healthy: bool) -> None:
        """
        Set the health state of the status label
        """
        if healthy:
            self.icon.setPixmap(QtGui.QPixmap(os.path.join(IMG_DIR, "green.png")))
        else:
            self.icon.setPixmap(QtGui.QPixmap(os.path.join(IMG_DIR, "red.png")))


class PrePopupComboBox(QtWidgets.QComboBox):
    """
    Combobox that emits an event before the popup is shown.
    This can be used for updating its items before the popup is shown.
    """

    popup_about_to_be_shown: QtCore.SignalInstance = QtCore.Signal()  # type: ignore

    def showPopup(self) -> None:
        self.popup_about_to_be_shown.emit()
        super().showPopup()
