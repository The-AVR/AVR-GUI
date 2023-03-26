import base64
import contextlib
import math
import time
from typing import Dict, List

import numpy as np

# suppress pygame welcome message on import
with contextlib.redirect_stdout(None):
    import pygame

from bell.avr.mqtt.payloads import (
    AVRPCMServoAbsolute,
    AVRPCMServoPercent,
    AVRThermalReading,
)
from bell.avr.utils.timing import rate_limit
from PySide6 import QtCore, QtGui, QtWidgets

# fix for pyright bug not recognizing griddata as a memmber of scipy.interpolate
from scipy.interpolate import griddata as scipy_interpolate_griddata

from app.lib.calc import constrain, map_value
from app.lib.color import wrap_text
from app.lib.color_config import (
    THERMAL_VIEW_CONTROL_LASER_OFF,
    THERMAL_VIEW_CONTROL_LASER_ON,
    THERMAL_VIEW_CONTROL_MAX_COLOR,
    THERMAL_VIEW_CONTROL_MIN_COLOR,
)
from app.lib.user_config import UserConfig
from app.lib.widgets import DoubleLineEdit, PrePopupComboBox
from app.tabs.base import BaseTabWidget


class ThermalView(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        # canvas size
        self.width_ = 300
        self.height_ = self.width_

        # pixels within canvas
        self.pixels_x = 30
        self.pixels_y = self.pixels_x

        self.pixel_width = self.width_ / self.pixels_x
        self.pixel_height = self.height_ / self.pixels_y

        # low range of the sensor (this will be blue on the screen)
        self.MINTEMP = 20.0

        # high range of the sensor (this will be red on the screen)
        self.MAXTEMP = 32.0

        # last lowest temp from camera
        self.last_lowest_temp = 999.0

        # how many color values we can have
        self.COLORDEPTH = 1024

        # how many pixels the camera is
        self.camera_x = 8
        self.camera_y = self.camera_x
        self.camera_total = self.camera_x * self.camera_y

        # create list of x/y points
        self.points = [
            (math.floor(ix / self.camera_x), (ix % self.camera_y))
            for ix in range(self.camera_total)
        ]
        # i'm not fully sure what this does
        self.grid_x, self.grid_y = np.mgrid[
            0 : self.camera_x - 1 : self.camera_total / 2j,
            0 : self.camera_y - 1 : self.camera_total / 2j,
        ]

        # create avaiable colors
        self.colors = [
            (int(c.red * 255), int(c.green * 255), int(c.blue * 255))
            for c in list(
                THERMAL_VIEW_CONTROL_MIN_COLOR.range_to(
                    THERMAL_VIEW_CONTROL_MAX_COLOR, self.COLORDEPTH
                )
            )
        ]

        # create canvas
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.canvas = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.canvas)
        self.view.setGeometry(0, 0, self.width_, self.height_)

        layout.addWidget(self.view)

        # need a bit of padding for the edges of the canvas
        self.setFixedSize(self.width_ + 50, self.height_ + 50)

    def set_temp_range(self, mintemp: float, maxtemp: float) -> None:
        self.MINTEMP = mintemp
        self.MAXTEMP = maxtemp

    def set_calibrated_temp_range(self) -> None:
        self.MINTEMP = self.last_lowest_temp + 0.0
        self.MAXTEMP = self.last_lowest_temp + 15.0

    def update_canvas(self, pixels: List[int]) -> None:
        float_pixels = [
            map_value(p, self.MINTEMP, self.MAXTEMP, 0, self.COLORDEPTH - 1)
            for p in pixels
        ]

        # Rotate 90° to orient for mounting correctly
        float_pixels_matrix = np.reshape(float_pixels, (self.camera_x, self.camera_y))
        float_pixels_matrix = np.rot90(float_pixels_matrix, 1)
        rotated_float_pixels = float_pixels_matrix.flatten()

        bicubic = scipy_interpolate_griddata(
            self.points,
            rotated_float_pixels,
            (self.grid_x, self.grid_y),
            method="cubic",
        )

        pen = QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
        self.canvas.clear()

        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                brush = QtGui.QBrush(
                    QtGui.QColor(
                        *self.colors[int(constrain(pixel, 0, self.COLORDEPTH - 1))]
                    )
                )
                self.canvas.addRect(
                    self.pixel_width * jx,
                    self.pixel_height * ix,
                    self.pixel_width,
                    self.pixel_height,
                    pen,
                    brush,
                )


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
        print("signals emitted")

    def run(self) -> None:
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.loop)
        # self.timer.start(100)
        while True:
            self.loop()
            time.sleep(500)


