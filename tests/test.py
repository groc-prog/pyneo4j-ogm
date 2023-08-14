# pylint: disable-all

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

os.environ["NEO4J_OGM_LOG_LEVEL"] = "DEBUG"
os.environ["NEO4J_OGM_ENABLE_LOGGING"] = str(True)

from neo4j_ogm import (
    Neo4jClient,
    NodeModel,
    RelationshipModel,
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
    WithOptions,
)
from neo4j_ogm.queries.validators import QueryOptionsOrder


def hook(*args, **kwargs):
    print("HOOK", args, kwargs)


class MetaInformation(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Knows(RelationshipModel):
    since: datetime = Field(default_factory=datetime.now)


class Male(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, range_index=True)
    age: int
    happy: bool = True
    meta_data_info: Dict[str, Any] = {"created_at": datetime.now().isoformat()}

    females: RelationshipProperty["Female", Knows] = RelationshipProperty(
        target_model="Female",
        relationship_model=Knows,
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )

    class Settings:
        exclude_from_export = {"meta_data_info"}
        labels = "Male"
        pre_hooks = {"delete": [hook]}
        post_hooks = {"update": hook}
        auto_fetch_nodes = True


class Female(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, text_index=True)
    age: int
    happy: bool = False
    meta_data_info: MetaInformation = MetaInformation()
    letters: List[str]

    males: RelationshipProperty[Male, Knows] = RelationshipProperty(
        target_model=Male,
        relationship_model="Knows",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=False,
    )


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.register_models([Male, Female, Knows])

    async with client.batch():
        await Male(name="foo1", age=1).create()
        await Male(name="bar1", age=2).create()
        raise Exception("OH NOOO")

    print("DONE")


asyncio.run(main())
