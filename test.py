import contextlib
import sys
from typing import Dict, List

from loguru import logger

# suppress pygame welcome message on import
with contextlib.redirect_stdout(None):
    import pygame

from PySide6 import QtCore, QtWidgets

# fix for pyright bug not recognizing griddata as a memmber of scipy.interpolate
from app.lib.user_config import UserConfig
from app.lib.widgets import PrePopupComboBox


class GamepadUpdater(QtCore.QObject):
    joystick_name_to_guid_signal: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore
    joystick_guid_to_name_signal: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore
    joystick_guid_to_axes_signal: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore

    def __init__(self) -> None:
        super().__init__()

        if not pygame.get_init():
            pygame.init()

        if not pygame.joystick.get_init():
            pygame.joystick.init()

    def loop(self) -> None:
        # processing events is required to update joystick list
        pygame.event.pump()

        joystick_name_to_guid = {}
        joystick_guid_to_name = {}
        joystick_guid_to_axes = {}

        for j in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(j)
            joystick_name_to_guid[joystick.get_name()] = joystick.get_guid()
            joystick_guid_to_name[joystick.get_guid()] = joystick.get_name()
            joystick_guid_to_axes[joystick.get_guid()] = [
                joystick.get_axis(a) for a in range(joystick.get_numaxes())
            ]

        self.joystick_name_to_guid_signal.emit(joystick_name_to_guid)
        self.joystick_guid_to_name_signal.emit(joystick_guid_to_name)
        self.joystick_guid_to_axes_signal.emit(joystick_guid_to_axes)

    def run(self) -> None:
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.loop)
        # self.timer.start(100)
        x = 0
        while True:
            logger.debug(f"Loop {x} started")
            self.loop()
            logger.debug(f"Loop {x} run")
            # time.sleep(100)
            logger.debug(f"Loop {x} waited")
            x += 1


