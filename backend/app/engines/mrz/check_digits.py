def char_to_value(char: str) -> int:
    """ICAO 9303 Character to Value Mapping."""
    if char == '<':
        return 0
    if char.isdigit():
        return int(char)
    if 'A' <= char.upper() <= 'Z':
        return ord(char.upper()) - ord('A') + 10
    return 0


def calculate_mrz_check_digit(data_str: str) -> str:
    """
    Computes ICAO 9303 Check Digit using 7-3-1 weight sequence.
    Formula: Sum(val * weight) % 10
    """
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(data_str):
        weight = weights[i % 3]
        total += char_to_value(char) * weight
    return str(total % 10)


def verify_check_digit(data_str: str, expected_digit: str) -> bool:
    """Verifies if the computed check digit matches the expected digit."""
    if not expected_digit:
        return False
    computed = calculate_mrz_check_digit(data_str)
    return computed == expected_digit
