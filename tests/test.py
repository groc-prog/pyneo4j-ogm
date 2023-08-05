import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from neo4j_ogm import Neo4jClient
from tests.models import Actor, Actress, Friends, WorkedTogether


async def main():
    client = Neo4jClient().connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.register_models([Actress, Actor, WorkedTogether, Friends])

    results, _ = await client.cypher("MATCH (n) RETURN n.id")

    print("DONE")


asyncio.run(main())
