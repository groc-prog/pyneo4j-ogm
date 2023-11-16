"""
Utility functions for asserting string tests.
"""
from typing import Optional


def assert_string_equality(actual: Optional[str], expected: str) -> None:
    """
    Assert that two strings are equal after removing all whitespace.

    Args:
        actual (str | None): The actual string.
        expected (str): The expected string.

    Raises:
        AssertionError: If the actual string is None or the strings are not equal.
    """
    if actual is None:
        raise AssertionError("The actual string is None.")

    normalized_actual = "".join(actual.split())
    normalized_expected = "".join(expected.split())

    assert normalized_actual == normalized_expected