class GamepadManager(QtWidgets.QWidget):
    x_axis_value: QtCore.SignalInstance = QtCore.Signal(float)  # type: ignore
    y_axis_value: QtCore.SignalInstance = QtCore.Signal(float)  # type: ignore

    def __init__(self) -> None:
        super().__init__()

        # dict of joystick guid, with name, and number of axes
        self.joystick_name_to_guid: Dict[str, str] = {}
        self.joystick_guid_to_name: Dict[str, str] = {}
        self.joystick_guid_to_axes: Dict[str, List[float]] = {}

        self.build()

    def build(self) -> None:
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        # first row
        gamepad_label = QtWidgets.QLabel("Gamepad")
        layout.addWidget(gamepad_label, 0, 0)

        self.gamepad_combobox = PrePopupComboBox()
        layout.addWidget(self.gamepad_combobox, 0, 1)

        self.gamepad_enabled_checkbox = QtWidgets.QCheckBox("Enable")
        self.gamepad_enabled_checkbox.setDisabled(True)
        layout.addWidget(self.gamepad_enabled_checkbox, 0, 2)

        # second row
        x_axis_label = QtWidgets.QLabel("X Axis")
        layout.addWidget(x_axis_label, 1, 0)

        self.x_axis_combobox = QtWidgets.QComboBox()
        self.x_axis_combobox.setDisabled(True)
        layout.addWidget(self.x_axis_combobox, 1, 1)

        self.x_axis_inverted_checkbox = QtWidgets.QCheckBox("Invert X Axis")
        self.x_axis_inverted_checkbox.setDisabled(True)
        layout.addWidget(self.x_axis_inverted_checkbox, 1, 2)

        # third row
        y_axis_label = QtWidgets.QLabel("Y Axis")
        layout.addWidget(y_axis_label, 2, 0)

        self.y_axis_combobox = QtWidgets.QComboBox()
        self.y_axis_combobox.setDisabled(True)
        layout.addWidget(self.y_axis_combobox, 2, 1)

        self.y_axis_inverted_checkbox = QtWidgets.QCheckBox("Invert Y Axis")
        self.y_axis_inverted_checkbox.setDisabled(True)
        layout.addWidget(self.y_axis_inverted_checkbox, 2, 2)

        self.gamepad_updater = GamepadUpdater()
        self.gamepad_updater_thread = QtCore.QThread(self)
        self.gamepad_updater.moveToThread(self.gamepad_updater_thread)

        self.gamepad_updater.joystick_name_to_guid_signal.connect(
            self.update_joystick_name_to_guid
        )
        self.gamepad_updater.joystick_guid_to_name_signal.connect(
            self.update_joystick_guid_to_name
        )
        self.gamepad_updater.joystick_guid_to_axes_signal.connect(
            self.update_joystick_guid_to_axes
        )

        self.show()

        self.gamepad_updater_thread.start()
        self.gamepad_updater.run()

    def update_joystick_name_to_guid(
        self, joystick_name_to_guid: Dict[str, str]
    ) -> None:
        self.joystick_name_to_guid = joystick_name_to_guid

    def update_joystick_guid_to_name(
        self, joystick_guid_to_name: Dict[str, str]
    ) -> None:
        self.joystick_guid_to_name = joystick_guid_to_name
        self.update_gamepad_combobox()

    def update_joystick_guid_to_axes(
        self, joystick_guid_to_axes: Dict[str, List[float]]
    ) -> None:
        self.joystick_guid_to_axes = joystick_guid_to_axes
        self.update_axes_comboboxes()

    def update_gamepad_combobox(self) -> None:
        """
        Update the gamepad combobox
        """
        self.gamepad_combobox.clear()
        self.gamepad_combobox.addItems(list(self.joystick_name_to_guid.keys()))

        # if we have something in the config, set it
        if UserConfig.gamepad_guid in self.joystick_guid_to_name:
            self.gamepad_combobox.setCurrentIndex(
                self.gamepad_combobox.findText(
                    self.joystick_guid_to_name[UserConfig.gamepad_guid]
                )
            )

        # self.update_axes_comboboxes()

    # def update_axes_comboboxes(self) -> None:
    #     """
    #     Update the axes comboboxes
    #     """
    #     self.x_axis_combobox.clear()
    #     self.y_axis_combobox.clear()

    #     if (
    #         not self.gamepad_combobox.currentText()
    #         or self.gamepad_combobox.currentIndex() == -1
    #     ):
    #         # if no item is selected, disable the other combo boxes
    #         self.gamepad_enabled_checkbox.setDisabled(True)
    #         self.x_axis_combobox.setDisabled(True)
    #         self.x_axis_inverted_checkbox.setDisabled(True)
    #         self.y_axis_combobox.setDisabled(True)
    #         self.y_axis_inverted_checkbox.setDisabled(True)

    #     else:
    #         selected_guid = self.joystick_name_to_guid[
    #             self.gamepad_combobox.currentText()
    #         ]

    #         # populate the other combo boxes
    #         self.gamepad_enabled_checkbox.setEnabled(True)

    #         self.x_axis_combobox.addItems(
    #             list(
    #                 f"Axis {i} - {x}"
    #                 for i, x in enumerate(self.joystick_guid_to_axes[selected_guid])
    #             )
    #         )
    #         self.x_axis_combobox.setEnabled(True)
    #         self.x_axis_inverted_checkbox.setEnabled(True)

    #         # load settings if this is our saved gamepad
    #         if UserConfig.gamepad_guid == selected_guid and selected_guid:
    #             self.x_axis_combobox.setCurrentIndex(UserConfig.gamepad_x_axis)
    #             self.x_axis_inverted_checkbox.setChecked(
    #                 UserConfig.gamepad_x_axis_inverted
    #             )

    #         self.y_axis_combobox.setEnabled(True)
    #         self.y_axis_combobox.addItems(
    #             list(
    #                 f"Axis {i} - {y}"
    #                 for i, y in enumerate(self.joystick_guid_to_axes[selected_guid])
    #             )
    #         )
    #         self.y_axis_inverted_checkbox.setEnabled(True)

    #         # load settings if this is our saved gamepad
    #         if UserConfig.gamepad_guid == selected_guid:
    #             self.y_axis_combobox.setCurrentIndex(UserConfig.gamepad_y_axis)
    #             self.y_axis_inverted_checkbox.setChecked(
    #                 UserConfig.gamepad_y_axis_inverted
    #             )

    def update_axes_comboboxes(self) -> None:
        """
        Update the axes comboboxes
        """
        self.x_axis_combobox.clear()
        self.y_axis_combobox.clear()

        if (
            not self.gamepad_combobox.currentText()
            or self.gamepad_combobox.currentIndex() == -1
        ):
            # if no item is selected, disable the other combo boxes
            self.gamepad_enabled_checkbox.setDisabled(True)
            self.x_axis_combobox.setDisabled(True)
            self.x_axis_inverted_checkbox.setDisabled(True)
            self.y_axis_combobox.setDisabled(True)
            self.y_axis_inverted_checkbox.setDisabled(True)

        else:
            selected_guid = self.joystick_name_to_guid[
                self.gamepad_combobox.currentText()
            ]

            # populate the other combo boxes
            self.gamepad_enabled_checkbox.setEnabled(True)

            self.x_axis_combobox.addItems(
                list(
                    f"Axis {i} - {x}"
                    for i, x in enumerate(self.joystick_guid_to_axes[selected_guid])
                )
            )
            self.x_axis_combobox.setEnabled(True)
            self.x_axis_inverted_checkbox.setEnabled(True)

            # load settings if this is our saved gamepad
            if UserConfig.gamepad_guid == selected_guid and selected_guid:
                self.x_axis_combobox.setCurrentIndex(UserConfig.gamepad_x_axis)
                self.x_axis_inverted_checkbox.setChecked(
                    UserConfig.gamepad_x_axis_inverted
                )

            self.y_axis_combobox.setEnabled(True)
            self.y_axis_combobox.addItems(
                list(
                    f"Axis {i} - {y}"
                    for i, y in enumerate(self.joystick_guid_to_axes[selected_guid])
                )
            )
            self.y_axis_inverted_checkbox.setEnabled(True)

            # load settings if this is our saved gamepad
            if UserConfig.gamepad_guid == selected_guid:
                self.y_axis_combobox.setCurrentIndex(UserConfig.gamepad_y_axis)
                self.y_axis_inverted_checkbox.setChecked(
                    UserConfig.gamepad_y_axis_inverted
                )

    def save_gamepad_settings(self) -> None:
        """
        Save gamepad settings on any change
        """
        UserConfig.gamepad_guid = self.joystick_name_to_guid[
            self.gamepad_combobox.currentText()
        ]
        UserConfig.gamepad_x_axis = self.x_axis_combobox.currentIndex()
        UserConfig.gamepad_x_axis_inverted = self.x_axis_inverted_checkbox.isChecked()

        UserConfig.gamepad_y_axis = self.y_axis_combobox.currentIndex()
        UserConfig.gamepad_y_axis_inverted = self.y_axis_inverted_checkbox.isChecked()


if __name__ == "__main__":
    app = QtWidgets.QApplication()

    # create the main window
    w = GamepadManager()
    w.build()
    w.show()

    # run
    sys.exit(app.exec())
