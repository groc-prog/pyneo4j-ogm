import asyncio

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.relationship_property import (
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)


class Developer(NodeModel):
    """
    A model representing a developer node in the graph.
    """

    name: str
    age: int

    coffee: RelationshipProperty["Coffee", "Drinks"] = RelationshipProperty(
        target_model="Coffee",
        relationship_model="Drinks",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )


class Coffee(NodeModel):
    """
    A model representing a coffee node in the graph.
    """

    name: str


class Drinks(RelationshipModel):
    """
    A model representing a DRINKS relationship between a developer and a coffee node.
    """

    likes_it: bool


async def main():
    from neo4j_ogm import Neo4jClient

    client = Neo4jClient()
    client.connect("bolt://localhost:7687", ("neo4j", "password"), max_connection_pool_size=10)
    await client.register_models([Developer, Coffee, Drinks])

    async with client.batch():
        # All queries executed inside the context manager will be batched into a single transaction
        # and executed once the context manager exits. If any of the queries fail, the whole transaction
        # will be rolled back.
        await client.cypher(
            query="CREATE (d:Developer {name: $name, age: $age})",
            parameters={"name": "John Doe", "age": 25},
        )
        await client.cypher(
            query="CREATE (c:Coffee {name: $name})",
            parameters={"name": "Espresso"},
        )

        # Model queries also can be batched together
        coffee = await Coffee(name="Americano").create()

    print("DONE")


asyncio.run(main())
