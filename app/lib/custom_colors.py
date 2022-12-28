import darkdetect

from .color import Color
from .enums import ConnectionState

BLACK_COLOR = Color(red=0, green=0, blue=0)
WHITE_COLOR = Color(red=1, green=1, blue=1)
RED_COLOR = Color(red=1)
GREEN_COLOR = Color(green=1)
BLUE_COLOR = Color(blue=1)

MQTT_DEBUGGER_TOPIC_FLASH_COLOR = Color("#DCDCDC")
MQTT_DEBUGGER_DATA_VIEW_BACKGROUND_COLOR = Color("#DCDCDC")

if darkdetect.isDark():
    MQTT_DEBUGGER_TOPIC_FLASH_COLOR = Color("#646464")
    MQTT_DEBUGGER_DATA_VIEW_BACKGROUND_COLOR = Color("#646464")

VMC_TELEMETRY_BATTERY_MIN_COLOR = Color("#870010")
VMC_TELEMETRY_BATTERY_MAX_COLOR = Color("#0b8700")
VMC_TELEMETRY_ARMED_COLOR = Color("#ff0000")  # red
VMC_TELEMETRY_DISARMED_COLOR = Color("#b8860b")  # darkgoldenrod

MOVING_MAP_ALTITUDE_MIN_COLOR = Color("#0e0bbf")
MOVING_MAP_ALTITUDE_MAX_COLOR = Color("#bf0b0e")

VMC_CONTROL_SERVO_OPEN_COLOR = Color("#0000ff")  # blue
VMC_CONTROL_SERVO_CLOSED_COLOR = Color("#d2691e")  # chocolate

THERMAL_VIEW_CONTROL_LASER_ON = Color("#008000")  # green
THERMAL_VIEW_CONTROL_LASER_OFF = Color("#ff0000")  # red
THERMAL_VIEW_CONTROL_MIN_COLOR = Color("#4b0082")  # indigo
THERMAL_VIEW_CONTROL_MAX_COLOR = Color("#ff0000")  # red

AUTONOMY_DROP_ENABLED_COLOR = Color("#008000")  # green
AUTONOMY_DROP_DISABLED_COLOR = Color("#ff0000")  # red
AUTONOMY_AUTONOMOUS_ENABLED_COLOR = Color("#008000")  # green
AUTONOMY_AUTONOMOUS_DISABLED_COLOR = Color("#ff0000")  # red

DISPLAY_LINE_EDIT_BACKGROUND_COLOR = Color("#DCDCDC")

if darkdetect.isDark():
    DISPLAY_LINE_EDIT_BACKGROUND_COLOR = Color("#646464")

CONNECTED_STATE_COLOR = Color("#008000")  # green
CONNECTING_STATE_COLOR = Color("#b8860b")  # darkgoldenrod
DISCONNECTING_STATE_COLOR = Color("#b8860b")  # darkgoldenrod
DISCONNECTED_STATE_COLOR = Color("#ff0000")  # red
FAILURE_STATE_COLOR = Color("#ff0000")  # red

CONNECTION_STATE_COLOR_LOOKUP = {
    ConnectionState.connected: CONNECTED_STATE_COLOR,
    ConnectionState.connecting: CONNECTING_STATE_COLOR,
    ConnectionState.disconnecting: DISCONNECTING_STATE_COLOR,
    ConnectionState.disconnected: DISCONNECTED_STATE_COLOR,
    ConnectionState.failure: FAILURE_STATE_COLOR,
}
