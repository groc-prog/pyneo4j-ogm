from typing import Any, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.node_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty


class Role(BaseModel):
    name: str = "Emmies"
    year: int = 2020


class Actress(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, text_index=True)
    age: int
    latest_role: Dict[str, Any] = dict(Role())
    all_roles: List[Role] = [Role()]

    class Settings:
        labels = ["Actress", "Female"]
