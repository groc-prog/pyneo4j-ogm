# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import patch

import pytest
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import MissingFilters
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


async def test_find_one(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

    found_node = await SinglePropModel.find_one({"my_prop": "value1"})

    assert found_node is not None
    assert isinstance(found_node, SinglePropModel)
    assert found_node._id == node1._id
    assert found_node._element_id == node1._element_id
    assert found_node.my_prop == "value1"


async def test_find_one_no_match(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    found_node = await SinglePropModel.find_one({"my_prop": "non-existent"})

    assert found_node is None


async def test_find_one_raw_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel(my_prop="value1")
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_node = Node(graph=Graph(), element_id=node.element_id, id_=node.id, properties={"my_prop": "value1"})
        mock_cypher.return_value = (
            [[mock_node]],
            [],
        )

        found_node = await SinglePropModel.find_one({"my_prop": "non-existent"})

        assert found_node is not None
        assert isinstance(found_node, SinglePropModel)
        assert found_node._id == node._id
        assert found_node._element_id == node._element_id
        assert found_node.my_prop == "value1"


async def test_find_one_missing_filter(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    with pytest.raises(MissingFilters):
        await SinglePropModel.find_one({})


async def test_find_one_projections(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

    found_node = await SinglePropModel.find_one({"my_prop": "value1"}, projections={"prop": "my_prop"})

    assert found_node is not None
    assert isinstance(found_node, dict)
    assert found_node["prop"] == "value1"


async def test_find_one_auto_fetch(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models(
        [RelatedModelOne, RelatedModelTwo, RelationshipOne, RelationshipTwo, RelPropModel]
    )

    find_node = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")
    rel_one_node_two = RelatedModelOne(name="rel_one_node_two")
    rel_two_node_one = RelatedModelTwo(name="rel_two_node_one")
    rel_two_node_two = RelatedModelTwo(name="rel_two_node_two")
    rel_two_node_three = RelatedModelTwo(name="rel_two_node_three")

    await find_node.create()
    await rel_one_node_one.create()
    await rel_one_node_two.create()
    await rel_two_node_one.create()
    await rel_two_node_two.create()
    await rel_two_node_three.create()

    await find_node.relations_one.connect(rel_one_node_one)
    await find_node.relations_two.connect(rel_two_node_one)
    await find_node.relations_two.connect(rel_two_node_two)
    await find_node.relations_two.connect(rel_two_node_two)

    found_node = await RelPropModel.find_one({"val": "val"}, auto_fetch_nodes=True)

    assert found_node is not None
    assert isinstance(found_node, RelPropModel)
    assert len(found_node.relations_one.nodes) == 1
    assert len(found_node.relations_two.nodes) == 2


async def test_find_one_auto_fetch_models(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models(
        [RelatedModelOne, RelatedModelTwo, RelationshipOne, RelationshipTwo, RelPropModel]
    )

    find_node = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")
    rel_two_node_one = RelatedModelTwo(name="rel_two_node_one")

    await find_node.create()
    await rel_one_node_one.create()
    await rel_two_node_one.create()

    await find_node.relations_one.connect(rel_one_node_one)
    await find_node.relations_two.connect(rel_two_node_one)

    found_node = await RelPropModel.find_one({"val": "val"}, auto_fetch_nodes=True, auto_fetch_models=[RelatedModelOne])

    assert found_node is not None
    assert isinstance(found_node, RelPropModel)
    assert len(found_node.relations_one.nodes) == 1
    assert len(found_node.relations_two.nodes) == 0


async def test_find_one_auto_fetch_models_as_string(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models(
        [RelatedModelOne, RelatedModelTwo, RelationshipOne, RelationshipTwo, RelPropModel]
    )

    find_node = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")
    rel_two_node_one = RelatedModelTwo(name="rel_two_node_one")

    await find_node.create()
    await rel_one_node_one.create()
    await rel_two_node_one.create()

    await find_node.relations_one.connect(rel_one_node_one)
    await find_node.relations_two.connect(rel_two_node_one)

    found_node = await RelPropModel.find_one(
        {"val": "val"}, auto_fetch_nodes=True, auto_fetch_models=["RelatedModelOne"]
    )

    assert found_node is not None
    assert isinstance(found_node, RelPropModel)
    assert len(found_node.relations_one.nodes) == 1
    assert len(found_node.relations_two.nodes) == 0


async def test_find_one_auto_fetch_models_unregistered_relationship(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([RelatedModelOne, RelatedModelTwo, RelationshipOne, RelPropModel])

    find_node = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")

    await find_node.create()
    await rel_one_node_one.create()

    await find_node.relations_one.connect(rel_one_node_one)

    found_node = await RelPropModel.find_one(
        {"val": "val"}, auto_fetch_nodes=True, auto_fetch_models=["RelatedModelTwo"]
    )

    assert found_node is not None
    assert isinstance(found_node, RelPropModel)
    assert len(found_node.relations_one.nodes) == 0
    assert len(found_node.relations_two.nodes) == 0


async def test_find_one_auto_fetch_models_unregistered_node(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([RelatedModelOne, RelationshipTwo, RelationshipOne, RelPropModel])

    find_node = RelPropModel()
    rel_one_node_one = RelatedModelOne(name="rel_one_node_one")

    await find_node.create()
    await rel_one_node_one.create()

    await find_node.relations_one.connect(rel_one_node_one)

    found_node = await RelPropModel.find_one(
        {"val": "val"}, auto_fetch_nodes=True, auto_fetch_models=["RelatedModelTwo"]
    )

    assert found_node is not None
    assert isinstance(found_node, RelPropModel)
    assert len(found_node.relations_one.nodes) == 0
    assert len(found_node.relations_two.nodes) == 0
