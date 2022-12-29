import json
from typing import Any, Generator

import pytest

from app.lib.user_config import UserConfig


def assert_config_file_contents(expected_file_contents: dict) -> None:
    """
    Check that the config file contains the expected keys and values.
    """
    with open(UserConfig.config_file, "r") as fp:
        config_file_contents = json.load(fp)

    for key, value in expected_file_contents.items():
        assert key in config_file_contents
        assert config_file_contents[key] == value


def set_config_file_contents(file_contents: Any) -> None:
    """
    Overwrite the contents of the config file.
    """
    with open(UserConfig.config_file, "w") as fp:
        json.dump(file_contents, fp)


@pytest.fixture
def config_file() -> Generator:
    """
    Pytest fixture to wipe config file contents before and after each test.
    """
    set_config_file_contents({})
    yield
    set_config_file_contents({})


def test_corrupt_config_file_contents(config_file: None) -> None:
    """
    Check that the config file is reset when corrupted.
    """
    # corrupt file
    set_config_file_contents(True)
    # ask for something from file
    assert isinstance(UserConfig.joystick_inverted, bool)


def test_set_value(config_file: None) -> None:
    """
    Check that value set is saved
    """
    # set a value
    UserConfig.joystick_inverted = True
    assert_config_file_contents({"joystick_inverted": True})


def test_get_value(config_file: None) -> None:
    """
    Check that saved options are retrieved.
    """
    # set a value
    UserConfig.joystick_inverted = True
    # make sure value was saved
    assert_config_file_contents({"joystick_inverted": True})
    # make sure value gets loaded
    assert UserConfig.joystick_inverted is True


def test_get_value_default(config_file: None) -> None:
    """
    Check that missing option has default saved.
    """
    # get a value
    UserConfig.joystick_inverted
    # make sure a default was saved
    assert_config_file_contents({"joystick_inverted": False})


def test_get_value_type_check(config_file: None) -> None:
    """
    Check that corrupted values are caught.
    """
    # set bad data
    set_config_file_contents({"joystick_inverted": "abcde"})
    # get a value
    assert UserConfig.joystick_inverted is False
    # make sure value was corrected
    assert_config_file_contents({"joystick_inverted": False})
