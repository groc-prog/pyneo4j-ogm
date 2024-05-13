# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import Any, Dict, List, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node
from pydantic import BaseModel, Field
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel, ensure_alive
from pyneo4j_ogm.exceptions import (
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidFilters,
    ListItemNotEncodable,
    NoResultFound,
    UnexpectedEmptyResult,
    UnregisteredModel,
)
from pyneo4j_ogm.fields.property_options import WithOptions
from pyneo4j_ogm.pydantic_utils import (
    IS_PYDANTIC_V2,
    get_model_dump,
    get_model_dump_json,
    get_schema,
)
from pyneo4j_ogm.queries.types import RelationshipMatchDirection
from tests.fixtures.db_setup import (
    Bestseller,
    Coffee,
    CoffeeShop,
    Consumed,
    Developer,
    WorkedWith,
    client,
    session,
    setup_test_data,
)
from tests.utils.string_utils import assert_string_equality


async def test_update(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    node.tags.append("neighborhood")
    await node.update()
    assert node.tags == ["modern", "trendy", "neighborhood"]
    assert node._db_properties == {"rating": 5, "tags": ["modern", "trendy", "neighborhood"]}

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["tags"] == ["modern", "trendy", "neighborhood"]


async def test_update_no_result(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            node.rating = 2
            await node.update()


async def test_update_one(session: AsyncSession, setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 1})

    assert updated_node is not None
    assert isinstance(updated_node, Developer)
    assert updated_node.age == 30

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Developer.model_settings().labels)})
            WHERE n.uid = $uid
            RETURN n
            """,
        ),
        {"uid": 1},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert query_result[0][0]["age"] == 50


async def test_update_one_raw_result(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"age": 30, "uid": 1, "name": "John"},
        )
        mock_cypher.return_value = (
            [[mock_node]],
            [],
        )

        found_node = await Developer.find_one({"my_prop": "non-existent"})

        assert found_node is not None
        assert isinstance(found_node, Developer)
        assert found_node._id == mock_node.id
        assert found_node._element_id == mock_node.element_id
        assert found_node.age == mock_node["age"]
        assert found_node.uid == mock_node["uid"]
        assert found_node.name == mock_node["name"]


async def test_update_one_return_updated(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 1}, new=True)

    assert updated_node is not None
    assert isinstance(updated_node, Developer)
    assert updated_node.age == 50


async def test_update_one_no_match(setup_test_data):
    updated_node = await Developer.update_one({"age": 50}, {"uid": 99999})

    assert updated_node is None

    with pytest.raises(NoResultFound):
        await Developer.update_one({"age": 50}, {"uid": 99999}, raise_on_empty=True)


async def test_update_one_missing_filters(client: Pyneo4jClient):
    await client.register_models([Developer])

    with pytest.raises(InvalidFilters):
        await Developer.update_one({"my_prop": "updated"}, {})


async def test_update_many(session: AsyncSession, setup_test_data):
    updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, Developer) for node in updated_nodes)
    assert all(node.age != 50 for node in updated_nodes)

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Developer.model_settings().labels)})
            WHERE n.age = $age
            RETURN n
            """,
        ),
        {"age": 50},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_update_many_return_updated(setup_test_data):
    updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}}, new=True)

    assert isinstance(updated_nodes, list)
    assert len(updated_nodes) == 2
    assert all(isinstance(node, Developer) for node in updated_nodes)
    assert all(node.age == 50 for node in updated_nodes)


