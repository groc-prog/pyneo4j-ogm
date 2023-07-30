from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty, RelationshipPropertyDirection


class OwnsToy(RelationshipModel):
    class Settings:
        type = "OWNS"


class Toy(NodeModel):
    id: WithOptions(property_type=UUID, unique=True) = Field(default_factory=uuid4)
    make: str
    produced_at: float = Field(default=lambda: datetime.timestamp(datetime.now()))

    owner = RelationshipProperty(
        target_model="Child", relationship_model=OwnsToy, direction=RelationshipPropertyDirection.INCOMING
    )
