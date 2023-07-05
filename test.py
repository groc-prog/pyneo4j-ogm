import asyncio
import random
from uuid import uuid4

from neo4j_ogm.client import Neo4jClient
from neo4j_ogm.node import Neo4jNode


class TestModel(Neo4jNode):
    __labels__ = ["Test", "Node"]

    id: str
    name: str
    age: int


async def main():
    client = Neo4jClient()
    await client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    result = await TestModel.find_one({"age": 99})

    print("DONE")


asyncio.run(main())
