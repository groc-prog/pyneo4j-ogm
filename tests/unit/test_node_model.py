# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

import pytest

from pyneo4j_ogm.core.node import NodeModel, ensure_alive
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection


class LabelsTest(NodeModel):
    pass

    class Settings:
        labels = set()


class RelationshipPropertyNode(NodeModel):
    pass


class RelationshipPropertyRelationship(RelationshipModel):
    pass


class RelationshipPropertyTest(NodeModel):
    my_prop: int = 1

    rel_prop_one: RelationshipProperty[
        RelationshipPropertyNode, RelationshipPropertyRelationship
    ] = RelationshipProperty(
        target_model=RelationshipPropertyNode,
        relationship_model=RelationshipPropertyRelationship,
        direction=RelationshipPropertyDirection.OUTGOING,
    )
    rel_prop_two: RelationshipProperty[
        RelationshipPropertyNode, RelationshipPropertyRelationship
    ] = RelationshipProperty(
        target_model=RelationshipPropertyNode,
        relationship_model=RelationshipPropertyRelationship,
        direction=RelationshipPropertyDirection.OUTGOING,
    )


setattr(LabelsTest, "_client", None)
setattr(RelationshipPropertyNode, "_client", None)
setattr(RelationshipPropertyRelationship, "_client", None)
setattr(RelationshipPropertyTest, "_client", None)


def test_converting_labels():
    assert LabelsTest.__settings__.labels == {"Labels", "Test"}


def test_relationship_property_auto_exclude():
    assert RelationshipPropertyTest.__settings__.exclude_from_export == {"rel_prop_one", "rel_prop_two"}


def test_ensure_alive_decorator():
    class EnsureAliveTest:
        _destroyed = False
        _element_id = None
        _id = None

        @classmethod
        @ensure_alive
        def test_func(cls):
            return True

    setattr(EnsureAliveTest, "_client", None)
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
