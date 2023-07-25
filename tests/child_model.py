from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty
from neo4j_ogm.queries.types import RelationshipPropertyDirection


class HasChild(RelationshipModel):
    born: datetime = Field(default_factory=datetime.now)


class Child(NodeModel):
    id: WithOptions(property_type=UUID, unique=True) = Field(default_factory=uuid4)
    name: str

    parents = RelationshipProperty(
        target_model="Adult", relationship_model=HasChild, direction=RelationshipPropertyDirection.INCOMING
    )
    toys = RelationshipProperty(
        target_model="Toy", relationship_model="OwnsToy", direction=RelationshipPropertyDirection.OUTGOING
    )

    class Settings:
        labels = "Child"
