# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

import pytest

from pyneo4j_ogm.core.node import ensure_alive
from pyneo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated
from tests.fixtures.db_setup import CoffeeShop, Developer


def test_labels_fallback():
    assert CoffeeShop.__settings__.labels == {"Coffee", "Shop"}


def test_relationship_property_auto_exclude():
    assert Developer.__settings__.exclude_from_export == {"colleagues", "coffee"}


def test_ensure_alive_decorator():
    class EnsureAliveTest:
        _destroyed = False
        _element_id = None
        _id = None

        @classmethod
        @ensure_alive
        def test_func(cls):
            return True

    setattr(EnsureAliveTest, "_client", None)
    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_id", 1)
    setattr(EnsureAliveTest, "_destroyed", True)
    with pytest.raises(InstanceDestroyed):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_destroyed", False)
    assert EnsureAliveTest.test_func()
