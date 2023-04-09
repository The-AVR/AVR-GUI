from PySide6 import QtGui

from app.lib.color import Color
from app.lib.enums import ConnectionState
from app.lib.user_config import UserConfig

BLACK_COLOR = Color("#000000")
WHITE_COLOR = Color("#ffffff")
RED_COLOR = Color("#ff0000")
GREEN_COLOR = Color("#00ff00")
BLUE_COLOR = Color("#0000ff")

DARK_GOLDEN_ROD_COLOR = Color("#b8860b")


class _ColorConfig:
    @property
    def is_dark(self) -> bool:
        """
        Return whether the system is in dark mode.
        This must be done after the QApplication is created and style applied
        (after import).
        """
        if UserConfig.force_color_mode == "light":
            # user has forced light mode
            return False
        elif UserConfig.force_color_mode == "dark":
            # user has forced dark mode
            return True
        else:
            # try our best
            default_palette = QtGui.QPalette()
            return (
                default_palette.windowText().color().lightness()
                > default_palette.window().color().lightness()
            )

    @property
    def MQTT_DEBUGGER_TOPIC_FLASH_COLOR(self) -> Color:
        if self.is_dark:
            return Color("#646464")
        return Color("#DCDCDC")

    @property
    def MQTT_DEBUGGER_DATA_VIEW_BACKGROUND_COLOR(self) -> Color:
        if self.is_dark:
            return Color("#646464")
        return Color("#DCDCDC")

    @property
    def VMC_TELEMETRY_BATTERY_MIN_COLOR(self) -> Color:
        return Color("#870010")

    @property
    def VMC_TELEMETRY_BATTERY_MAX_COLOR(self) -> Color:
        return Color("#0b8700")

    @property
    def VMC_TELEMETRY_ARMED_COLOR(self) -> Color:
        return RED_COLOR

    @property
    def VMC_TELEMETRY_DISARMED_COLOR(self) -> Color:
        return DARK_GOLDEN_ROD_COLOR

    @property
    def MOVING_MAP_ALTITUDE_MIN_COLOR(self) -> Color:
        return Color("#0e0bbf")

    @property
    def MOVING_MAP_ALTITUDE_MAX_COLOR(self) -> Color:
        return Color("#bf0b0e")

    @property
    def MOVING_MAP_GROUND_COLOR(self) -> Color:
        return Color("#785a08")

    @property
    def VMC_CONTROL_SERVO_OPEN_COLOR(self) -> Color:
        return BLUE_COLOR

    @property
    def VMC_CONTROL_SERVO_CLOSED_COLOR(self) -> Color:
        return Color("#d2691e")  # chocolate

    @property
    def THERMAL_VIEW_CONTROL_LASER_ON(self) -> Color:
        return GREEN_COLOR

    @property
    def THERMAL_VIEW_CONTROL_LASER_OFF(self) -> Color:
        return RED_COLOR

    @property
    def THERMAL_VIEW_CONTROL_MIN_COLOR(self) -> Color:
        return Color("#4b0082")  # indigo

    @property
    def THERMAL_VIEW_CONTROL_MAX_COLOR(self) -> Color:
        return RED_COLOR

    @property
    def AUTONOMY_DROP_ENABLED_COLOR(self) -> Color:
        return GREEN_COLOR

    @property
    def AUTONOMY_DROP_DISABLED_COLOR(self) -> Color:
        return RED_COLOR

    @property
    def AUTONOMY_AUTONOMOUS_ENABLED_COLOR(self) -> Color:
        return GREEN_COLOR

    @property
    def AUTONOMY_AUTONOMOUS_DISABLED_COLOR(self) -> Color:
        return RED_COLOR

    @property
    def DISPLAY_LINE_EDIT_BACKGROUND_COLOR(self) -> Color:
        if self.is_dark:
            return Color("#646464")
        return Color("#DCDCDC")

    @property
    def CONNECTED_STATE_COLOR(self) -> Color:
        return GREEN_COLOR

    @property
    def CONNECTING_STATE_COLOR(self) -> Color:
        return DARK_GOLDEN_ROD_COLOR

    @property
    def DISCONNECTING_STATE_COLOR(self) -> Color:
        return DARK_GOLDEN_ROD_COLOR

    @property
    def DISCONNECTED_STATE_COLOR(self) -> Color:
        return RED_COLOR

    @property
    def FAILURE_STATE_COLOR(self) -> Color:
        return RED_COLOR


ColorConfig = _ColorConfig()

CONNECTION_STATE_COLOR_LOOKUP = {
    ConnectionState.connected: ColorConfig.CONNECTED_STATE_COLOR,
    ConnectionState.connecting: ColorConfig.CONNECTING_STATE_COLOR,
    ConnectionState.disconnecting: ColorConfig.DISCONNECTING_STATE_COLOR,
    ConnectionState.disconnected: ColorConfig.DISCONNECTED_STATE_COLOR,
    ConnectionState.failure: ColorConfig.FAILURE_STATE_COLOR,
}
