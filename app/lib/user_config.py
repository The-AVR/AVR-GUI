import contextlib
import json
import os
from typing import Any, Optional

import typeguard

from app.lib.directory_config import ROOT_DIR


class _UserConfig:
    config_file = os.path.join(ROOT_DIR, "settings.json")

    def __init__(self):
        self.__file_cache: Optional[dict] = None

    def __read(self) -> dict:
        # if the file does not exist, return an empty dict
        if not os.path.isfile(self.config_file):
            return {}

        # if we have a cached version, return it
        if self.__file_cache is not None:
            return self.__file_cache

        try:
            with open(self.config_file, "r") as fp:
                data = json.load(fp)

            # if we got valid JSON, but it's not a dict, still trigger error
            if not isinstance(data, dict):
                raise ValueError

            self.__file_cache = data
            return data

        except (json.JSONDecodeError, ValueError):
            # on invalid files, just delete it
            os.remove(self.config_file)
            return {}

    def __write(self, data: dict) -> None:
        self.__file_cache = data

        with open(self.config_file, "w") as fp:
            json.dump(data, fp, indent=4)

    def __get(self, key: str, type_hint: Any, default: Any) -> Any:
        # read the file
        data = self.__read()

        # if the requested key is in the config, return it
        if key in data:
            value = data[key]

            with contextlib.suppress(typeguard.TypeCheckError):
                # make sure the value is of the correct type
                # otherwise, return the default
                typeguard.check_type(value, type_hint)
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
    def force_light_mode(self) -> bool:
        """
        Allow the use to force the application to light mode.
        This only works on Windows.
        """
        return self.__get("force_light_mode", bool, False)

    @force_light_mode.setter
    def force_light_mode(self, value: bool) -> None:
        return self.__set("force_light_mode", value)

    @property
    def joystick_inverted(self) -> bool:
        return self.__get("joystick_inverted", bool, False)

    @joystick_inverted.setter
    def joystick_inverted(self, value: bool) -> None:
        return self.__set("joystick_inverted", value)


UserConfig = _UserConfig()
