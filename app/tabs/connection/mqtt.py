from typing import Any

import paho.mqtt.client as paho_mqtt
from bell.avr.mqtt.client import MQTTClient as BaseMQTTClient
from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets

from app.lib.color import wrap_text
from app.lib.color_config import CONNECTION_STATE_COLOR_LOOKUP
from app.lib.enums import ConnectionState
from app.lib.user_config import UserConfig
from app.lib.widgets import IntLineEdit


class MQTTClient(BaseMQTTClient, QtCore.QObject):
    # This class MUST inherit from QObject in order for the signals to work

    # This class works with a QSigna based architecture, as the MQTT client
    # runs in a seperate thread. The callbacks from the MQTT client run in the same
    # thread as the client and thus those cannot update the GUI, as only the
    # thread that started the GUI is allowed to update it. Thus, set up the
    # MQTT client in a seperate class with signals that are emitted and connected to
    # so the data gets passed back to the GUI thread.

    # Once the Signal objects are created, they transform into SignalInstance objects
    connection_state: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore
    on_message_signal: QtCore.SignalInstance = QtCore.Signal(str, bytes)  # type: ignore

    def __init__(self) -> None:
        super().__init__()
        super(BaseMQTTClient, self).__init__()

        self.subscribe_to_all_topics = True
        self.enable_verbose_logging = True

    def on_message(
        self, client: paho_mqtt.Client, userdata: Any, msg: paho_mqtt.MQTTMessage
    ) -> None:
        """
        Callback for every MQTT message
        """
        self.on_message_signal.emit(msg.topic, msg.payload)

    def on_disconnect(self, *args: Any) -> None:
        super().on_disconnect(*args)
        self.connection_state.emit(ConnectionState.disconnected)

    def connect2(self, host: str, port: int) -> None:
        # connect_ is already a method that we shouldn't overwrite

        # do nothing on empty sring
        if not host:
            return

        self.connection_state.emit(ConnectionState.connecting)

        try:
            self.run_non_blocking(host, port)

            # save settings
            UserConfig.mqtt_host = host
            UserConfig.mqtt_port = port

            # emit success
            logger.success("Connected to MQTT server")
            self.connection_state.emit(ConnectionState.connected)

        except Exception:
            logger.exception("Connection failed to MQTT broker")
            self.connection_state.emit(ConnectionState.failure)

    def stop(self) -> None:
        self.connection_state.emit(ConnectionState.disconnecting)
        super().stop()
        self.connection_state.emit(ConnectionState.disconnected)


class MQTTConnectionWidget(QtWidgets.QWidget):
    connection_state: QtCore.SignalInstance = QtCore.Signal(object)  # type: ignore

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.mqtt_client = MQTTClient()
        self.mqtt_client.connection_state.connect(self.set_connected_state)

    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        # lay out the host label and line edit
        host_layout = QtWidgets.QFormLayout()

        self.hostname_line_edit = QtWidgets.QLineEdit()
        host_layout.addRow(QtWidgets.QLabel("Host:"), self.hostname_line_edit)

        self.port_line_edit = IntLineEdit()
        host_layout.addRow(QtWidgets.QLabel("Port:"), self.port_line_edit)

        layout.addLayout(host_layout)

        # lay out the bottom connection state and buttons
        bottom_layout = QtWidgets.QHBoxLayout()
        self.state_label = QtWidgets.QLabel()
        bottom_layout.addWidget(self.state_label)

        button_layout = QtWidgets.QHBoxLayout()
        self.connect_button = QtWidgets.QPushButton("Connect")
        button_layout.addWidget(self.connect_button)

        self.disconnect_button = QtWidgets.QPushButton("Disconnect")
        button_layout.addWidget(self.disconnect_button)

        bottom_layout.addLayout(button_layout)

        layout.addLayout(bottom_layout)

        # set starting state
        self.set_connected_state(ConnectionState.disconnected)

        self.hostname_line_edit.setText(UserConfig.mqtt_host)
        self.port_line_edit.setText(str(UserConfig.mqtt_port))

        # set up connections
        self.hostname_line_edit.returnPressed.connect(self.connect_button.click)  # type: ignore
        self.connect_button.clicked.connect(  # type: ignore
            lambda: self.mqtt_client.connect2(
                self.hostname_line_edit.text(), int(self.port_line_edit.text())
            )
        )
        self.disconnect_button.clicked.connect(self.mqtt_client.stop)  # type: ignore

    def set_connected_state(self, connection_state: ConnectionState) -> None:
        """
        Set the connected state of the MQTT connection widget elements.
        """
        connected = connection_state == ConnectionState.connected
        disconnected = connection_state in [
            ConnectionState.failure,
            ConnectionState.disconnected,
        ]

        self.state_label.setText(
            f"State: {wrap_text(connection_state.name.title(), CONNECTION_STATE_COLOR_LOOKUP[connection_state])}"
        )

        self.disconnect_button.setEnabled(connected)
        self.connect_button.setDisabled(connected)

        self.hostname_line_edit.setReadOnly(not disconnected)
        self.port_line_edit.setReadOnly(not disconnected)

        self.connection_state.emit(connection_state)
        QtGui.QGuiApplication.processEvents()