async def test_update_many_raw_results(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_nodes = [
            Node(
                graph=Graph(),
                element_id="element-id",
                id_=1,
                properties={"age": 30, "uid": 1, "name": "John"},
            ),
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 1
        assert all(isinstance(node, Developer) for node in updated_nodes)


async def test_update_many_no_results(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_nodes = [
            None,
        ]
        mock_cypher.return_value = (
            [mock_nodes],
            [],
        )
        updated_nodes = await Developer.update_many({"age": 50}, {"age": {"$gte": 30}})

        assert isinstance(updated_nodes, list)
        assert len(updated_nodes) == 0


async def test_refresh(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    node.tags.append("neighborhood")

    await node.refresh()
    assert node.tags == ["modern", "trendy"]

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["tags"] == ["modern", "trendy"]


async def test_refresh_no_result(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            await node.refresh()


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
    assert CoffeeShop._settings.labels == {"CoffeeShop"}


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
    node = cast(Developer, await Developer.find_one({"uid": 1}, auto_fetch_nodes=False))

    model_dump = get_model_dump(node)
    json_dump = get_model_dump_json(node)

    parsed_model_dump = Developer(**model_dump)
    parsed_json_dump = Developer(**json.loads(json_dump))

    assert node.coffee.nodes == parsed_model_dump.coffee.nodes
    assert node.coffee.nodes == parsed_json_dump.coffee.nodes


async def test_model_parse_with_auto_fetched_nodes(setup_test_data):
    node = cast(Developer, await Developer.find_one({"uid": 1}, auto_fetch_nodes=True))

    model_dump = get_model_dump(node)
    json_dump = get_model_dump_json(node)

    parsed_model_dump = Developer(**model_dump)
    parsed_json_dump = Developer(**json.loads(json_dump))

    assert node.coffee.nodes == parsed_model_dump.coffee.nodes
    assert node.coffee.nodes == parsed_json_dump.coffee.nodes


async def test_model_parse_with_model_instances(setup_test_data):
    node = cast(Developer, await Developer.find_one({"uid": 1}, auto_fetch_nodes=True))

    model_dump = get_model_dump(node)
    model_dump["coffee"] = node.coffee.nodes

    parsed_model_dump = Developer(**model_dump)

    assert node.coffee.nodes == parsed_model_dump.coffee.nodes


def test_eq():
    class A(NodeModel):
        pass

    class B(NodeModel):
        pass

    setattr(A, "_client", None)
    setattr(B, "_client", None)

    model_a = A()
    model_b_one = B()
    model_b_two = B()
    model_b_three = B()

    setattr(model_a, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model_b_one, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model_b_two, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model_b_three, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19")

    assert model_a != model_b_one
    assert model_b_one == model_b_two
    assert model_b_one != model_b_three


def test_repr():
    class A(NodeModel):
        pass

    setattr(A, "_client", None)

    model_a = A()
    setattr(model_a, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model_a, "_destroyed", False)
    assert repr(model_a) == "A(element_id=4:08f8a347-1856-487c-8705-26d2b4a69bb7:18, destroyed=False)"

    setattr(model_a, "_destroyed", True)
    assert repr(model_a) == "A(element_id=4:08f8a347-1856-487c-8705-26d2b4a69bb7:18, destroyed=True)"

    setattr(model_a, "_element_id", None)
    setattr(model_a, "_destroyed", False)
    assert repr(model_a) == "A(element_id=None, destroyed=False)"


def test_str():
    class A(NodeModel):
        pass

    setattr(A, "_client", None)

    model_a = A()
    setattr(model_a, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model_a, "_destroyed", False)
    assert str(model_a) == "A(element_id=4:08f8a347-1856-487c-8705-26d2b4a69bb7:18, destroyed=False)"

    setattr(model_a, "_destroyed", True)
    assert str(model_a) == "A(element_id=4:08f8a347-1856-487c-8705-26d2b4a69bb7:18, destroyed=True)"

    setattr(model_a, "_element_id", None)
    setattr(model_a, "_destroyed", False)
    assert str(model_a) == "A(element_id=None, destroyed=False)"


def test_iter():
    class A(NodeModel):
        foo_prop: str = "foo"
        bar_prop: int = 1

    setattr(A, "_client", None)

    model = A()
    setattr(model, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model, "_id", 18)

    for attr_name, attr_value in model:
        assert attr_name in ["foo_prop", "bar_prop", "element_id", "id"]
        assert attr_value in ["foo", 1, "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18", 18]


async def test_find_one(setup_test_data):
    found_node = await Developer.find_one({"uid": 1})

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert found_node.uid == 1

    found_node = await Developer.find_one({"age": {"$gte": 30}})

    assert found_node is not None
    assert isinstance(found_node, Developer)


async def test_find_one_no_match(setup_test_data):
    found_node = await Developer.find_one({"my_prop": "non-existent"})

    assert found_node is None

    with pytest.raises(NoResultFound):
        await Developer.find_one({"my_prop": "non-existent"}, raise_on_empty=True)


async def test_find_one_raw_result(client: Pyneo4jClient):
    await client.register_models([Developer])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"age": 30, "uid": 1, "name": "John"},
        )
        mock_cypher.return_value = (
            [[mock_node]],
            [],
        )

        found_node = await Developer.find_one({"my_prop": "non-existent"})

        assert found_node is not None
        assert isinstance(found_node, Developer)
        assert found_node._id == mock_node.id
        assert found_node._element_id == mock_node.element_id
        assert found_node.age == mock_node["age"]
        assert found_node.uid == mock_node["uid"]
        assert found_node.name == mock_node["name"]


async def test_find_one_missing_filter(client: Pyneo4jClient):
    await client.register_models([Developer])

    with pytest.raises(InvalidFilters):
        await Developer.find_one({})


async def test_find_one_projections(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, projections={"dev_name": "name"})

    assert found_node is not None
    assert isinstance(found_node, dict)
    assert found_node["dev_name"] == "John"


async def test_find_one_auto_fetch(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True)

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 2
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 0
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models_as_string(setup_test_data):
    found_node = await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

    assert found_node is not None
    assert isinstance(found_node, Developer)
    assert len(found_node.colleagues.nodes) == 0
    assert len(found_node.coffee.nodes) == 2


async def test_find_one_auto_fetch_models_unregistered_relationship(setup_test_data):
    Developer._client.models.remove(Consumed)

    with pytest.raises(UnregisteredModel):
        await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])


async def test_find_one_auto_fetch_models_unregistered_node(setup_test_data):
    Developer._client.models.remove(Coffee)

    with pytest.raises(UnregisteredModel):
        await Developer.find_one({"uid": 1}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])


async def test_find_many(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 3
    assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_no_match(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": 12})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 0


async def test_find_many_raw_result(client: Pyneo4jClient):
    await client.register_models([Coffee])

    with patch.object(client, "cypher") as mock_cypher:
        mock_node = Node(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"flavor": "Espresso", "sugar": False, "milk": False, "note": '{"roast": "dark"}'},
        )
        mock_cypher.return_value = (
            [[mock_node, None]],
            [],
        )

        found_nodes = await Coffee.find_many({"sugar": False})

        assert isinstance(found_nodes, list)
        assert len(found_nodes) == 1
        assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_projections(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True}, projections={"has_sugar": "sugar"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 3
    assert all(isinstance(node, dict) for node in found_nodes)
    assert all("has_sugar" in cast(Dict[str, Any], node) for node in found_nodes)


async def test_find_many_options(setup_test_data):
    found_nodes = await Coffee.find_many({"sugar": True}, options={"limit": 1})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert all(isinstance(node, Coffee) for node in found_nodes)


async def test_find_many_projections_and_options(setup_test_data):
    found_nodes = await Coffee.find_many(options={"skip": 1}, projections={"has_sugar": "sugar"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 4
    assert all(isinstance(node, dict) for node in found_nodes)


async def test_find_many_projections_and_options_auto_fetch(setup_test_data):
    found_nodes = await Coffee.find_many(options={"skip": 1}, projections={"has_sugar": "sugar"}, auto_fetch_nodes=True)

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 4
    assert all(isinstance(node, dict) for node in found_nodes)


async def test_find_many_auto_fetch(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True)

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 1
    assert len(found_nodes[0].bestseller_for.nodes) == 1


async def test_find_many_auto_fetch_models(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=[Developer])

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 1
    assert len(found_nodes[0].bestseller_for.nodes) == 0


async def test_find_many_auto_fetch_models_as_string(setup_test_data):
    found_nodes = await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=["CoffeeShop"])

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert isinstance(found_nodes[0], Coffee)
    assert len(found_nodes[0].developers.nodes) == 0
    assert len(found_nodes[0].bestseller_for.nodes) == 1


async def test_find_many_auto_fetch_models_unregistered_relationship(setup_test_data):
    Coffee._client.models.remove(Bestseller)

    with pytest.raises(UnregisteredModel):
        await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=[CoffeeShop])


async def test_find_many_auto_fetch_models_unregistered_node(setup_test_data):
    Coffee._client.models.remove(CoffeeShop)

    with pytest.raises(UnregisteredModel):
        await Coffee.find_many({"flavor": "Mocha"}, auto_fetch_nodes=True, auto_fetch_models=["CoffeeShop"])


async def test_find_connected_nodes(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {"$node": {"$labels": list(CoffeeShop.model_settings().labels), "tags": {"$in": ["cozy"]}}},
    )

    assert len(results) == 1
    assert isinstance(results[0], CoffeeShop)
    assert results[0].rating == 5


async def test_find_connected_nodes_filter_relationships(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$relationships": [{"$type": "LIKES_TO_DRINK", "liked": True}],
            "$minHops": 1,
            "$maxHops": 2,
        },
    )

    assert len(results) == 1
    assert isinstance(results[0], CoffeeShop)
    assert results[0].rating == 5


async def test_find_connected_nodes_direction_incoming(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels)},
            "$direction": RelationshipMatchDirection.INCOMING,
            "$minHops": 2,
            "$maxHops": 2,
        },
    )

    assert len(results) == 2


