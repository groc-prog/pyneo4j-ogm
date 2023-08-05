import asyncio
from typing import Any, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.property_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty, RelationshipPropertyDirection


class Role(BaseModel):
    name: str = "Emmies"
    year: int = 2020


class WorkedTogether(RelationshipModel):
    had_fun: bool = True
    fun_level: int = 5


class Friends(RelationshipModel):
    class Settings:
        type = "FRIENDS_WITH"


class Actor(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, text_index=True)
    age: int
    latest_role: Dict[str, Any] = dict(Role(name="No Emmies", year=2020))
    all_roles: List[Role] = [Role()]

    class Settings:
        exclude_from_export = {"latest_role"}
        labels = "Actor"


class Actress(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, text_index=True)
    age: int
    latest_role: Dict[str, Any] = dict(Role(name="No Emmies", year=2020))
    all_roles: List[Role] = [Role()]

    colleagues: RelationshipProperty["Actor", WorkedTogether] = RelationshipProperty(
        target_model=Actor, relationship_model="WorkedTogether", direction=RelationshipPropertyDirection.OUTGOING
    )
    friends: RelationshipProperty["Actress", Friends] = RelationshipProperty(
        "Actress", Friends, RelationshipPropertyDirection.INCOMING, True
    )

    class Settings:
        exclude_from_export = {"latest_role"}
        labels = {"Actress", "Female"}
