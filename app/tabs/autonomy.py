from __future__ import annotations

import functools

from bell.avr.mqtt.payloads import (
    AVRAutonomousBuildingDisable,
    AVRAutonomousBuildingEnable,
)
from PySide6 import QtCore, QtWidgets

from app.lib.color import wrap_text
from app.lib.color_config import ColorConfig
from app.tabs.base import BaseTabWidget


class AutonomyWidget(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("Autonomy")

    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

        # ==========================
        # Autonomous mode
        autonomous_groupbox = QtWidgets.QGroupBox("Autonomous")
        autonomous_layout = QtWidgets.QHBoxLayout()
        autonomous_groupbox.setLayout(autonomous_layout)

        autonomous_enable_button = QtWidgets.QPushButton("Enable")
        autonomous_enable_button.clicked.connect(self.enable_autonomous)  # type: ignore
        autonomous_layout.addWidget(autonomous_enable_button)

        autonomous_disable_button = QtWidgets.QPushButton("Disable")
        autonomous_disable_button.clicked.connect(self.disable_autonomous)  # type: ignore
        autonomous_layout.addWidget(autonomous_disable_button)

        self.autonomous_label = QtWidgets.QLabel()
        self.autonomous_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        autonomous_layout.addWidget(self.autonomous_label)

        layout.addWidget(autonomous_groupbox, 0, 0, 1, 1)

        # ==========================
        # Buildings
        self.number_of_buildings = 6
        self.building_labels: list[QtWidgets.QLabel] = []

        buildings_groupbox = QtWidgets.QGroupBox("Buildings")
        buildings_layout = QtWidgets.QVBoxLayout()
        buildings_groupbox.setLayout(buildings_layout)

        building_all_layout = QtWidgets.QHBoxLayout()

        building_all_enable_button = QtWidgets.QPushButton("Enable All Drops")
        building_all_enable_button.clicked.connect(self.enable_building_drop_all)  # type: ignore
        building_all_layout.addWidget(building_all_enable_button)

        building_all_disable_button = QtWidgets.QPushButton("Disable All Drops")
        building_all_disable_button.clicked.connect(self.disable_building_drop_all)  # type: ignore
        building_all_layout.addWidget(building_all_disable_button)

        buildings_layout.addLayout(building_all_layout)

        for i in range(self.number_of_buildings):
            building_groupbox = QtWidgets.QGroupBox(f"Building {i}")
            building_layout = QtWidgets.QHBoxLayout()
            building_groupbox.setLayout(building_layout)

            building_enable_button = QtWidgets.QPushButton("Enable Drop")
            building_enable_button.clicked.connect(functools.partial(self.enable_building_drop, i))  # type: ignore
            building_layout.addWidget(building_enable_button)

            building_disable_button = QtWidgets.QPushButton("Disable Drop")
            building_disable_button.clicked.connect(functools.partial(self.disable_building_drop, i))  # type: ignore
            building_layout.addWidget(building_disable_button)

            building_label = QtWidgets.QLabel()
            building_label.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight
                | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            building_layout.addWidget(building_label)
            self.building_labels.append(building_label)

            buildings_layout.addWidget(building_groupbox)

        layout.addWidget(buildings_groupbox, 1, 0, 4, 1)

    def enable_building_drop(self, number: int) -> None:
        """
        Enable building drop
        """
        self.send_message(
            "avr/autonomous/building/enable",
            AVRAutonomousBuildingEnable(building=number),
        )

        text = "Drop Enabled"
        color = ColorConfig.AUTONOMY_DROP_ENABLED_COLOR
        self.building_labels[number].setText(wrap_text(text, color))

    def disable_building_drop(self, number: int) -> None:
        """
        Disable building drop
        """
        self.send_message(
            "avr/autonomous/building/disable",
            AVRAutonomousBuildingDisable(building=number),
        )

        text = "Drop Disabled"
        color = ColorConfig.AUTONOMY_DROP_DISABLED_COLOR
        self.building_labels[number].setText(wrap_text(text, color))

    def enable_building_drop_all(self) -> None:
        """
        Enable all building drops
        """
        for i in range(self.number_of_buildings):
            self.enable_building_drop(i)

    def disable_building_drop_all(self) -> None:
        """
        Disable all building drops
        """
        for i in range(self.number_of_buildings):
            self.disable_building_drop(i)

    def enable_autonomous(self) -> None:
        """
        Enable autonomous mode
        """
        self.send_message("avr/autonomous/enable")

        text = "Autonomous Enabled"
        color = ColorConfig.AUTONOMY_AUTONOMOUS_ENABLED_COLOR
        self.autonomous_label.setText(wrap_text(text, color))

    def disable_autonomous(self) -> None:
        """
        Disable autonomous mode
        """
        self.send_message("avr/autonomous/disable")

        text = "Autonomous Disabled"
        color = ColorConfig.AUTONOMY_AUTONOMOUS_DISABLED_COLOR
        self.autonomous_label.setText(wrap_text(text, color))
