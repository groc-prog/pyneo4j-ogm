import asyncio
import random
from copy import deepcopy
from typing import Generic, Type, TypeVar
from uuid import uuid4

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import Neo4jNode
from neo4j_ogm.fields import WithOptions


class TestModel(Neo4jNode):
    __labels__ = ["Test", "Node"]

    id: str
    name: str
    age: int


class RefModel(Neo4jNode):
    __labels__ = ["Ref"]

    id: str
    name: str


class ExceptionModel(Neo4jNode):
    __labels__ = ["Exception"]

    id: WithOptions(str, unique=True) = str("ID")


class TestExceptionModel(Neo4jNode):
    __labels__ = ["TestException"]

    id: str


async def main():
    client = Neo4jClient(node_models=[TestModel])
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    await client.drop_constraints()
    await client.set_constraint("exception_model_unique", "NODE", ["id"], ["Exception"])

    # a = TestModel.find_many({"age": {"$gt": 30, "$lte": 35}})

    print("DONE")


asyncio.run(main())