class GamepadManager(QtWidgets.QWidget):
    x_axis_value: QtCore.SignalInstance = QtCore.Signal(float)  # type: ignore
    y_axis_value: QtCore.SignalInstance = QtCore.Signal(float)  # type: ignore

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

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

        update_joysticks_timer = QtCore.QTimer(self)
        update_joysticks_timer.timeout.connect(self.update_joysticks_manager)
        update_joysticks_timer.start(100)
        # thread_manager = QtCore.QThreadPool()
        # thread_manager.start(self.update_joysticks_loop)

        # gamepad_updater = GamepadUpdater()
        # self.gamepad_updater_thread = QtCore.QThread(self)
        # self.gamepad_updater_thread.started.connect(gamepad_updater.run)  # type: ignore
        # gamepad_updater.moveToThread(self.gamepad_updater_thread)

        # gamepad_updater_thread.finished.connect(gamepad_updater.deleteLater)

        # gamepad_updater.joystick_name_to_guid_signal.connect(
        #     self.update_joystick_name_to_guid
        # )
        # gamepad_updater.joystick_guid_to_name_signal.connect(
        #     self.update_joystick_guid_to_name
        # )
        # gamepad_updater.joystick_guid_to_axes_signal.connect(
        #     self.update_joystick_guid_to_axes
        # )
        # # gamepad_updater.start()

        # self.gamepad_updater_thread.start()
        # self.destroyed.connect(self.gamepad_updater_thread.quit)  # type: ignore

    def update_joystick_name_to_guid(
        self, joystick_name_to_guid: Dict[str, str]
    ) -> None:
        print("Slot run")
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

    # def update_joysticks_loop(self) -> None:
    #     while True:
    #         self.update_joysticks()
    #         QtWidgets.QApplication.processEvents()
    #         time.sleep(0.1)

    def update_joysticks_manager(self) -> None:
        thread = QtCore.QThread(self)
        thread.started.connect(self.update_joysticks)
        thread.finished.connect(self.update_gamepad_combobox)
        thread.start()

    def update_joysticks(self) -> None:
        """
        Update our cache of joystick information
        """
        print("update_joysticks")

        if not pygame.get_init():
            pygame.init()

        if not pygame.joystick.get_init():
            pygame.joystick.init()

        # processing events is required to update joystick list
        pygame.event.pump()

        for j in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(j)
            self.joystick_name_to_guid[joystick.get_name()] = joystick.get_guid()
            self.joystick_guid_to_name[joystick.get_guid()] = joystick.get_name()
            self.joystick_guid_to_axes[joystick.get_guid()] = [
                joystick.get_axis(a) for a in range(joystick.get_numaxes())
            ]

        # self.update_gamepad_combobox()

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


