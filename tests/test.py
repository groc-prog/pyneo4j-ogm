import asyncio
import logging

logging.basicConfig(level=logging.WARNING)

from neo4j_ogm.core.client import Neo4jClient
from tests.models import Actor, Actress, Role


def hook(*args, **kwargs):
    print(args, kwargs)


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.drop_indexes()
    await client.drop_constraints()
    await client.drop_nodes()
    await client.register_models([Actress])

    Actress.register_post_hooks("create", hook)

    a = await Actress(name="Scarlett Johansson", age=35).create()
    b = await Actress(name="Gal Gadot", age=29).create()
    c = await Actress(name="Margot Robbie", age=39).create()
    d = await Actress(name="Jennifer Lawrence", age=30).create()
    e = await Actress(name="Angelina Jolie", age=45).create()
    f = await Actor(name="Arnold Schwarzenegger", age=31).create()

    print("DONE")


asyncio.run(main())
