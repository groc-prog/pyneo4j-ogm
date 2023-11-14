# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import MissingFilters, NoResultsFound
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client

pytest_plugins = ("pytest_asyncio",)


class MultiPropModel(NodeModel):
    str_prop: str
    int_prop: int
    bool_prop: bool
    dict_prop: Dict[str, Any]

    class Settings:
        labels = {"Test"}


class SinglePropModel(NodeModel):
    my_prop: str = "default"

    class Settings:
        labels = {"Test"}


class NoPropModel(NodeModel):
    class Settings:
        labels = {"Test"}


class RelatedModelOne(NodeModel):
    name: str

    class Settings:
        labels = {"RelatedOne"}


class RelationshipOne(RelationshipModel):
    class Settings:
        type = "REL_ONE"


class RelatedModelTwo(NodeModel):
    name: str

    class Settings:
        labels = {"RelatedTwo"}


class RelationshipTwo(RelationshipModel):
    class Settings:
        type = "REL_TWO"


class RelPropModel(NodeModel):
    val: str = "val"

    relations_one: RelationshipProperty[RelatedModelOne, RelationshipOne] = RelationshipProperty(
        target_model=RelatedModelOne,
        relationship_model=RelationshipOne,
        direction=RelationshipPropertyDirection.OUTGOING,
    )
    relations_two: RelationshipProperty[RelatedModelTwo, RelationshipTwo] = RelationshipProperty(
        target_model=RelatedModelTwo,
        relationship_model=RelationshipTwo,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=True,
    )


async def test_create(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    dict_prop = {"key1": "value1", "key2": 2, "key3": [1, 2, 3]}

    await pyneo4j_client.register_models([MultiPropModel])

    node = MultiPropModel(str_prop="string", int_prop=1, bool_prop=True, dict_prop=dict_prop)
    await node.create()

    assert node._element_id is not None
    assert node._id is not None
    assert node._db_properties == {
        "str_prop": "string",
        "int_prop": 1,
        "bool_prop": True,
        "dict_prop": dict_prop,
    }

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert isinstance(node_result, Node)
    assert node_result.element_id == node._element_id
    assert node_result.id == node._id

    assert node_result["str_prop"] == "string"
    assert node_result["int_prop"] == 1
    assert node_result["bool_prop"]
    assert node_result["dict_prop"] == json.dumps(dict_prop)


async def test_create_no_result(pyneo4j_client: Pyneo4jClient):
    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        await pyneo4j_client.register_models([MultiPropModel])

        node = MultiPropModel(str_prop="string", int_prop=1, bool_prop=True, dict_prop={"key": "value"})

        with pytest.raises(NoResultsFound):
            await node.create()


async def test_update(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()
    assert node.my_prop == "default"

    node.my_prop = "new value"
    await node.update()
    assert node.my_prop == "new value"
    assert node._db_properties == {"my_prop": "new value"}

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["my_prop"] == "new value"


async def test_update_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()
    assert node.my_prop == "default"

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            node.my_prop = "new value"
            await node.update()


async def test_delete(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([NoPropModel])

    node = NoPropModel()
    await node.create()
    assert node._destroyed is False

    await node.delete()
    assert node._destroyed

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 0


async def test_delete_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([NoPropModel])

    node = NoPropModel()
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            await node.delete()


async def test_refresh(pyneo4j_client: Pyneo4jClient, neo4j_session: AsyncSession):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()

    node.my_prop = "new value"

    await node.refresh()
    assert node.my_prop == "default"

    results = await neo4j_session.run("MATCH (n:Test) RETURN n")
    query_result: List[List[Node]] = await results.values()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    node_result = query_result[0][0]
    assert node_result["my_prop"] == "default"


async def test_refresh_no_result(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([SinglePropModel])

    node = SinglePropModel()
    await node.create()

    with patch.object(pyneo4j_client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(NoResultsFound):
            await node.refresh()


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

    node1 = SinglePropModel(my_prop="value1")
    node2 = SinglePropModel(my_prop="value2")
    await node1.create()
    await node2.create()

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
