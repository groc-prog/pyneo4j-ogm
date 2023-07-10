import asyncio
import logging
import random
from copy import deepcopy
from typing import Any, Dict, Generic, Type, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from neo4j_ogm.core.client import BatchManager, Neo4jClient
from neo4j_ogm.core.node import Neo4jNode
from neo4j_ogm.fields import WithOptions
from neo4j_ogm.queries.query_builder import QueryBuilder

logging.basicConfig(level=logging.DEBUG)

names = [
    "Alice",
    "Bob",
    "Charlie",
    "David",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Ivy",
    "Jack",
    "Katherine",
    "Liam",
    "Mia",
    "Noah",
    "Olivia",
    "Penelope",
    "Quinn",
    "Ryan",
    "Sophia",
    "Thomas",
]


class MetaModel(BaseModel):
    msg: str = "METADATA"


class TestModel(Neo4jNode):
    __labels__ = ["Test", "Node"]

    id: str
    name: str
    age: int
    friends: list[str]
    best_friend: str
    meta: MetaModel = MetaModel()
    json_data: Dict[str, str] = {"key": "value"}


expressions = {
    # "age": {"$or": [{"$and": [{"$gte": 30}, {"$lte": 45}]}, {"$eq": 60}]},
    # "best_friend": {"$in": "Henry"},
    # "special": {"$exists": True},
    # "$elementId": "non-existing"
    "special": True
}


async def main():
    client = Neo4jClient()
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    # await client.drop_constraints()
    # await client.drop_indexes()
    # await client.drop_nodes()
    await client.register_models(models=[TestModel])

    # for i in range(20):
    #     await TestModel(
    #         id=str(uuid4()),
    #         name=f"instance-{i}",
    #         age=random.randint(1, 100),
    #         best_friend=random.sample(names, 1)[0],
    #         friends=random.sample(names, random.randint(3, 10)),
    #     ).create()

    async with client.batch():
        result_one = await TestModel.find_one(expressions)
        result_two = await TestModel.delete_one(expressions)
        # result_one = await TestModel.update_many({"special": False}, expressions, False, True)
    # result_many = await TestModel.find_many(expressions)

    # instance = await TestModel(id=str(uuid4()), name=f"instance-0", age=random.randint(1, 100)).create()
    # instance.name = "instance-updated"
    # instance.age = 20
    # await instance.update()
    # await instance.delete()

    print("DONE")


asyncio.run(main())

# 5 7 12 19
