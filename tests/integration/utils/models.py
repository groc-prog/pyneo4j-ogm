"""
Database models for integration tests.
"""
# pylint: disable=missing-class-docstring

from typing import Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.property_options import WithOptions
from neo4j_ogm.fields.relationship_property import (
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)


class PydanticModel(BaseModel):
    field_one: str = "field_one"
    field_two: int = 2
    field_three: bool = True


class TestRelationshipOne(RelationshipModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    valid: bool

    class Settings:
        type = "VALIDITY"
        exclude_from_export = {"id"}


class TestRelationshipTwo(RelationshipModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    valid: bool

    class Settings:
        pre_hooks = {"save": [lambda: print("save pre-hook called")]}
        post_hooks = {"save": lambda: print("save post-hook called")}


class TestNodeOne(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, text_index=True)

    test_node_two: RelationshipProperty["TestNodeTwo", TestRelationshipOne] = RelationshipProperty(
        target_model="TestNodeTwo",
        relationship_model=TestRelationshipOne,
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )
    test_node_three: RelationshipProperty["TestNodeThree", TestRelationshipTwo] = RelationshipProperty(
        target_model="TestNodeThree",
        relationship_model="TestRelationshipTwo",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=True,
    )

    class Settings:
        labels = ("One",)
        exclude_from_export = {"id"}
        auto_fetch_nodes = True


class TestNodeTwo(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    dict_data: Dict[str, Any] = Field(default_factory=dict)
    model_data: PydanticModel = Field(default_factory=PydanticModel)

    test_node_one: RelationshipProperty[TestNodeOne, TestRelationshipOne] = RelationshipProperty(
        target_model=TestNodeOne,
        relationship_model=TestRelationshipOne,
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=False,
    )
    test_node_three: RelationshipProperty["TestNodeThree", TestRelationshipTwo] = RelationshipProperty(
        target_model="TestNodeThree",
        relationship_model="TestRelationshipTwo",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )

    class Settings:
        labels = ("Pytest", "Two")
        pre_hooks = {"save": [lambda: print("save pre-hook called")]}
        post_hooks = {"save": lambda: print("save post-hook called")}


class TestNodeThree(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)

    test_node_one: RelationshipProperty[TestNodeOne, TestRelationshipTwo] = RelationshipProperty(
        target_model=TestNodeOne,
        relationship_model="TestRelationshipOne",
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=True,
    )
    test_node_two: RelationshipProperty[TestNodeTwo, TestRelationshipTwo] = RelationshipProperty(
        target_model="TestNodeTwo",
        relationship_model=TestRelationshipTwo,
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )

    class Settings:
        labels = "Three"
