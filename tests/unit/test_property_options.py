"""
Unit tests for neo4j_ogm.fields.property_options module.
"""

# pylint: disable=invalid-name

from neo4j_ogm.fields.property_options import WithOptions


def test_WithOptions_returns_subclass_of_provided_type():
    """
    Test that WithOptions returns a subclass of the provided type.
    """

    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty)

    assert issubclass(MyPropertyWithOptions, MyProperty)


def test_with_options_sets_range_index_attribute():
    """
    Test that WithOptions sets the range_index attribute to True.
    """

    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, range_index=True)

    assert getattr(MyPropertyWithOptions, "_range_index") is True


def test_with_options_sets_text_index_attribute():
    """
    Test that WithOptions sets the text_index attribute to True.
    """

    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, text_index=True)

    assert getattr(MyPropertyWithOptions, "_text_index") is True


def test_with_options_sets_point_index_attribute():
    """
    Test that WithOptions sets the point_index attribute to True.
    """

    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, point_index=True)

    assert getattr(MyPropertyWithOptions, "_point_index") is True


def test_with_options_sets_unique_attribute():
    """
    Test that WithOptions sets the unique attribute to True.
    """

    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, unique=True)

    assert getattr(MyPropertyWithOptions, "_unique") is True
