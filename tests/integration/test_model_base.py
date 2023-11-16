# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import Dict, List

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection
from tests.fixtures.db_setup import client

pytest_plugins = ("pytest_asyncio",)


class NodeTestModel(NodeModel):
    pass


class RelationshipTestModel(RelationshipModel):
    pass


class ModelExportTest2(NodeModel):
    pass


class RelationshipExportTest(RelationshipModel):
    pass


class ModelExportTest(NodeModel):
    my_prop: int = 2
    my_list: List[Dict] = [{"list_dict_prop": 1}]

    model: RelationshipProperty[ModelExportTest2, RelationshipExportTest] = RelationshipProperty(
        target_model=ModelExportTest2,
        relationship_model=RelationshipExportTest,
        direction=RelationshipPropertyDirection.OUTGOING,
    )


async def test_str_method(client: Pyneo4jClient):
    await client.register_models([NodeTestModel, RelationshipTestModel])

    non_hydrated_node = NodeTestModel()
    hydrated_node = await NodeTestModel().create()

    assert str(non_hydrated_node) == "NodeTestModel(element_id=None, destroyed=False)"
    assert str(hydrated_node) == f"NodeTestModel(element_id={hydrated_node.element_id}, destroyed=False)"

    await hydrated_node.delete()

    assert str(hydrated_node) == f"NodeTestModel(element_id={hydrated_node.element_id}, destroyed=True)"


async def test_eq_method(client: Pyneo4jClient):
    await client.register_models([NodeTestModel, RelationshipTestModel])

    node1 = await NodeTestModel().create()
    node2 = await NodeTestModel().create()
    relationship = RelationshipTestModel()

    assert node1 == node1  # pylint: disable=comparison-with-itself
    assert node1 != node2
    assert not node1 == node2
    assert not node1 == relationship


async def test_export_model(client: Pyneo4jClient):
    await client.register_models([ModelExportTest, ModelExportTest2, RelationshipExportTest])

    node = await ModelExportTest().create()

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


async def test_element_id(client: Pyneo4jClient):
    await client.register_models([NodeTestModel])

    node = NodeTestModel()
    assert node.element_id is None

    await node.create()
    assert node.element_id is not None


async def test_id(client: Pyneo4jClient):
    await client.register_models([NodeTestModel])

    node = NodeTestModel()
    assert node.id is None

    await node.create()
    assert node.id is not None
