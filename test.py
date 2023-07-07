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
    await client.drop_indexes()
    await client.create_index("custom_index", "NODE", "TEXT", ["id", "name"], ["FOO", "BAR"])
    await client.create_index("custom_index1", "RELATIONSHIP", "RANGE", ["id", "name"], "REL")
    await client.create_index("custom_index2", "RELATIONSHIP", "POINT", ["id", "name"], "REL1")
    await client.create_index("custom_index3", "RELATIONSHIP", "TOKEN", ["id", "name"], "REL2")
    await client.create_constraint("custom_index4", "NODE", ["id", "name"], ["FOO1", "BAR1"])
    await client.create_constraint("custom_index5", "RELATIONSHIP", ["id", "name"], "REL3")

    # a = TestModel.find_many({"age": {"$gt": 30, "$lte": 35}})

    print("DONE")


asyncio.run(main())
