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
    await client.drop_nodes()
    await client.drop_constraints()
    await client.drop_indexes()

    john = Male(
        id=UUID("ab11097c-f75f-4555-a973-a70ebc46af35"),
        name="John Doe",
        age=42,
    )
    donald = Male(
        id=UUID("142eb1a0-1f8d-4acc-89ea-779b2b2f765a"),
        name="Donald Trump",
        age=64,
    )
    jimmy = Male(
        id=UUID("557e3222-fe41-40ae-a69a-5e9905f413df"),
        name="Jimmy Angel",
        age=39,
    )
    henry = Male(
        id=UUID("f5c0b68a-e89d-489d-a8a5-57078afee8c0"),
        name="Henry cavil",
        age=29,
    )

    await henry.create()
    await john.create()
    await donald.create()
    await jimmy.create()

    anna = Female(id=UUID("7c66ae5e-f0e1-4635-a2ba-356bef64b04e"), name="Anna Angel", age=39, letters=["a", "b", "c"])
    bella = Female(id=UUID("36eb1035-3159-4a0e-b066-399c62def0a5"), name="Bella Chao", age=21, letters=["d", "a"])
    stephany = Female(
        id=UUID("5b8d4097-5414-4f31-9a5e-6027de860585"), name="Stephany Dillenger", age=26, letters=["e", "f", "b"]
    )

    await anna.create()
    await bella.create()
    await stephany.create()

    await jimmy.females.connect(anna, {"since": datetime(2021, 12, 12)})

    await henry.females.connect(anna)
    await henry.females.connect(bella, {"since": datetime(2020, 1, 1)})
    await henry.females.connect(stephany, {"since": datetime(2020, 2, 4)})

    result = await Knows.count()

    print("DONE")


asyncio.run(main())
