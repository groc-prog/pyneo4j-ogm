"""
This module contains custom datatypes which can be used to declare additional options for a property
like indexing or a unique constraint.
"""
from typing import Any


def WithPropertyDefaults(property_type: Any, indexed: bool = False, unique: bool = False):
    """
    Returns a subclass of `property_type` which includes extra attributes like `_indexed` and `_unique`
    which can be used to define indexes and constraints on the property. Does not have an effect when called
    with just the `property_type` argument.

    Args:
        property_type (Any): The property type to return for the model field
        indexed (bool, optional): Whether the property should be indexed or not. Defaults to False.
        unique (bool, optional): Whether a `UNIQUENESS` constraint should be created for the property.
            Defaults to False.

    Returns:
        A subclass of the provided type with extra attributes
    """

    class PropertyWithOptions(property_type):
        """
        Subclass of provided type with extra arguments
        """

        _indexed: bool = indexed
        _unique: bool = unique

        def __new__(cls, *args, **kwargs):
            return property_type.__new__(property_type, *args, **kwargs)

    return PropertyWithOptions
