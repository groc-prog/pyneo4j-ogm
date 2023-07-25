from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty
from neo4j_ogm.queries.types import RelationshipDirection


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
