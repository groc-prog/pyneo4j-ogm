# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import Any, Dict

import pytest
from neo4j.graph import Graph, Node, Relationship
from pydantic import BaseModel

from pyneo4j_ogm.core.relationship import RelationshipModel, ensure_alive
from pyneo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated
from tests.fixtures.db_setup import Sells, WorkedWith


@pytest.fixture()
def use_deflate_inflate_model():
    class NestedModel(BaseModel):
        name: str = "test"

    class DeflateInflateModel(RelationshipModel):
        normal_field: bool = True
        nested_model: NestedModel = NestedModel()
        dict_field: Dict[str, Any] = {"test_str": "test", "test_int": 12}
        list_field: list = ["test", 12, {"test": "test"}]

    setattr(DeflateInflateModel, "_client", None)

    return DeflateInflateModel


@pytest.fixture()
def use_test_relationship():
    setattr(WorkedWith, "_client", None)
    relationship_model = WorkedWith(language="Go")
    relationship_model._element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:6"
    relationship_model._id = 6
    relationship_model._start_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:7"
    relationship_model._start_node_id = 7
    relationship_model._end_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:8"
    relationship_model._end_node_id = 8

    return relationship_model


def test_type_fallback():
    assert Sells._settings.type == "SELLS"


def test_ensure_alive_decorator():
    class EnsureAliveTest:
        _destroyed = False
        _element_id = None
        _id = None
        _start_node_element_id = None
        _end_node_element_id = None
        _start_node_id = None
        _end_node_id = None

        @classmethod
        @ensure_alive
        def test_func(cls):
            return True

    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(EnsureAliveTest, "_id", 1)
    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_start_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17")
    setattr(EnsureAliveTest, "_start_node_id", 3)
    setattr(EnsureAliveTest, "_end_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19")
    setattr(EnsureAliveTest, "_end_node_id", 2)
    setattr(EnsureAliveTest, "_destroyed", True)
    with pytest.raises(InstanceDestroyed):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_destroyed", False)
    assert EnsureAliveTest.test_func()


def test_start_node_element_id(use_test_relationship):
    assert use_test_relationship.start_node_element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:7"


def test_end_node_element_id(use_test_relationship):
    assert use_test_relationship.end_node_element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:8"


def test_start_node_id(use_test_relationship):
    assert use_test_relationship.start_node_id == 7


def test_end_node_id(use_test_relationship):
    assert use_test_relationship.end_node_id == 8


def test_deflate(use_deflate_inflate_model):
    model = use_deflate_inflate_model()
    deflated = model._deflate()

    assert deflated["normal_field"]
    assert deflated["nested_model"] == '{"name": "test"}'
    assert deflated["dict_field"] == '{"test_str": "test", "test_int": 12}'


def test_inflate(use_deflate_inflate_model):
    mock_start_node = Node(
        graph=Graph(),
        element_id="start-element-id",
        id_=2,
        properties={},
    )
    mock_end_node = Node(
        graph=Graph(),
        element_id="end-element-id",
        id_=3,
        properties={},
    )
    mock_relationship = Relationship(
        element_id="4:08f8a347-1856-487c-8705-26d2b4a69bb7:6",
        id_=6,
        graph=Graph(),
        properties={
            "normal_field": True,
            "nested_model": '{"name": "test"}',
            "dict_field": '{"test_str": "test", "test_int": 12}',
            "list_field": ["test", 12, '{"test": "test"}'],
        },
    )
    setattr(mock_relationship, "_start_node", mock_start_node)
    setattr(mock_relationship, "_end_node", mock_end_node)

    inflated = use_deflate_inflate_model._inflate(mock_relationship)

    assert inflated.normal_field
    assert inflated.nested_model.name == "test"
    assert inflated.dict_field["test_str"] == "test"
    assert inflated.dict_field["test_int"] == 12
    assert inflated.list_field[0] == "test"
    assert inflated.list_field[1] == 12
    assert inflated.list_field[2] == {"test": "test"}


def test_iter():
    class Rel(RelationshipModel):
        foo_prop: str = "foo"
        bar_prop: int = 1

    setattr(Rel, "_client", None)

    model = Rel()
    setattr(model, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model, "_id", 18)
    setattr(model, "_start_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17")
    setattr(model, "_start_node_id", 17)
    setattr(model, "_end_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19")
    setattr(model, "_end_node_id", 19)

    for attr_name, attr_value in model:
        assert attr_name in [
            "foo_prop",
            "bar_prop",
            "element_id",
            "id",
            "start_node_element_id",
            "start_node_id",
            "end_node_element_id",
            "end_node_id",
        ]
        assert attr_value in [
            "foo",
            1,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
            18,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17",
            17,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19",
            19,
        ]
