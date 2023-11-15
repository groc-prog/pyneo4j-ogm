# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

import logging
import os
from typing import Any, Dict, List, cast

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection
from pyneo4j_ogm.queries.types import RelationshipMatchDirection
from tests.fixtures.db_clients import pyneo4j_client

pytest_plugins = ("pytest_asyncio",)


class RelatedOne(RelationshipModel):
    counter: int = 1

    class Settings:
        type = "REL_ONE"


class RelatedTwo(RelationshipModel):
    kind = "a"

    class Settings:
        type = "REL_TWO"


class FarRelatedOne(NodeModel):
    val: str = "val"

    related: RelationshipProperty["FarRelatedTwo", RelatedOne] = RelationshipProperty(
        target_model="FarRelatedTwo",
        relationship_model=RelatedOne,
        direction=RelationshipPropertyDirection.OUTGOING,
    )

    class Settings:
        labels = {"One"}


class FarRelatedTwo(NodeModel):
    val: str = "val"

    related_in: RelationshipProperty[FarRelatedOne, RelatedOne] = RelationshipProperty(
        target_model=FarRelatedOne,
        relationship_model=RelatedOne,
        direction=RelationshipPropertyDirection.INCOMING,
    )

    related_out: RelationshipProperty["FarRelatedThree", RelatedTwo] = RelationshipProperty(
        target_model="FarRelatedThree",
        relationship_model=RelatedTwo,
        direction=RelationshipPropertyDirection.OUTGOING,
    )

    class Settings:
        labels = {"Two"}


class FarRelatedThree(NodeModel):
    val: str = "val"

    related_in: RelationshipProperty[FarRelatedTwo, RelatedTwo] = RelationshipProperty(
        target_model=FarRelatedTwo,
        relationship_model=RelatedTwo,
        direction=RelationshipPropertyDirection.INCOMING,
    )

    class Settings:
        labels = {"Three"}


@pytest.fixture(autouse=True)
async def setup_graph(pyneo4j_client: Pyneo4jClient):
    os.environ["PYNEO4J_OGM_LOG_LEVEL"] = str(logging.DEBUG)

    await pyneo4j_client.register_models([FarRelatedOne, FarRelatedTwo, FarRelatedThree, RelatedOne, RelatedTwo])

    start1 = FarRelatedOne(val="start_one")
    start2 = FarRelatedOne(val="start_two")
    middle1 = FarRelatedTwo(val="middleman_one")
    middle2 = FarRelatedTwo(val="middleman_two")
    end1 = FarRelatedThree(val="far_end_one")
    end2 = FarRelatedThree(val="far_end_two")
    end3 = FarRelatedThree(val="far_end_three")

    await start1.create()
    await start2.create()
    await middle1.create()
    await middle2.create()
    await end1.create()
    await end2.create()
    await end3.create()

    await start1.related.connect(middle1)
    await start1.related.connect(middle2)
    await middle1.related_in.connect(start1)
    await middle2.related_in.connect(start1, {"counter": 5})
    await middle2.related_in.connect(start2)
    await middle1.related_out.connect(end1, {"kind": "b"})
    await middle1.related_out.connect(end2)
    await middle2.related_out.connect(end1)
    await middle2.related_out.connect(end3, {"kind": "b"})

    return start1, start2, middle1, middle2, end1, end2, end3


async def test_find_connected_nodes(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]

    results = await start.find_connected_nodes(
        {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
    )

    assert len(results) == 2
    assert all(isinstance(node, FarRelatedThree) for node in results)


async def test_find_connected_nodes_filter_relationships(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]
    matched: FarRelatedOne = setup_graph[6]

    results = await start.find_connected_nodes(
        {
            "$node": {"$labels": ["Three"]},
            "$relationships": [{"$type": "REL_ONE", "counter": {"$gt": 3}}, {"$type": "REL_TWO", "kind": "b"}],
        },
    )

    assert len(results) == 1
    assert isinstance(results[0], FarRelatedThree)
    assert cast(FarRelatedThree, results[0])._element_id == matched._element_id
    assert cast(FarRelatedThree, results[0])._id == matched._id


async def test_find_connected_nodes_direction_incoming(pyneo4j_client: Pyneo4jClient, setup_graph):
    start_outgoing: FarRelatedOne = setup_graph[0]
    start_incoming: FarRelatedOne = setup_graph[5]
    start_both: FarRelatedOne = setup_graph[1]

    results = await start_outgoing.find_connected_nodes(
        {
            "$node": {"$labels": ["Three"]},
            "$relationships": [{"$type": "REL_ONE", "counter": {"$gt": 3}}, {"$type": "REL_TWO", "kind": "b"}],
            "$direction": RelationshipMatchDirection.INCOMING,
        },
    )

    assert len(results) == 0

    results = await start_incoming.find_connected_nodes(
        {"$node": {"$labels": ["One"]}, "$direction": RelationshipMatchDirection.INCOMING},
    )

    assert len(results) == 1
    assert isinstance(results[0], FarRelatedOne)
    assert cast(FarRelatedOne, results[0])._element_id == start_outgoing._element_id
    assert cast(FarRelatedOne, results[0])._id == start_outgoing._id

    results = await start_both.find_connected_nodes(
        {"$node": {"$labels": ["One"]}, "$direction": RelationshipMatchDirection.BOTH},
    )

    assert len(results) == 1
    assert isinstance(results[0], FarRelatedOne)
    assert cast(FarRelatedOne, results[0])._element_id == start_outgoing._element_id
    assert cast(FarRelatedOne, results[0])._id == start_outgoing._id


async def test_find_connected_nodes_projections(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]

    results = await start.find_connected_nodes(
        {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
        projections={"node_val": "val", "node_id": "$id"},
    )

    assert len(results) == 2
    assert all(isinstance(node, dict) for node in results)
    assert all("node_val" in cast(Dict[str, Any], node) for node in results)
    assert all("node_id" in cast(Dict[str, Any], node) for node in results)


async def test_find_connected_nodes_options(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]

    results = await start.find_connected_nodes(
        {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
        options={"limit": 1},
    )

    assert len(results) == 1


async def test_find_connected_nodes_auto_fetch(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]

    results = await start.find_connected_nodes(
        {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
        auto_fetch_nodes=True,
    )

    assert len(results) == 2
    assert all(isinstance(node, FarRelatedThree) for node in results)
    assert all(len(node.related_in.nodes) > 0 for node in cast(List[FarRelatedThree], results))


async def test_find_connected_nodes_auto_fetch_models(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]

    results = await start.find_connected_nodes(
        {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
        auto_fetch_nodes=True,
        auto_fetch_models=[FarRelatedOne],
    )

    assert len(results) == 2
    assert all(isinstance(node, FarRelatedThree) for node in results)
    assert all(len(node.related_in.nodes) == 0 for node in cast(List[FarRelatedThree], results))


async def test_find_connected_nodes_auto_fetch_cancelled(pyneo4j_client: Pyneo4jClient, setup_graph):
    start: FarRelatedOne = setup_graph[0]
    pyneo4j_client.models = {model for model in pyneo4j_client.models if model != FarRelatedThree}

    with pytest.raises(UnregisteredModel):
        results = await start.find_connected_nodes(
            {"$node": {"$labels": ["Three"], "val": {"$or": [{"$eq": "far_end_one"}, {"$eq": "far_end_two"}]}}},
            auto_fetch_nodes=True,
        )

        assert len(results) == 2
        assert all(isinstance(node, FarRelatedThree) for node in results)
        assert all(len(node.related_in.nodes) == 0 for node in cast(List[FarRelatedThree], results))
