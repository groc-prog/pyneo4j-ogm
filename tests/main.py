import asyncio

from pyneo4j_ogm import (
    Neo4jClient,
    NodeModel,
    RelationshipModel,
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)
from pyneo4j_ogm.core.client import EntityType, IndexType


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
    dev: RelationshipProperty["Developer", "Drinks"] = RelationshipProperty(
        target_model="Developer",
        relationship_model="Drinks",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )

    class Settings:
        auto_fetch_nodes = True


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
    client = Neo4jClient()
    client.connect(uri="bolt://localhost:7687", auth=("neo4j", "password"))
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()
    await client.register_models([Developer, Coffee, Drinks])

    # Update instance with new values
    developer = await Developer(name="John", age=25).create()
    dev2 = await Developer(name="Jenny", age=22).create()

    # Create a new coffee node
    coffee = await Coffee(name="Espresso").create()

    # Connect the developer and coffee nodes with a DRINKS relationship
    drink1 = await developer.coffee.connect(coffee, {"likes_it": True})
    drink2 = await developer.dev.connect(dev2, {"likes_it": False})

    # developer = await Developer.update_many({"name": "Foo", "foo": "bar"}, {"age": 25}, new=True)

    await client.close()

    print(developer)
    print(coffee)

    print("Done!")


# Run the main function
asyncio.run(main())
