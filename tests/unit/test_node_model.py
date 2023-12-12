# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

from typing import Any, Dict, List, Union

import pytest
from neo4j.graph import Graph, Node
from pydantic import BaseModel

from pyneo4j_ogm.core.node import NodeModel, ensure_alive
from pyneo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated
from tests.fixtures.db_setup import CoffeeShop, Developer


@pytest.fixture()
def use_deflate_inflate_model():
    class NestedModel(BaseModel):
        name: str = "test"

    class DeflateInflateModel(NodeModel):
        normal_field: bool = True
        nested_model: NestedModel = NestedModel()
        dict_field: Dict[str, Any] = {"test_str": "test", "test_int": 12}

    setattr(DeflateInflateModel, "_client", None)

    return DeflateInflateModel


def test_labels_fallback():
    assert CoffeeShop._settings.labels == {"Coffee", "Shop"}


def test_ensure_alive_decorator():
    class EnsureAliveTest:
        _destroyed = False
        _element_id = None
        _id = None

        @classmethod
        @ensure_alive
        def test_func(cls):
            return True

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


def test_deflate(use_deflate_inflate_model):
    model = use_deflate_inflate_model()
    deflated = model._deflate()

    assert deflated["normal_field"]
    assert deflated["nested_model"] == '{"name": "test"}'
    assert deflated["dict_field"] == '{"test_str": "test", "test_int": 12}'


def test_inflate(use_deflate_inflate_model):
    mock_node = Node(
        graph=Graph(),
        element_id="element-id",
        id_=1,
        properties={
            "normal_field": True,
            "nested_model": '{"name": "test"}',
            "dict_field": '{"test_str": "test", "test_int": 12}',
        },
    )

    inflated = use_deflate_inflate_model._inflate(mock_node)

    assert inflated.normal_field
    assert inflated.nested_model.name == "test"
    assert inflated.dict_field["test_str"] == "test"
    assert inflated.dict_field["test_int"] == 12
