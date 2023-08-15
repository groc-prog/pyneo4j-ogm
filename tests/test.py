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
    client = Neo4jClient().connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.register_models([Developer, Coffee, Drinks])

    a = Developer.model_settings()

    print("DONE")


asyncio.run(main())
