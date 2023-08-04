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

    await Actress(name="Scarlett Johansson", age=35).create()
    await Actress(name="Gal Gadot", age=29).create()
    await Actress(name="Margot Robbie", age=39).create()
    await Actress(name="Jennifer Lawrence", age=30).create()
    await Actress(name="Angelina Jolie", age=45).create()
    await Actor(name="Arnold Schwarzenegger", age=31).create()

    result = await Actor.find_one({"name": "Arnold Schwarzenegger"})

    print("DONE")


asyncio.run(main())
