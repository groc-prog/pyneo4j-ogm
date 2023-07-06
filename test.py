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


async def main():
    client = Neo4jClient(node_models=[TestModel])
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    a = await TestModel.find_many({"age": {"$gt": 30, "$lte": 35}})

    print("DONE")


# asyncio.run(main())


# a = ComparisonExpressionValidator()
# b = [value.alias for _, value in a.__fields__.items()]
# c = [value.field_info.extra["extra"]["parser"] for _, value in a.__fields__.items()]
# print("")

from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.queries.validators import ExpressionsValidator, Neo4jExpressionValidator

expression = {
    "age": {"$gte": "13", "$lt": 12},
    "name": {"$startsWith": 123},
    "friends": {"$not": {"$in": [1, 2, 3]}},
    "logical": {
        "$or": [
            {
                "$and": [
                    {"$gte": 12},
                    {"$lte": 34},
                ]
            },
            {"$eq": 45},
            {"$size": {"$not": {"$gt": 100}}},
        ]
    },
}

builder = QueryBuilder()
normalized = builder._validate_expressions(expression)

print(normalized)
