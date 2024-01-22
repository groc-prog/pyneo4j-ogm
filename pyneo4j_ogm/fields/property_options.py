"""
Model property wrapper for defining indexes and constraints on properties.
"""
from typing import Any, Type

from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


def WithOptions(
    property_type: Type,
    range_index: bool = False,
    text_index: bool = False,
    point_index: bool = False,
    unique: bool = False,
):
    """
    Returns a subclass of `property_type` and defines indexes and constraints on the property.

    Args:
        property_type (Type): The property type to return for the model field.
        range_index (bool, optional): Whether the property should have a `RANGE` index or not. Defaults to `False`.
        text_index (bool, optional): Whether the property should have a `TEXT` index or not. Defaults to `False`.
        point_index (bool, optional): Whether the property should have a `POINT` index or not. Defaults to `False`.
        unique (bool, optional): Whether a `UNIQUENESS` constraint should be created for the property.
            Defaults to `False`.

    Returns:
        A subclass of the provided type with extra attributes.
    """

    class PropertyWithOptions(property_type):
        """
        Subclass of provided type with extra arguments.
        """

        _range_index: bool = range_index
        _text_index: bool = text_index
        _point_index: bool = point_index
        _unique: bool = unique

        def __new__(cls, *args, **kwargs):
            return property_type.__new__(property_type, *args, **kwargs)

        if IS_PYDANTIC_V2:

            @classmethod
            def __get_pydantic_core_schema__(cls, _: Any, handler: GetCoreSchemaHandler) -> CoreSchema:  # type: ignore
                return handler(property_type)  # type: ignore

    return PropertyWithOptions
