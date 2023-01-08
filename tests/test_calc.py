import pytest

import app.lib.calc


@pytest.mark.parametrize(
    "in_value, min_value, max_value, out_value",
    [(3, 0, 5, 3), (10, 0, 5, 5), (-10, 0, 5, 0)],
)
def test_constrain(
    in_value: float, min_value: float, max_value: float, out_value: float
) -> None:
    assert app.lib.calc.constrain(in_value, min_value, max_value) == out_value


@pytest.mark.parametrize(
    "in_value, min_value, max_value, out_value",
    [(3, 0, 5, 0.6), (10, 0, 5, 1), (-10, 0, 5, 0)],
)
def test_normalize_value(
    in_value: float, min_value: float, max_value: float, out_value: float
) -> None:
    assert app.lib.calc.normalize_value(in_value, min_value, max_value) == out_value


@pytest.mark.parametrize(
    "in_value, in_min, in_max, out_min, out_max, out_value",
    [(3, 0, 5, 0, 10, 6), (10, 0, 5, 0, 10, 10)],
)
def test_map_value(
    in_value: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float,
    out_value: float,
) -> None:
    assert (
        app.lib.calc.map_value(in_value, in_min, in_max, out_min, out_max) == out_value
    )
