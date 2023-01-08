import pytest

import app.lib.color


def test_color_class() -> None:
    c = app.lib.color.Color("red")
    assert c.rgb_255 == (255, 0, 0)


@pytest.mark.parametrize(
    "min_color, max_color, value, min_value, max_value, out_color",
    [
        (
            app.lib.color.Color("red"),
            app.lib.color.Color("blue"),
            5,
            0,
            10,
            app.lib.color.Color(rgb=(0.5, 0, 0.5)),
        ),
        (
            app.lib.color.Color("black"),
            app.lib.color.Color("white"),
            1,
            0,
            10,
            app.lib.color.Color(rgb=(0.1, 0.1, 0.1)),
        ),
    ],
)
def test_smear_color(
    min_color: app.lib.color.Color,
    max_color: app.lib.color.Color,
    value: float,
    min_value: float,
    max_value: float,
    out_color: app.lib.color.Color,
) -> None:
    assert (
        app.lib.color.smear_color(min_color, max_color, value, min_value, max_value)
        == out_color
    )
