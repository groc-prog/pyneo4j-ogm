import asyncio

from pyneo4j_ogm import (
    Neo4jClient,
    NodeModel,
    RelationshipModel,
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
    # Connect to the database and register the models
    client = Neo4jClient().connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    await client.register_models([Developer, Coffee, Drinks])

    # Create new developer and coffee nodes and connect them with a DRINKS relationship
    developer = await Developer(name="John Doe", age=25).create()
    coffee = await Coffee(name="Espresso").create()

    await developer.coffee.connect(coffee, {"likes_it": True})

    # Close connection again
    await client.close()


# Run the main function
asyncio.run(main())
