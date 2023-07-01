from __future__ import annotations

from typing import Any, Generator

import colour

from app.lib.calc import normalize_value


class Color(colour.Color):
    """
    Small tweak to the normal `colour` library, to include a property to get the
    `Color` object's RGB values in a 0-255 range.
    """

    @property
    def rgb_255(self) -> tuple[int, int, int]:
        return tuple(round(i * 255) for i in self.rgb)

    def range_to(self, value: Any, steps: int) -> Generator[Color, Any, None]:
        for hsl in colour.color_scale(self._hsl, Color(value).hsl, steps - 1):
            yield Color(hsl=hsl)


def smear_color(
    min_color: Color,
    max_color: Color,
    value: float,
    min_value: float,
    max_value: float,
) -> Color:
    """
    Smear a color between two colors based on a value.
    """
    norm_value = normalize_value(value, min_value, max_value)
    diff = [f - e for f, e in zip(max_color.rgb, min_color.rgb)]
    smear = [d * norm_value for d in diff]
    return Color(rgb=[e + s for e, s in zip(min_color.rgb, smear)])


def wrap_text(text: str, color: Color) -> str:
    """
    Take a color, and wrap the text with a `span` element for that color.
    """
    return f"<span style='color:{color.hex};'>{text}</span>"
