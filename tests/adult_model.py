from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty
from neo4j_ogm.queries.types import RelationshipDirection


class Married(RelationshipModel):
    wedding_day: datetime = Field(default_factory=datetime.now)

    class Settings:
        type = "IS_TOGETHER_WITH"


class Friends(RelationshipModel):
    since: datetime = Field(default_factory=datetime.now)
    best_friends: bool

    class Settings:
        type = "IS_FRIENDS_WITH"


class Adult(NodeModel):
    id: WithOptions(property_type=UUID, unique=True) = Field(default_factory=uuid4)
    name: str
    age: int

    friends = RelationshipProperty(
        target_model="Adult", relationship_model=Friends, direction=RelationshipDirection.BOTH, allow_multiple=True
    )
    partner = RelationshipProperty(
        target_model="Adult", relationship_model=Married, direction=RelationshipDirection.BOTH
    )
    children = RelationshipProperty(
        target_model="Child", relationship_model="HasChild", direction=RelationshipDirection.OUTGOING
    )

    class Settings:
        labels = ["Person", "Adult"]
