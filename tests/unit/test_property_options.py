# pylint: disable=invalid-name

from pyneo4j_ogm.fields.property_options import WithOptions


def test_WithOptions_returns_subclass_of_provided_type():
    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty)

    assert issubclass(MyPropertyWithOptions, MyProperty)


def test_with_options_sets_range_index_attribute():
    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, range_index=True)

    assert getattr(MyPropertyWithOptions, "_range_index") is True


def test_with_options_sets_text_index_attribute():
    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, text_index=True)

    assert getattr(MyPropertyWithOptions, "_text_index") is True


def test_with_options_sets_point_index_attribute():
    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, point_index=True)

    assert getattr(MyPropertyWithOptions, "_point_index") is True


def test_with_options_sets_unique_attribute():
    class MyProperty:
        pass

    MyPropertyWithOptions = WithOptions(MyProperty, unique=True)

    assert getattr(MyPropertyWithOptions, "_unique") is True
