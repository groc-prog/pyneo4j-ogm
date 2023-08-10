import asyncio
import logging

from neo4j_ogm.queries.query_builder import QueryBuilder

logging.basicConfig(level=logging.DEBUG)

from neo4j_ogm.core.client import Neo4jClient
from tests.models import Actor, Actress, Friends, Producer, WorkedFor, WorkedTogether


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
