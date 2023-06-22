import asyncio

from neo4j_ogm.core.client import Neo4jClient


async def main():
    client = Neo4jClient()
    await client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    print("DONE")


asyncio.run(main())
