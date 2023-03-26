import contextlib
import json
import os
from typing import Any, Literal

import typeguard

from app.lib.directory_config import ROOT_DIR


class _UserConfig:
    config_file = os.path.join(ROOT_DIR, "settings.json")

    def __read(self) -> dict:
        if not os.path.isfile(self.config_file):
            return {}

        try:
            with open(self.config_file, "r") as fp:
                data = json.load(fp)

            # if we got valid JSON, but it's not a dict, still trigger error
            if not isinstance(data, dict):
                raise ValueError

            return data

        except (json.JSONDecodeError, ValueError):
            # on invalid files, just delete it
            os.remove(self.config_file)
            return {}

    def __write(self, data: dict) -> None:
        with open(self.config_file, "w") as fp:
            json.dump(data, fp, indent=4)

    def __get(self, key: str, type_hint: Any, default: Any) -> Any:
        # read the file
        data = self.__read()

        # if the requested key is in the config, return it
        if key in data:
            value = data[key]

            with contextlib.suppress(TypeError):
                # make sure the value is of the correct type
                # otherwise, return the default
                typeguard.check_type(key, value, type_hint)
                return value

        # if we have a set default value that is not None, write it out
        if default is not None:
            self.__set(key, default)

        return default

    def __set(self, key: str, value: Any) -> None:
        data = self.__read()
        data[key] = value
        self.__write(data)

    @property
    def mqtt_host(self) -> str:
        return self.__get("mqtt_host", str, "")

    @mqtt_host.setter
    def mqtt_host(self, value: str) -> None:
        return self.__set("mqtt_host", value)

    @property
    def mqtt_port(self) -> int:
        return self.__get("mqtt_port", int, 18830)

    @mqtt_port.setter
    def mqtt_port(self, value: int) -> None:
        return self.__set("mqtt_port", value)

    @property
    def serial_port(self) -> str:
        return self.__get("serial_port", str, "")

    @serial_port.setter
    def serial_port(self, value: str) -> None:
        return self.__set("serial_port", value)

    @property
    def serial_baud_rate(self) -> int:
        return self.__get("serial_baud_rate", int, 115200)

    @serial_baud_rate.setter
    def serial_baud_rate(self, value: int) -> None:
        return self.__set("serial_baud_rate", value)

    @property
    def log_file_directory(self) -> str:
        return self.__get("log_file_directory", str, os.path.join(ROOT_DIR, "logs"))

    @log_file_directory.setter
    def log_file_directory(self, value: str) -> None:
        return self.__set("log_file_directory", value)

    @property
    def force_color_mode(self) -> Literal["dark", "light", None]:
        return self.__get("force_color_mode", Literal["dark", "light", None], None)

    @force_color_mode.setter
    def force_color_mode(self, value: Literal["dark", "light", None]) -> None:
        return self.__set("force_color_mode", value)

    @property
    def joystick_inverted(self) -> bool:
        return self.__get("joystick_inverted", bool, False)

    @joystick_inverted.setter
    def joystick_inverted(self, value: bool) -> None:
        return self.__set("joystick_inverted", value)

    @property
    def gamepad_guid(self) -> str:
        return self.__get("gamepad_guid", str, "")

    @gamepad_guid.setter
    def gamepad_guid(self, value: str) -> None:
        return self.__set("gamepad_guid", value)

    # for my T-Flight HOTAS X, x is 0, y is 1
    @property
    def gamepad_x_axis(self) -> int:
        return self.__get("gamepad_x_axis", int, 0)

    @gamepad_x_axis.setter
    def gamepad_x_axis(self, value: int) -> None:
        return self.__set("gamepad_x_axis", value)

    @property
    def gamepad_x_axis_inverted(self) -> bool:
        return self.__get("gamepad_x_axis_inverted", int, 0)

    @gamepad_x_axis_inverted.setter
    def gamepad_x_axis_inverted(self, value: bool) -> None:
        return self.__set("gamepad_x_axis_inverted", value)

    @property
    def gamepad_y_axis(self) -> int:
        return self.__get("gamepad_y_axis", int, 1)

    @gamepad_y_axis.setter
    def gamepad_y_axis(self, value: int) -> None:
        return self.__set("gamepad_y_axis", value)

    @property
    def gamepad_y_axis_inverted(self) -> bool:
        return self.__get("gamepad_y_axis_inverted", int, 0)

    @gamepad_y_axis_inverted.setter
    def gamepad_y_axis_inverted(self, value: bool) -> None:
        return self.__set("gamepad_y_axis_inverted", value)


UserConfig = _UserConfig()
