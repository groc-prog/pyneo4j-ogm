import asyncio
import random
from copy import deepcopy
from typing import Generic, Type, TypeVar
from uuid import uuid4

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import Neo4jNode


class TestModel(Neo4jNode):
    __labels__ = ["Test", "Node"]

    id: str
    name: str
    age: int


class RefModel(Neo4jNode):
    __labels__ = ["Ref"]

    id: str
    name: str


async def main():
    client = Neo4jClient(node_models=[TestModel])
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    # a = await TestModel.find_many({"age": {"$gt": 30, "$lte": 35}})
    for i in range(20):
        instance = RefModel(id=str(uuid4()), name=f"instance-{i}")

        await instance.create()

    print("DONE")


asyncio.run(main())
