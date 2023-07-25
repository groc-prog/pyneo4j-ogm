# pylint: disable=missing-class-docstring missing-module-docstring
import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty
from neo4j_ogm.queries.types import RelationshipDirection


class HasChild(RelationshipModel):
    born: datetime = Field(default_factory=datetime.now)


class AdultToAdult(RelationshipModel):
    since: datetime = Field(default_factory=datetime.now)
    best_friends: bool = False

    class Settings:
        type = "HAS_CHILD"


class Adult(NodeModel):
    id: WithOptions(property_type=UUID, unique=True) = Field(default_factory=uuid4)
    name: str
    age: int

    friends = RelationshipProperty(
        target_model="Adult", relationship_model=AdultToAdult, direction=RelationshipDirection.BOTH
    )
    children = RelationshipProperty(
        target_model="Child", relationship_model="HasChild", direction=RelationshipDirection.OUTGOING
    )

    class Settings:
        labels = ["Person", "Adult"]


class Child(NodeModel):
    id: WithOptions(property_type=UUID, unique=True) = Field(default_factory=uuid4)
    name: str

    parents = RelationshipProperty(
        target_model=Adult, relationship_model=HasChild, direction=RelationshipDirection.INCOMING
    )
    toys = RelationshipProperty(
        target_model="Toy", relationship_model="OwnsToy", direction=RelationshipDirection.OUTGOING
    )

    class Settings:
        labels = "Child"


async def main():
    client = Neo4jClient()
    client.connect(uri="neo4j://localhost:7687", auth=("neo4j", "password"))

    await client.register_models([Adult, AdultToAdult, Child, HasChild])
    await client.register_models_directory("models")

    print("DONE")


asyncio.run(main())
