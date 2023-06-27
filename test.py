import asyncio
import logging
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.client import Neo4jClient
from neo4j_ogm.fields import WithOptions
from neo4j_ogm.node import Neo4jNode
from neo4j_ogm.relationship_property import RelationshipProperty

logging.basicConfig(level=logging.DEBUG)


class MetaModel(BaseModel):
    registered: bool = False
    last_seen: datetime = Field(default_factory=datetime.now)


class MaleUserModel(Neo4jNode):
    __labels__ = ["User", "Male"]

    uid: WithOptions(UUID, indexed=True, unique=True) = Field(default_factory=uuid4)
    name: WithOptions(str, indexed=True) = "AAA"
    age: int = 23
    income: float = 2356.23
    dynamic: dict = {"dynamic": True, "uid": uuid4()}
    meta: MetaModel = MetaModel()


async def main():
    client = Neo4jClient(models=[MaleUserModel])
    await client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    await client.drop_constraints()
    await client.drop_nodes()

    user = MaleUserModel()
    await user.create()

    user.name = "123"
    await user.update()

    await user.delete()

    print("DONE")


asyncio.run(main())
