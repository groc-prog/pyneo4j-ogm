# pylint: disable-all

import asyncio
import logging

from neo4j_ogm.queries.query_builder import QueryBuilder

logging.basicConfig(level=logging.DEBUG)

import asyncio
from typing import Any, Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.property_options import WithOptions
from neo4j_ogm.fields.relationship_property import RelationshipProperty, RelationshipPropertyDirection


class FrontendDeveloper(NodeModel):
    id: WithOptions(property_type=UUID, range_index=True) = Field(default_factory=uuid4)
    name: str
    age: int
    likes_his_job: bool

    class Settings:
        labels = {"Developer", "Sane"}


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.drop_indexes()
    await client.drop_constraints()
    await client.drop_nodes()
    await client.register_models([Actress, Actor, WorkedTogether, Friends, Producer, WorkedFor])

    a = await Actress(name="Scarlett Johansson", age=41).create()
    g = await Actress(name="Rachel McAdams", age=41).create()
    b = await Actor(name="Gal Gadot", age=29).create()
    c = await Actor(name="Margot Robbie", age=39).create()
    d = await Actor(name="Jennifer Lawrence", age=30).create()
    e = await Producer(name="Angelina Jolie", age=45).create()
    f = await Producer(name="Arnold Schwarzenegger", age=31).create()

    await a.colleagues.connect(b)
    await a.colleagues.connect(c)
    await g.colleagues.connect(d)
    await a.bosses.connect(e)
    await g.bosses.connect(f)

    result = await Actress.find_many({"age": 41}, auto_fetch_nodes=False)

    print("DONE")


asyncio.run(main())
