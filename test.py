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
    client = Neo4jClient(database_models=[TestModel])
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    await client.cypher("MATCH (n) RETURN n LIMIT 1")

    print("DONE")


asyncio.run(main())