class JoystickWidget(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        # dimensions of the bounding box, and joystick
        self.BOUNDING_BOX_WIDTH = 200
        self.BOUNDING_BOX_HEIGHT = 200
        self.JOYSTICK_RADIUS = 20

        # add an extra amount so things are clipping at the edge
        self.WIDTH = round(self.BOUNDING_BOX_WIDTH * 1.5)
        self.HEIGHT = round(self.BOUNDING_BOX_HEIGHT * 1.5)

        self.setFixedSize(self.WIDTH, self.HEIGHT)

        # calculate edges of bounding box
        self.BOUNDING_BOX_MIN_X = int(self._center().x() - self.BOUNDING_BOX_WIDTH / 2)
        self.BOUNDING_BOX_MAX_X = int(self._center().x() + self.BOUNDING_BOX_WIDTH / 2)
        self.BOUNDING_BOX_MIN_Y = int(self._center().y() - self.BOUNDING_BOX_HEIGHT / 2)
        self.BOUNDING_BOX_MAX_Y = int(self._center().y() + self.BOUNDING_BOX_HEIGHT / 2)

        # absolute position within the widget of where the joystick is
        self.joystick_center_abs = QtCore.QPointF(0, 0)
        # relative position within the widget of where the joystick is
        self.joystick_center_rel = QtCore.QPointF(0, 0)

        # record if joystick was grabbed
        self.joystick_grabbed = False

        # servo values
        self.SERVO_ABS_MAX = 2200
        self.SERVO_ABS_MIN = 700

    def _center(self) -> QtCore.QPointF:
        """
        Return the center of the widget.
        """
        return QtCore.QPointF(self.width() / 2, self.height() / 2)

    def move_gimbal(self, x_servo_percent: int, y_servo_percent: int) -> None:
        self.send_message(
            "avr/pcm/servo/percent",
            AVRPCMServoPercent(servo=2, percent=x_servo_percent),
        )
        self.send_message(
            "avr/pcm/servo/percent",
            AVRPCMServoPercent(servo=3, percent=y_servo_percent),
        )

    def move_gimbal_absolute(self, x_servo_abs: int, y_servo_abs: int) -> None:
        self.send_message(
            "avr/pcm/servo/absolute",
            AVRPCMServoAbsolute(servo=2, position=x_servo_abs),
        )
        self.send_message(
            "avr/pcm/servo/absolute",
            AVRPCMServoAbsolute(servo=3, position=y_servo_abs),
        )

    def update_servos(self) -> None:
        """
        Update the servos on joystick movement.
        """
        x_servo_abs = round(
            map_value(
                self.joystick_center_rel.x(),
                0,
                self.BOUNDING_BOX_WIDTH,
                self.SERVO_ABS_MIN,
                self.SERVO_ABS_MAX,
            )
        )
        y_servo_abs = round(
            map_value(
                self.joystick_center_rel.y(),
                0,
                self.BOUNDING_BOX_HEIGHT,
                self.SERVO_ABS_MIN,
                self.SERVO_ABS_MAX,
            )
        )

        self.move_gimbal_absolute(x_servo_abs, y_servo_abs)

    def _joystick_rect(self) -> QtCore.QRectF:
        """
        Return the rectangle representing the edges of the joystick.
        """
        # sourcery skip: assign-if-exp
        if self.joystick_grabbed:
            # if the joystick was grabbed, the center is now it's current position
            center = self.joystick_center_abs
        else:
            # otherwise, re-center i
            center = self._center()

        return QtCore.QRectF(
            -self.JOYSTICK_RADIUS,
            -self.JOYSTICK_RADIUS,
            2 * self.JOYSTICK_RADIUS,
            2 * self.JOYSTICK_RADIUS,
        ).translated(center)

    def _bound_joystick(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """
        If the joystick is leaving the widget, bound it to the edge of the widget.
        """
        if point.x() > (self.BOUNDING_BOX_MAX_X):
            point.setX(self.BOUNDING_BOX_MAX_X)
        elif point.x() < (self.BOUNDING_BOX_MIN_X):
            point.setX(self.BOUNDING_BOX_MIN_X)

        if point.y() > (self.BOUNDING_BOX_MAX_Y):
            point.setY(self.BOUNDING_BOX_MAX_Y)
        elif point.y() < (self.BOUNDING_BOX_MIN_Y):
            point.setY(self.BOUNDING_BOX_MIN_Y)

        return point

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)

        # draw the bounding box
        bounds = QtCore.QRectF(
            self.BOUNDING_BOX_MIN_X,
            self.BOUNDING_BOX_MIN_Y,
            self.BOUNDING_BOX_WIDTH,
            self.BOUNDING_BOX_HEIGHT,
        )
        painter.drawRect(bounds)

        # draw the joystick
        painter.setBrush(QtCore.Qt.GlobalColor.black)
        painter.drawEllipse(self._joystick_rect())

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> QtGui.QMouseEvent:
        """
        On a mouse press, check if we've clicked on the joystick.
        """
        self.joystick_grabbed = self._joystick_rect().contains(event.pos())
        return event

    def mouseReleaseEvent(self, event: QtCore.QEvent) -> None:
        """
        When the mouse is released, update the joystick position. This is
        for when the center is clicked, and not the joystick itself.
        """
        # trigger a repaint
        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Process a mouse move event.
        """
        if self.joystick_grabbed:
            self.joystick_center_abs = self._bound_joystick(event.pos())
            # trigger a repaint
            self.update()

        joystick_center_abs_y = self.joystick_center_abs.y()
        if UserConfig.joystick_inverted:
            joystick_center_abs_y = self.height() - joystick_center_abs_y

        # set the current relative position
        self.joystick_center_rel = QtCore.QPointF(
            self.joystick_center_abs.x()
            - self._center().x()
            + self.BOUNDING_BOX_WIDTH / 2,
            joystick_center_abs_y - self._center().y() + self.BOUNDING_BOX_HEIGHT / 2,
        )

        # update servos
        rate_limit(self.update_servos, frequency=50)


class ThermalViewControlWidget(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("Thermal View/Control")

        self.topic_callbacks = {"avr/thermal/reading": self.process_thermal_reading}

    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QHBoxLayout(self)
        layout_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        layout.addWidget(layout_splitter)
        self.setLayout(layout)

        # viewer
        viewer_groupbox = QtWidgets.QGroupBox("Viewer")
        viewer_layout = QtWidgets.QVBoxLayout()
        viewer_groupbox.setLayout(viewer_layout)

        # this sub layout is used to keep the viewer centered in the column
        sub_viewer_layout = QtWidgets.QHBoxLayout()
        self.viewer = ThermalView(self)
        sub_viewer_layout.addWidget(self.viewer)
        viewer_layout.addLayout(sub_viewer_layout)

        # set temp range

        temp_range_layout = QtWidgets.QFormLayout()

        self.temp_min_line_edit = DoubleLineEdit()
        temp_range_layout.addRow(QtWidgets.QLabel("Min Temp:"), self.temp_min_line_edit)
        self.temp_min_line_edit.setText(str(self.viewer.MINTEMP))

        self.temp_max_line_edit = DoubleLineEdit()
        temp_range_layout.addRow(QtWidgets.QLabel("Max Temp:"), self.temp_max_line_edit)
        self.temp_max_line_edit.setText(str(self.viewer.MAXTEMP))

        viewer_layout.addLayout(temp_range_layout)

        button_layout = QtWidgets.QVBoxLayout()
        set_temp_range_button = QtWidgets.QPushButton("Set Temp Range")
        button_layout.addWidget(set_temp_range_button)

        set_temp_range_calibrate_button = QtWidgets.QPushButton(
            "Auto Calibrate Temp Range"
        )
        button_layout.addWidget(set_temp_range_calibrate_button)
        viewer_layout.addLayout(button_layout)

        layout_splitter.addWidget(viewer_groupbox)

        right_side_widget = QtWidgets.QWidget()
        right_side_layout = QtWidgets.QVBoxLayout()
        right_side_widget.setLayout(right_side_layout)

        # joystick
        joystick_groupbox = QtWidgets.QGroupBox("Joystick")
        joystick_layout = QtWidgets.QVBoxLayout()
        joystick_groupbox.setLayout(joystick_layout)

        # this hbox is used to keep the joystick centered in the column
        sub_joystick_layout = QtWidgets.QHBoxLayout()
        joystick_layout.addLayout(sub_joystick_layout)

        joystick = JoystickWidget(self)
        sub_joystick_layout.addWidget(joystick)

        # https://i.imgur.com/yvgNiFE.jpg
        self.joystick_inverted_checkbox = QtWidgets.QCheckBox("Invert Joystick")
        joystick_layout.addWidget(self.joystick_inverted_checkbox)
        self.joystick_inverted_checkbox.setChecked(UserConfig.joystick_inverted)

        self.gamepad_manager = GamepadManager(self)
        joystick_layout.addWidget(self.gamepad_manager)

        right_side_layout.addWidget(joystick_groupbox)

        # laser
        laser_groupbox = QtWidgets.QGroupBox("Laser")
        laser_layout = QtWidgets.QVBoxLayout()
        laser_groupbox.setLayout(laser_layout)

        fire_laser_button = QtWidgets.QPushButton("Fire Laser")
        laser_layout.addWidget(fire_laser_button)

        laser_toggle_layout = QtWidgets.QHBoxLayout()

        laser_on_button = QtWidgets.QPushButton("Laser On")
        laser_toggle_layout.addWidget(laser_on_button)

        laser_off_button = QtWidgets.QPushButton("Laser Off")
        laser_toggle_layout.addWidget(laser_off_button)

        self.laser_toggle_label = QtWidgets.QLabel()
        self.laser_toggle_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        laser_toggle_layout.addWidget(self.laser_toggle_label)
        laser_layout.addLayout(laser_toggle_layout)

        right_side_layout.addWidget(laser_groupbox)

        layout_splitter.addWidget(right_side_widget)

        # connect signals
        set_temp_range_button.clicked.connect(  # type: ignore
            lambda: self.viewer.set_temp_range(
                float(self.temp_min_line_edit.text()),
                float(self.temp_max_line_edit.text()),
            )
        )

        set_temp_range_calibrate_button.clicked.connect(  # type: ignore
            lambda: self.calibrate_temp()
        )

        joystick.send_message_signal.connect(self.send_message_signal.emit)

        fire_laser_button.clicked.connect(  # type: ignore
            lambda: self.send_message("avr/pcm/laser/fire")
        )

        laser_on_button.clicked.connect(self.laser_on)  # type: ignore
        laser_off_button.clicked.connect(self.laser_off)  # type: ignore

        self.joystick_inverted_checkbox.clicked.connect(self.inverted_checkbox_clicked)  # type: ignore

        # don't allow us to shrink below size hint
        self.setMinimumSize(self.sizeHint())

    def inverted_checkbox_clicked(self) -> None:
        """
        Callback when joystick inverted checkbox is clicked
        """
        UserConfig.joystick_inverted = self.joystick_inverted_checkbox.isChecked()

    def laser_on(self) -> None:
        text = "Laser On"
        color = THERMAL_VIEW_CONTROL_LASER_ON

        self.send_message("avr/pcm/laser/on")
        self.laser_toggle_label.setText(wrap_text(text, color))

    def laser_off(self) -> None:
        text = "Laser Off"
        color = THERMAL_VIEW_CONTROL_LASER_OFF

        self.send_message("avr/pcm/laser/off")
        self.laser_toggle_label.setText(wrap_text(text, color))

    def calibrate_temp(self) -> None:
        self.viewer.set_calibrated_temp_range()
        self.temp_min_line_edit.setText(str(self.viewer.MINTEMP))
        self.temp_max_line_edit.setText(str(self.viewer.MAXTEMP))

    def process_thermal_reading(self, payload: AVRThermalReading) -> None:
        # decode the payload
        base64_decoded = payload.data.encode("utf-8")
        asbytes = base64.b64decode(base64_decoded)
        pixel_ints = list(bytearray(asbytes))

        # find lowest temp
        lowest = min(pixel_ints)
        self.viewer.last_lowest_temp = lowest

        # update the canvase
        # pixel_ints = data
        self.viewer.update_canvas(pixel_ints)

    def clear(self) -> None:
        self.viewer.canvas.clear()
