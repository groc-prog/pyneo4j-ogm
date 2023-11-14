# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import patch

from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from tests.fixtures.db_clients import pyneo4j_client
from tests.fixtures.models import (
    RelatedModelOne,
    RelatedModelTwo,
    RelationshipOne,
    RelationshipTwo,
    RelPropModel,
    SinglePropModel,
)

pytest_plugins = ("pytest_asyncio",)


async def test_find_many(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    found_nodes = await SinglePropModel.find_many({"my_prop": {"$contains": "value"}})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 2
    assert all(isinstance(node, SinglePropModel) for node in found_nodes)


async def test_find_many_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    found_nodes = await SinglePropModel.find_many({"my_prop": "non-existent"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 0


async def test_find_many_raw_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel(my_prop="value1")
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_nodes = Node(graph=Graph(), element_id=node.element_id, id_=node.id, properties={"my_prop": "value1"})
        mock_cypher.return_value = (
            [[mock_nodes, None]],
            [],
        )

        found_nodes = await SinglePropModel.find_many({"my_prop": "non-existent"})

        assert isinstance(found_nodes, list)
        assert len(found_nodes) == 1
        assert all(isinstance(node, SinglePropModel) for node in found_nodes)


async def test_find_many_projections(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    found_nodes = await SinglePropModel.find_many({"my_prop": {"$contains": "value"}}, projections={"prop": "my_prop"})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 2
    assert all(isinstance(node, dict) for node in found_nodes)
    assert all("prop" in node for node in found_nodes)


async def test_find_many_options(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    node3 = SinglePropModel(my_prop="other")
    await node1.create()
    await node2.create()
    await node3.create()

    found_nodes = await SinglePropModel.find_many({"my_prop": {"$contains": "value"}}, options={"limit": 1})

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 1
    assert all(isinstance(node, SinglePropModel) for node in found_nodes)


async def test_find_many_auto_fetch(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models(
        [RelatedModelOne, RelatedModelTwo, RelationshipOne, RelationshipTwo, RelPropModel]
    )

    find_node_one = RelPropModel()
    find_node_two = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")
    rel_one_node_two = RelatedModelOne(name="rel_one_node_two")
    rel_two_node_one = RelatedModelTwo(name="rel_two_node_one")
    rel_two_node_two = RelatedModelTwo(name="rel_two_node_two")
    rel_two_node_three = RelatedModelTwo(name="rel_two_node_three")

    await find_node_one.create()
    await find_node_two.create()
    await rel_one_node_one.create()
    await rel_one_node_two.create()
    await rel_two_node_one.create()
    await rel_two_node_two.create()
    await rel_two_node_three.create()

    await find_node_one.relations_one.connect(rel_one_node_one)
    await find_node_one.relations_two.connect(rel_two_node_one)
    await find_node_one.relations_two.connect(rel_two_node_two)
    await find_node_one.relations_two.connect(rel_two_node_two)

    await find_node_two.relations_one.connect(rel_one_node_two)
    await find_node_two.relations_two.connect(rel_two_node_three)
    await find_node_two.relations_two.connect(rel_two_node_three)

    found_nodes = await RelPropModel.find_many({"val": "val"}, auto_fetch_nodes=True)

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 2

    for node in found_nodes:
        assert isinstance(node, RelPropModel)

        if node._element_id == find_node_one._element_id:
            assert len(node.relations_one.nodes) == 1
            assert len(node.relations_two.nodes) == 2
        elif node._element_id == find_node_two._element_id:
            assert len(node.relations_one.nodes) == 1
            assert len(node.relations_two.nodes) == 1


async def test_find_many_auto_fetch_models(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models(
        [RelatedModelOne, RelatedModelTwo, RelationshipOne, RelationshipTwo, RelPropModel]
    )

    find_node_one = RelPropModel()
    find_node_two = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")
    rel_one_node_two = RelatedModelOne(name="rel_one_node_two")
    rel_two_node_one = RelatedModelTwo(name="rel_two_node_one")
    rel_two_node_two = RelatedModelTwo(name="rel_two_node_two")
    rel_two_node_three = RelatedModelTwo(name="rel_two_node_three")

    await find_node_one.create()
    await find_node_two.create()
    await rel_one_node_one.create()
    await rel_one_node_two.create()
    await rel_two_node_one.create()
    await rel_two_node_two.create()
    await rel_two_node_three.create()

    await find_node_one.relations_one.connect(rel_one_node_one)
    await find_node_one.relations_two.connect(rel_two_node_one)
    await find_node_one.relations_two.connect(rel_two_node_two)
    await find_node_one.relations_two.connect(rel_two_node_two)

    await find_node_two.relations_one.connect(rel_one_node_two)
    await find_node_two.relations_two.connect(rel_two_node_three)
    await find_node_two.relations_two.connect(rel_two_node_three)

    found_nodes = await RelPropModel.find_many(
        {"val": "val"}, auto_fetch_nodes=True, auto_fetch_models=[RelatedModelOne]
    )

    assert isinstance(found_nodes, list)
    assert len(found_nodes) == 2

    for node in found_nodes:
        assert isinstance(node, RelPropModel)

        if node._element_id == find_node_one._element_id:
            assert len(node.relations_one.nodes) == 1
            assert len(node.relations_two.nodes) == 0
        elif node._element_id == find_node_two._element_id:
            assert len(node.relations_one.nodes) == 1
            assert len(node.relations_two.nodes) == 0
