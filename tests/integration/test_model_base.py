# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

import os
from typing import Dict, List, Optional, cast

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection
from tests.fixtures.db_clients import neo4j_session, pyneo4j_client

pytest_plugins = ("pytest_asyncio",)


class TestNode(NodeModel):
    pass


class TestRelationship(RelationshipModel):
    pass


class TestExportModel2(NodeModel):
    pass


class TestExportModelRelationship(RelationshipModel):
    pass


class TestExportModel(NodeModel):
    my_prop: int = 2
    my_list: List[Dict] = [{"list_dict_prop": 1}]

    model: RelationshipProperty[TestExportModel2, TestExportModelRelationship] = RelationshipProperty(
        target_model=TestExportModel2,
        relationship_model=TestExportModelRelationship,
        direction=RelationshipPropertyDirection.OUTGOING,
    )


async def test_str_method(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([TestNode, TestRelationship])

    non_hydrated_node = TestNode()
    hydrated_node = await TestNode().create()

    assert str(non_hydrated_node) == "TestNode(element_id=None, destroyed=False)"
    assert str(hydrated_node) == f"TestNode(element_id={hydrated_node.element_id}, destroyed=False)"

    await hydrated_node.delete()

    assert str(hydrated_node) == f"TestNode(element_id={hydrated_node.element_id}, destroyed=True)"


async def test_eq_method(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([TestNode, TestRelationship])

    node1 = await TestNode().create()
    node2 = await TestNode().create()
    relationship = TestRelationship()

    assert node1 == node1  # pylint: disable=comparison-with-itself
    assert node1 != node2
    assert not node1 == node2
    assert not node1 == relationship


async def test_export_model(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([TestExportModel, TestExportModel2, TestExportModelRelationship])

    node = await TestExportModel().create()

    assert node.export_model() == {
        "element_id": node.element_id,
        "id": node.id,
        "my_prop": 2,
        "my_list": [{"list_dict_prop": 1}],
    }
    assert node.export_model(exclude={"my_prop"}) == {
        "element_id": node.element_id,
        "id": node.id,
        "my_list": [{"list_dict_prop": 1}],
    }
    assert node.export_model(convert_to_camel_case=True) == {
        "elementId": node.element_id,
        "id": node.id,
        "myProp": 2,
        "myList": [{"listDictProp": 1}],
    }


async def test_element_id(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([TestNode])

    node = TestNode()
    assert node.element_id is None

    await node.create()
    assert node.element_id is not None


async def test_id(pyneo4j_client: Pyneo4jClient):
    await pyneo4j_client.register_models([TestNode])

    node = TestNode()
    assert node.id is None

    await node.create()
    assert node.id is not None
