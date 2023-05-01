import base64
import math
from typing import List

import numpy as np
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
from app.lib.color_config import ColorConfig
from app.lib.user_config import UserConfig
from app.lib.widgets import DoubleLineEdit
from app.tabs.base import BaseTabWidget


class ThermalView(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        # canvas size
        self.CANVAS_WIDTH = 300
        self.CANVAS_HEIGHT = self.CANVAS_WIDTH

        # low range of the sensor (this will be blue on the screen)
        # this is a default value
        self.MINTEMP = 20.0

        # high range of the sensor (this will be red on the screen)
        # this is a default value
        self.MAXTEMP = 32.0

        # how many color values we can have
        self.COLOR_DEPTH = 1024

        # create available colors
        self.COLOR_PALETTE = [
            c.rgb_255
            for c in list(
                ColorConfig.THERMAL_VIEW_CONTROL_MIN_COLOR.range_to(
                    ColorConfig.THERMAL_VIEW_CONTROL_MAX_COLOR, self.COLOR_DEPTH
                )
            )
        ]

        # last lowest temp from camera
        self.last_lowest_temp = 999.0

        # create canvas
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.canvas = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.canvas)
        self.view.setGeometry(0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT)

        layout.addWidget(self.view)

        # need a bit of padding for the edges of the canvas
        self.setFixedSize(self.CANVAS_WIDTH + 50, self.CANVAS_HEIGHT + 50)

    def set_temp_range(self, mintemp: float, maxtemp: float) -> None:
        """
        Set the temperature range for the viewer.
        """
        self.MINTEMP = mintemp
        self.MAXTEMP = maxtemp

    def set_calibrated_temp_range(self) -> None:
        """
        Calibrate the temperature range based on the lowest observed value.
        """
        self.MINTEMP = self.last_lowest_temp
        self.MAXTEMP = self.last_lowest_temp + 15.0

    def update_canvas(self, pixels: List[int]) -> None:
        """
        Update the thermal view canvas with new data.
        """
        # figure out how many pixels the camera has
        # assumed to be square
        camera_x = int(math.sqrt(len(pixels)))
        camera_y = camera_x
        camera_total = camera_x * camera_y

        # create list of x/y coordinates from the camera
        camera_pixel_coordinats = [
            (math.floor(ix / camera_x), (ix % camera_y)) for ix in range(camera_total)
        ]

        # magic
        grid_x, grid_y = np.mgrid[
            0 : camera_x - 1 : camera_total / 2j,
            0 : camera_y - 1 : camera_total / 2j,
        ]

        # figure out how big the squares on the canvas now are
        # grid_x and grid_y shape are the same
        canvas_squares_x, canvas_squares_y = np.shape(grid_x)
        canvas_square_width = self.CANVAS_WIDTH / canvas_squares_x
        canvas_square_height = self.CANVAS_HEIGHT / canvas_squares_y

        # for all the incoming pixels, constrian them to our temperature range,
        # and give them a value within our color depth
        float_pixels = [
            map_value(p, self.MINTEMP, self.MAXTEMP, 0, self.COLOR_DEPTH - 1)
            for p in pixels
        ]

        # reshape flat list into our grid
        float_pixels_matrix = np.reshape(float_pixels, (camera_x, camera_y))

        # Rotate 90° to orient for mounting correctly
        float_pixels_matrix = np.rot90(float_pixels_matrix, 1)

        # reflatten the list
        rotated_float_pixels = float_pixels_matrix.flatten()

        # create a cubic interpolation of the pixel data
        bicubic = scipy_interpolate_griddata(
            camera_pixel_coordinats,
            rotated_float_pixels,
            (grid_x, grid_y),
            method="cubic",
        )

        # draw on the canvas
        pen = QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
        self.canvas.clear()

        for ix, row in enumerate(bicubic):
            for jx, square in enumerate(row):
                # constrain the value of the square to our color depth
                square_value = int(constrain(square, 0, self.COLOR_DEPTH - 1))
                # create a QColor object for it
                qcolor = QtGui.QColor(*self.COLOR_PALETTE[square_value])
                # create the brush
                brush = QtGui.QBrush(qcolor)
                # add the rectangle
                self.canvas.addRect(
                    canvas_square_width * jx,
                    canvas_square_height * ix,
                    canvas_square_width,
                    canvas_square_height,
                    pen,
                    brush,
                )


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
        color = ColorConfig.THERMAL_VIEW_CONTROL_LASER_ON

        self.send_message("avr/pcm/laser/on")
        self.laser_toggle_label.setText(wrap_text(text, color))

    def laser_off(self) -> None:
        text = "Laser Off"
        color = ColorConfig.THERMAL_VIEW_CONTROL_LASER_OFF

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
