def constrain(value: float, min_value: float, max_value: float) -> float:
    """
    Bound a value within a given range
    """
    return min(max_value, max(min_value, value))


def normalize_value(value: float, min_value: float, max_value: float) -> float:
    """
    Bound and normalize a value within a given range.
    """
    value = constrain(value, min_value, max_value)

    value_range = max_value - min_value
    relative_value = value - min_value
    return relative_value / value_range


def map_value(
    value: float, in_min: float, in_max: float, out_min: float, out_max: float
) -> float:
    """
    Take an input value within a given range and map it to a new range.
    If the input value is outside the input range, then it will be constrained to that
    range.
    """
    input_norm = normalize_value(value, in_min, in_max)
    return out_min + ((out_max - out_min) * input_norm)
