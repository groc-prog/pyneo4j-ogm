import asyncio

from neo4j_ogm.core.client import Neo4jClient


async def main():
    client = Neo4jClient()
    await client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    results, _ = await client.cypher("MATCH ()-[r]->() RETURN r")

    rel = results[0][0]
    b = rel.__dict__
    print("DONE")


asyncio.run(main())
