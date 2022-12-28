from __future__ import annotations

import functools
from typing import List, Literal, Tuple

from bell.avr.mqtt.payloads import (
    AvrPcmSetBaseColorPayload,
    AvrPcmSetServoOpenClosePayload,
)
from PySide6 import QtCore, QtWidgets

from ..lib.color import wrap_text
from ..lib.custom_colors import (
    BLACK_COLOR,
    BLUE_COLOR,
    GREEN_COLOR,
    RED_COLOR,
    VMC_CONTROL_SERVO_CLOSED_COLOR,
    VMC_CONTROL_SERVO_OPEN_COLOR,
    WHITE_COLOR,
)
from .base import BaseTabWidget


class VMCControlWidget(BaseTabWidget):
    # This is the primary control widget for the drone. This allows the user
    # to set LED color, open/close servos etc.

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("VMC Control")

    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

        # ==========================
        # LEDs
        led_groupbox = QtWidgets.QGroupBox("LEDs")
        led_layout = QtWidgets.QVBoxLayout()
        led_groupbox.setLayout(led_layout)

        red_led_button = QtWidgets.QPushButton("Red")
        red_led_button.setStyleSheet(
            f"background-color: {RED_COLOR.hex}; color: {BLACK_COLOR.hex}"
        )
        red_led_button.clicked.connect(lambda: self.set_led((255, *RED_COLOR.rgb_255)))  # type: ignore
        led_layout.addWidget(red_led_button)

        green_led_button = QtWidgets.QPushButton("Green")
        green_led_button.setStyleSheet(
            f"background-color: {GREEN_COLOR.hex}; color: {BLACK_COLOR.hex}"
        )
        green_led_button.clicked.connect(lambda: self.set_led((255, *GREEN_COLOR.rgb_255)))  # type: ignore
        led_layout.addWidget(green_led_button)

        blue_led_button = QtWidgets.QPushButton("Blue")
        blue_led_button.setStyleSheet(
            f"background-color: {BLUE_COLOR.hex}; color: {WHITE_COLOR.hex}"
        )
        blue_led_button.clicked.connect(lambda: self.set_led((255, *BLUE_COLOR.rgb_255)))  # type: ignore
        led_layout.addWidget(blue_led_button)

        clear_led_button = QtWidgets.QPushButton("Clear")
        clear_led_button.setStyleSheet(
            f"background-color: {WHITE_COLOR.hex}; color: {BLACK_COLOR.hex}"
        )
        clear_led_button.clicked.connect(lambda: self.set_led((0, *BLACK_COLOR.rgb_255)))  # type: ignore
        led_layout.addWidget(clear_led_button)

        layout.addWidget(led_groupbox, 0, 0, 3, 1)

        # ==========================
        # Servos
        self.number_of_servos = 4
        self.servo_labels: List[QtWidgets.QLabel] = []

        servos_groupbox = QtWidgets.QGroupBox("Servos")
        servos_layout = QtWidgets.QVBoxLayout()
        servos_groupbox.setLayout(servos_layout)

        servo_all_layout = QtWidgets.QHBoxLayout()

        servo_all_open_button = QtWidgets.QPushButton("Open all")
        servo_all_open_button.clicked.connect(lambda: self.set_servo_all("open"))  # type: ignore
        servo_all_layout.addWidget(servo_all_open_button)

        servo_all_close_button = QtWidgets.QPushButton("Close all")
        servo_all_close_button.clicked.connect(lambda: self.set_servo_all("close"))  # type: ignore
        servo_all_layout.addWidget(servo_all_close_button)

        servos_layout.addLayout(servo_all_layout)

        for i in range(self.number_of_servos):
            servo_groupbox = QtWidgets.QGroupBox(f"Servo {i+1}")
            servo_layout = QtWidgets.QHBoxLayout()
            servo_groupbox.setLayout(servo_layout)

            servo_open_button = QtWidgets.QPushButton("Open")
            servo_open_button.clicked.connect(functools.partial(self.set_servo, i, "open"))  # type: ignore
            servo_layout.addWidget(servo_open_button)

            servo_close_button = QtWidgets.QPushButton("Close")
            servo_close_button.clicked.connect(functools.partial(self.set_servo, i, "close"))  # type: ignore
            servo_layout.addWidget(servo_close_button)

            servo_label = QtWidgets.QLabel()
            servo_label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight
                | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            servo_layout.addWidget(servo_label)
            self.servo_labels.append(servo_label)

            servos_layout.addWidget(servo_groupbox)

        layout.addWidget(servos_groupbox, 0, 1, 3, 3)

        # # ==========================
        # # PCC Reset
        # reset_groupbox = QtWidgets.QGroupBox("Reset")
        # reset_layout = QtWidgets.QVBoxLayout()
        # reset_groupbox.setLayout(reset_layout)

        # reset_button = QtWidgets.QPushButton("Reset PCC")
        # reset_button.setStyleSheet("background-color: yellow")
        # reset_button.clicked.connect(lambda: self.send_message("avr/pcm/reset", AvrPcmResetPayload()))  # type: ignore
        # reset_layout.addWidget(reset_button)

        # layout.addWidget(reset_groupbox, 3, 3, 1, 1)

    def set_servo(self, number: int, action: Literal["open", "close"]) -> None:
        """
        Set a servo state
        """
        self.send_message(
            "avr/pcm/set_servo_open_close",
            AvrPcmSetServoOpenClosePayload(servo=number, action=action),
        )

        if action == "open":
            text = "Opened"
            color = VMC_CONTROL_SERVO_OPEN_COLOR
        else:
            text = "Closed"
            color = VMC_CONTROL_SERVO_CLOSED_COLOR

        self.servo_labels[number].setText(wrap_text(text, color))

    def set_servo_all(self, action: Literal["open", "close"]) -> None:
        """
        Set all servos to the same state
        """
        for i in range(self.number_of_servos):
            self.set_servo(i, action)

    def set_led(self, color: Tuple[int, int, int, int]) -> None:
        """
        Set LED color
        """
        self.send_message(
            "avr/pcm/set_base_color", AvrPcmSetBaseColorPayload(wrgb=color)
        )
