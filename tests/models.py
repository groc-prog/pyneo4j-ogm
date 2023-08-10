# pylint: disable-all

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.property_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty, RelationshipPropertyDirection


def coffee_pre_hook(model: "Coffee", *args, **kwargs):
    print("MORE COFFEEEEEE")


def worked_on_post_hook(model: "WorkingOn", *args, **kwargs):
    print("WORKING ON IT")


class WorkingOn(RelationshipModel):
    role: str

    class Settings:
        post_hooks = {"create": worked_on_post_hook}


class ImplementedFeature(RelationshipModel):
    name: str
    amount_of_bugs: int

    class Settings:
        type = "IMPLEMENTED"
        exclude_from_export = {"amount_of_bugs"}


class ConsumedBy(RelationshipModel):
    pass


class HatedBy(RelationshipModel):
    class Settings:
        type = "HATED_BY"


class Coffee(NodeModel):
    flavour: WithOptions(property_type=str, unique=True)
    origin: str

    typescript_developers: RelationshipProperty["TypescriptDeveloper", ConsumedBy] = RelationshipProperty(
        target_model="TypescriptDeveloper",
        relationship_model=ConsumedBy,
        direction=RelationshipPropertyDirection.OUTGOING,
        allow_multiple=False,
    )
    java_developers: RelationshipProperty["JavaDeveloper", ConsumedBy] = RelationshipProperty(
        target_model="JavaDeveloper",
        relationship_model=ConsumedBy,
        direction=RelationshipPropertyDirection.OUTGOING,
        allow_multiple=False,
    )

    class Settings:
        pre_hooks = {"create": coffee_pre_hook}


class Developer(NodeModel):
    id: WithOptions(property_type=UUID, range_index=True, unique=True) = Field(default_factory=uuid4)
    name: str

    projects: RelationshipProperty["Project", WorkingOn] = RelationshipProperty(
        target_model="Project",
        relationship_model=WorkingOn,
        direction=RelationshipPropertyDirection.OUTGOING,
        allow_multiple=False,
    )
    project_features: RelationshipProperty["Project", ImplementedFeature] = RelationshipProperty(
        target_model="Project",
        relationship_model="ImplementedFeature",
        direction=RelationshipPropertyDirection.OUTGOING,
        allow_multiple=True,
    )
    coffee: RelationshipProperty[Coffee, ConsumedBy] = RelationshipProperty(
        target_model=Coffee,
        relationship_model=ConsumedBy,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=False,
    )


class TypescriptDeveloper(Developer):
    hated_java_developes: RelationshipProperty["JavaDeveloper", HatedBy] = RelationshipProperty(
        target_model="JavaDeveloper",
        relationship_model=HatedBy,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=False,
    )

    class Settings:
        labels = {"Developer", "Happy"}


class JavaDeveloper(Developer):
    developers_hated_by: RelationshipProperty[TypescriptDeveloper, HatedBy] = RelationshipProperty(
        target_model=TypescriptDeveloper,
        relationship_model=HatedBy,
        direction=RelationshipPropertyDirection.OUTGOING,
        allow_multiple=False,
    )

    class Settings:
        labels = {"Developer", "RegretsLifeDecisions"}


class Milestone(BaseModel):
    name: str
    timestamp: float


class Project(NodeModel):
    name: str
    deadline: datetime
    metadata: Dict[str, Any]
    milestones: List[Milestone]

    typescript_developers: RelationshipProperty[TypescriptDeveloper, WorkingOn] = RelationshipProperty(
        target_model=TypescriptDeveloper,
        relationship_model=WorkingOn,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=False,
    )
    java_developers: RelationshipProperty[JavaDeveloper, WorkingOn] = RelationshipProperty(
        target_model=JavaDeveloper,
        relationship_model=WorkingOn,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=False,
    )
    typescript_developer_features: RelationshipProperty[TypescriptDeveloper, ImplementedFeature] = RelationshipProperty(
        target_model=TypescriptDeveloper,
        relationship_model=ImplementedFeature,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=True,
    )
    java_developer_features: RelationshipProperty[JavaDeveloper, ImplementedFeature] = RelationshipProperty(
        target_model=JavaDeveloper,
        relationship_model=ImplementedFeature,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=True,
    )

    class Settings:
        exclude_from_export = {"metadata"}
        auto_fetch_nodes = True
