# pylint: disable-all

import asyncio
import logging
import os
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

os.environ["NEO4J_OGM_LOG_LEVEL"] = "WARNING"
os.environ["NEO4J_OGM_ENABLE_LOGGING"] = str(True)

from neo4j_ogm import Neo4jClient, NodeModel, RelationshipModel, RelationshipProperty, WithOptions


def hook(*args, **kwargs):
    print("HOOK", args, kwargs)


class MetaInformation(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Male(NodeModel):
    id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, range_index=True)
    age: int
    happy: bool = True
    meta_data_info: dict = {"created_at": datetime.now().isoformat()}

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


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.drop_nodes()
    await client.drop_constraints()
    await client.drop_indexes()
    await client.register_models([Male, Female])

    john = Male(
        name="John Doe",
        age=42,
    )
    james = Male(
        name="James Doe",
        age=26,
    )
    jimmy = await Male(
        name="Jimmy Angel",
        age=39,
    ).create()

    anna = await Female(
        name="Anna Angel",
        age=39,
    ).create()

    print(jimmy.model_settings)
    exported = jimmy.export_model()

    print("DONE")


asyncio.run(main())
