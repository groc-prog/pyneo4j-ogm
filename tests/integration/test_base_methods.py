# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring
# pyright: reportGeneralTypeIssues=false

import os
from typing import Optional, cast

import pytest

from pyneo4j_ogm.core.client import Neo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import ModelImportFailure
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

    model: RelationshipProperty[TestExportModel2, TestExportModelRelationship] = RelationshipProperty(
        target_model=TestExportModel2,
        relationship_model=TestExportModelRelationship,
        direction=RelationshipPropertyDirection.OUTGOING,
    )


class TestImportModel(NodeModel):
    my_prop: Optional[int]


async def test_str_method(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestNode, TestRelationship])

    non_hydrated_node = TestNode()
    hydrated_node = await TestNode().create()

    assert str(non_hydrated_node) == "TestNode(element_id=None, destroyed=False)"
    assert str(hydrated_node) == f"TestNode(element_id={hydrated_node.element_id}, destroyed=False)"

    await hydrated_node.delete()

    assert str(hydrated_node) == f"TestNode(element_id={hydrated_node.element_id}, destroyed=True)"


async def test_eq_method(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestNode, TestRelationship])

    node1 = await TestNode().create()
    node2 = await TestNode().create()
    relationship = TestRelationship()

    assert node1 == node1  # pylint: disable=comparison-with-itself
    assert node1 != node2
    assert not node1 == node2
    assert not node1 == relationship


async def test_export_model(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestExportModel, TestExportModel2, TestExportModelRelationship])

    node = await TestExportModel().create()

    assert node.export_model() == {"element_id": node.element_id, "id": node.id, "my_prop": 2}
    assert node.export_model(exclude={"my_prop"}) == {"element_id": node.element_id, "id": node.id}
    assert node.export_model(convert_to_camel_case=True) == {"elementId": node.element_id, "id": node.id, "myProp": 2}


async def test_import_model(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestImportModel])

    model_dict = {
        "element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "my_prop": 2,
    }

    model = TestImportModel.import_model(model_dict)

    assert model.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model.id == 13
    assert model.my_prop == 2

    model_dict_converted = {
        "elementId": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "myProp": 2,
    }

    model_converted = TestImportModel.import_model(model_dict_converted, from_camel_case=True)

    assert model_converted.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model_converted.id == 13
    assert model_converted.my_prop == 2

    with pytest.raises(ModelImportFailure):
        TestImportModel.import_model({"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"})
        TestImportModel.import_model({"id": 13})
        TestImportModel.import_model(
            {"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18", "id": 13}, from_camel_case=True
        )


async def test_pre_hooks(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestNode])

    TestNode.register_pre_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", [lambda: None, lambda: None])
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", [lambda: None, "invalid"])
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", lambda: None)
    TestNode.register_pre_hooks("test_hook", lambda: None, overwrite=True)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", lambda: None)
    TestNode.register_pre_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []


async def test_post_hooks(pyneo4j_client: Neo4jClient):
    await pyneo4j_client.register_models([TestNode])

    TestNode.register_post_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", [lambda: None, lambda: None])
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", [lambda: None, "invalid"])
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", lambda: None)
    TestNode.register_post_hooks("test_hook", lambda: None, overwrite=True)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", lambda: None)
    TestNode.register_post_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []
