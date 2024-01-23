# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import Any, Dict

import pytest
from neo4j.graph import Graph, Node
from pydantic import BaseModel

from pyneo4j_ogm.core.node import NodeModel, ensure_alive
from pyneo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated
from pyneo4j_ogm.pydantic_utils import get_model_dump, get_model_dump_json
from tests.fixtures.db_setup import (
    CoffeeShop,
    Developer,
    client,
    session,
    setup_test_data,
)


@pytest.fixture()
def use_deflate_inflate_model():
    class NestedModel(BaseModel):
        name: str = "test"

    class DeflateInflateModel(NodeModel):
        normal_field: bool = True
        nested_model: NestedModel = NestedModel()
        dict_field: Dict[str, Any] = {"test_str": "test", "test_int": 12}
        list_field: list = ["test", 12, {"test": "test"}]

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
            "list_field": ["test", 12, '{"test": "test"}'],
        },
    )

    inflated = use_deflate_inflate_model._inflate(mock_node)

    assert inflated.normal_field
    assert inflated.nested_model.name == "test"
    assert inflated.dict_field["test_str"] == "test"
    assert inflated.dict_field["test_int"] == 12
    assert inflated.list_field[0] == "test"
    assert inflated.list_field[1] == 12
    assert inflated.list_field[2] == {"test": "test"}


async def test_model_parse(setup_test_data):
    node: Developer = await Developer.find_one({"uid": 1}, auto_fetch_nodes=False)

    model_dump = get_model_dump(node)
    json_dump = get_model_dump_json(node)

    parsed_model_dump = Developer(**model_dump)
    parsed_json_dump = Developer(**json.loads(json_dump))

    assert node.coffee.nodes == parsed_model_dump.coffee.nodes
    assert node.coffee.nodes == parsed_json_dump.coffee.nodes


async def test_model_parse_with_auto_fetched_nodes(setup_test_data):
    node: Developer = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True)

    model_dump = get_model_dump(node)
    json_dump = get_model_dump_json(node)

    parsed_model_dump = Developer(**model_dump)
    parsed_json_dump = Developer(**json.loads(json_dump))

    assert node.coffee.nodes == parsed_model_dump.coffee.nodes
    assert node.coffee.nodes == parsed_json_dump.coffee.nodes
