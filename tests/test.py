import asyncio

from neo4j_ogm.core.client import Neo4jClient
from tests.models import Actress, Role


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.drop_indexes()
    await client.drop_constraints()
    await client.drop_nodes()
    await client.register_models([Actress, Role])

    await Actress(name="Scarlett Johansson", age=35).create()
    actress = await Actress.find_one({"name": "Scarlett Johansson"})

    print("DONE")


asyncio.run(main())
