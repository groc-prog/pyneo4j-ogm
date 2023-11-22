"""
Model property wrapper for defining indexes and constraints on properties.
"""
from typing import Type, TypeVar

T = TypeVar("T")


def WithOptions(
    property_type: Type[T],
    range_index: bool = False,
    text_index: bool = False,
    point_index: bool = False,
    unique: bool = False,
) -> Type[T]:
    """
    Returns a subclass of `property_type` and defines indexes and constraints on the property.

    Args:
        property_type (Type[T]): The property type to return for the model field.
        range_index (bool, optional): Whether the property should have a `RANGE` index or not. Defaults to `False`.
        text_index (bool, optional): Whether the property should have a `TEXT` index or not. Defaults to `False`.
        point_index (bool, optional): Whether the property should have a `POINT` index or not. Defaults to `False`.
        unique (bool, optional): Whether a `UNIQUENESS` constraint should be created for the property.
            Defaults to `False`.

    Returns:
        Type[T]: A subclass of the provided type with extra attributes.
    """

    class PropertyWithOptions(property_type):
        """
        Subclass of provided type with extra arguments.
        """

        _range_index: bool = range_index
        _text_index: bool = text_index
        _point_index: bool = point_index
        _unique: bool = unique

    return PropertyWithOptions