async def test_find_connected_nodes_projections(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$maxHops": 2,
        },
        projections={"coffee_rating": "rating"},
    )

    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert all("coffee_rating" in cast(Dict[str, Any], result) for result in results)


async def test_find_connected_nodes_options(setup_test_data):
    node = await Developer.find_one({"uid": 3})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(CoffeeShop.model_settings().labels)},
            "$maxHops": 2,
        },
        options={"limit": 1},
    )

    assert len(results) == 1
    assert all(isinstance(result, CoffeeShop) for result in results)


async def test_find_connected_nodes_options_and_projections(setup_test_data):
    node = await Developer.find_one({"uid": 1})
    assert node is not None

    results = await cast(Developer, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels)},
        },
        options={"skip": 1},
        projections={"dev_name": "name"},
    )

    assert len(results) == 3
    assert all(isinstance(result, dict) for result in results)


async def test_find_connected_nodes_auto_fetch(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 3


async def test_find_connected_nodes_auto_fetch_models(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
        auto_fetch_models=[Developer],
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 0


async def test_find_connected_nodes_auto_fetch_models_as_string(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    results = await cast(CoffeeShop, node).find_connected_nodes(
        {
            "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
            "$direction": RelationshipMatchDirection.INCOMING,
        },
        auto_fetch_nodes=True,
        auto_fetch_models=["Developer"],
    )

    assert len(results) == 1
    assert isinstance(results[0], Developer)
    assert len(results[0].colleagues.nodes) == 2
    assert len(results[0].coffee.nodes) == 0


async def test_find_connected_nodes_auto_fetch_models_unregistered_node(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    CoffeeShop._client.models.remove(Developer)

    with pytest.raises(UnregisteredModel):
        await cast(CoffeeShop, node).find_connected_nodes(
            {
                "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
                "$direction": RelationshipMatchDirection.INCOMING,
            },
            auto_fetch_nodes=True,
            auto_fetch_models=["Developer"],
        )


async def test_find_connected_nodes_auto_fetch_models_unregistered_relationship(setup_test_data):
    node = await CoffeeShop.find_one({"rating": 5})
    assert node is not None

    CoffeeShop._client.models.remove(WorkedWith)

    with pytest.raises(UnregisteredModel):
        await cast(CoffeeShop, node).find_connected_nodes(
            {
                "$node": {"$labels": list(Developer.model_settings().labels), "uid": 3},
                "$direction": RelationshipMatchDirection.INCOMING,
            },
            auto_fetch_nodes=True,
            auto_fetch_models=[Developer],
        )


async def test_delete(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()
    assert node._destroyed is False

    await node.delete()
    assert node._destroyed

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_delete_no_result(client: Pyneo4jClient):
    await client.register_models([CoffeeShop])

    node = CoffeeShop(rating=5, tags=["modern", "trendy"])
    await node.create()

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            await node.delete()


async def test_delete_one(session: AsyncSession, setup_test_data):
    count = await CoffeeShop.delete_one({"tags": {"$in": ["cozy"]}})
    assert count == 1

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            RETURN DISTINCT n
            """,
        ),
    )
    query_result: list[list[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_delete_one_no_match(session: AsyncSession, setup_test_data):
    results = await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}})
    assert results == 0

    with pytest.raises(NoResultFound):
        await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}}, raise_on_empty=True)

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            RETURN DISTINCT n
            """,
        ),
    )
    query_result: list[list[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 3


async def test_delete_one_invalid_filter(setup_test_data):
    with pytest.raises(InvalidFilters):
        await CoffeeShop.delete_one({})


async def test_delete_one_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await CoffeeShop.delete_one({"tags": {"$in": ["oh-no"]}})


async def test_delete_many(session: AsyncSession, setup_test_data):
    count = await CoffeeShop.delete_many({"tags": {"$in": ["hipster"]}})
    assert count == 2

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            RETURN DISTINCT n
            """,
        ),
    )
    query_result: list[list[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 1


async def test_delete_many_no_match(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    count = await CoffeeShop.delete_many({"tags": {"$in": ["oh-no"]}})
    assert count == 0

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(CoffeeShop.model_settings().labels)})
            RETURN DISTINCT n
            """,
        ),
    )
    query_result: list[list[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 3


async def test_delete_many_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await CoffeeShop.delete_many({"tags": {"$in": ["oh-no"]}})


async def test_create(client: Pyneo4jClient, session: AsyncSession):
    await client.register_models([Coffee])

    node = Coffee(flavor="Mocha", sugar=True, milk=True, note={"roast": "dark"})
    await node.create()

    assert node._element_id is not None
    assert node._id is not None
    assert node._db_properties == {
        "flavor": "Mocha",
        "sugar": True,
        "milk": True,
        "note": {"roast": "dark"},
    }

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH (n:{':'.join(Coffee.model_settings().labels)})
            WHERE elementId(n) = $element_id
            RETURN n
            """,
        ),
        {"element_id": node._element_id},
    )
    query_result: List[List[Node]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert isinstance(node_result, Node)
    assert node_result.element_id == node._element_id
    assert node_result.id == node._id

    assert node_result["flavor"] == "Mocha"
    assert node_result["sugar"]
    assert node_result["milk"]
    assert node_result["note"] == '{"roast": "dark"}'


async def test_create_no_result(client: Pyneo4jClient):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        await client.register_models([Coffee])

        node = Coffee(flavor="Mocha", sugar=True, milk=True, note={"roast": "dark"})

        with pytest.raises(UnexpectedEmptyResult):
            await node.create()


async def test_count(setup_test_data):
    count = await Coffee.count({"milk": True})
    assert count == 3


async def test_count_no_match(setup_test_data):
    count = await Coffee.count({"flavor": "SomethingElse"})
    assert count == 0


async def test_count_no_query_result(client: Pyneo4jClient):
    await client.register_models([Coffee])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]
        with pytest.raises(UnexpectedEmptyResult):
            await Coffee.count({"milk": True})


def test_json_schema():
    setattr(Developer, "_client", None)
    setattr(Coffee, "_client", None)
    setattr(Consumed, "_client", None)

    schema = get_schema(Developer)

    if IS_PYDANTIC_V2:
        assert "coffee" in schema["properties"]
        assert "default" in schema["properties"]["coffee"]
        assert_string_equality(
            schema["properties"]["coffee"]["default"],
            """RelationshipProperty(target_model_name=Coffee, relationship_model=Consumed,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=False)""",
        )
        assert schema["properties"]["coffee"]["type"] == "object"
        assert schema["properties"]["coffee"]["title"] == "Coffee"
        assert schema["properties"]["coffee"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert schema["properties"]["coffee"]["properties"]["target_model_name"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["relationship_model_name"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["direction"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["cardinality"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["allow_multiple"]["type"] == "boolean"

        assert "colleagues" in schema["properties"]
        assert "default" in schema["properties"]["colleagues"]
        assert_string_equality(
            schema["properties"]["colleagues"]["default"],
            """RelationshipProperty(target_model_name=Developer, relationship_model=WorkedWith,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=True)""",
        )
        assert schema["properties"]["colleagues"]["type"] == "object"
        assert schema["properties"]["colleagues"]["title"] == "Colleagues"
        assert schema["properties"]["colleagues"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert schema["properties"]["colleagues"]["properties"]["target_model_name"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["relationship_model_name"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["direction"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["cardinality"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["allow_multiple"]["type"] == "boolean"
    else:
        assert "coffee" in schema["definitions"]["Developer"]["properties"]
        assert "default" in schema["definitions"]["Developer"]["properties"]["coffee"]
        assert_string_equality(
            schema["definitions"]["Developer"]["properties"]["coffee"]["default"],
            """RelationshipProperty(target_model_name=Coffee, relationship_model=Consumed,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=False)""",
        )
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["type"] == "object"
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["title"] == "Coffee"
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["target_model_name"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["relationship_model_name"]["type"]
            == "string"
        )
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["direction"]["type"] == "string"
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["cardinality"]["type"] == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["allow_multiple"]["type"]
            == "boolean"
        )

        assert "colleagues" in schema["definitions"]["Developer"]["properties"]
        assert "default" in schema["definitions"]["Developer"]["properties"]["colleagues"]
        assert_string_equality(
            schema["definitions"]["Developer"]["properties"]["colleagues"]["default"],
            """RelationshipProperty(target_model_name=Developer, relationship_model=WorkedWith,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=True)""",
        )
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["type"] == "object"
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["title"] == "Colleagues"
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["target_model_name"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["relationship_model_name"][
                "type"
            ]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["direction"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["cardinality"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["allow_multiple"]["type"]
            == "boolean"
        )


def test_json_schema_with_index_and_constraint():
    class TestModel(NodeModel):
        uid: WithOptions(str, text_index=True, unique=True, point_index=True, range_index=True) = Field("test-uid")

    setattr(TestModel, "_client", None)

    schema = get_schema(TestModel)

    if IS_PYDANTIC_V2:
        assert "text_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["text_index"]

        assert "point_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["point_index"]

        assert "range_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["range_index"]

        assert "uniqueness_constraint" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["uniqueness_constraint"]
    else:
        assert "text_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["text_index"]

        assert "point_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["point_index"]

        assert "range_index" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["range_index"]

        assert "uniqueness_constraint" in schema["properties"]["uid"]
        assert schema["properties"]["uid"]["uniqueness_constraint"]
