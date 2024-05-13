"""
Fixture for setup/teardown of a Neo4j database for integration tests.
"""

# pylint: disable=redefined-outer-name, missing-class-docstring

from typing import Any, Dict, List

import pytest
from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.graph import Node

from pyneo4j_ogm import (
    NodeModel,
    Pyneo4jClient,
    RelationshipModel,
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2


class Developer(NodeModel):
    uid: int
    name: str
    age: int

    colleagues: RelationshipProperty["Developer", "WorkedWith"] = RelationshipProperty(
        target_model="Developer",
        relationship_model="WorkedWith",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=True,
    )
    coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
        target_model="Coffee",
        relationship_model="Consumed",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )


class Coffee(NodeModel):
    flavor: str
    sugar: bool
    milk: bool
    note: Dict[str, Any]

    developers: RelationshipProperty["Developer", "Consumed"] = RelationshipProperty(
        target_model="Developer",
        relationship_model="Consumed",
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )
    bestseller_for: RelationshipProperty["CoffeeShop", "Bestseller"] = RelationshipProperty(
        target_model="CoffeeShop",
        relationship_model="Bestseller",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )

    class Settings:
        labels = {"Beverage", "Hot"}


class CoffeeShop(NodeModel):
    rating: int
    tags: List[str]

    coffees: RelationshipProperty["Coffee", "Sells"] = RelationshipProperty(
        target_model="Coffee",
        relationship_model="Sells",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )
    bestseller: RelationshipProperty["Coffee", "Bestseller"] = RelationshipProperty(
        target_model="Coffee",
        relationship_model="Bestseller",
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_ONE,
        allow_multiple=False,
    )


class WorkedWith(RelationshipModel):
    language: str

    class Settings:
        type = "WAS_WORK_BUDDY_WITH"


class Consumed(RelationshipModel):
    liked: bool

    class Settings:
        type = "LIKES_TO_DRINK"


class Sells(RelationshipModel):
    pass


class Bestseller(RelationshipModel):
    class Settings:
        type = "BESTSELLER_OF"


@pytest.fixture
async def client():
    """
    Create a Pyneo4jClient instance from the package for the test session.
    """
    client = await Pyneo4jClient().connect("bolt://localhost:7687", auth=("neo4j", "password"))

    # Drop all nodes, indexes, and constraints from the database.
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()

    yield client

    await client.close()


@pytest.fixture
async def session():
    """
    Create a neo4j driver instance for the test session.
    """
    driver = AsyncGraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "password"))

    async with driver.session() as session:
        yield session

    await driver.close()


@pytest.fixture
async def setup_test_data(client: Pyneo4jClient, session: AsyncSession):
    client.models = set()
    await client.register_models([Developer, Coffee, CoffeeShop, WorkedWith, Consumed, Sells, Bestseller])
    await session.run(
        """
    CREATE (s1:CoffeeShop {rating: 5, tags: ["cozy", "hipster"]})
    CREATE (s2:CoffeeShop {rating: 1, tags: ["chain"]})
    CREATE (s3:CoffeeShop {rating: 3, tags: ["chain", "hipster"]})

    CREATE (c1:Beverage:Hot {flavor: "Espresso", sugar: false, milk: false, note: '{\"roast\": \"dark\"}'})
    CREATE (c2:Beverage:Hot {flavor: "Latte", sugar: true, milk: true, note: '{\"roast\": \"medium\"}'})
    CREATE (c3:Beverage:Hot {flavor: "Cappuccino", sugar: true, milk: true, note: '{\"roast\": \"medium\"}'})
    CREATE (c4:Beverage:Hot {flavor: "Americano", sugar: false, milk: false, note: '{\"roast\": \"light\"}'})
    CREATE (c5:Beverage:Hot {flavor: "Mocha", sugar: true, milk: true, note: '{\"roast\": \"dark\"}'})

    CREATE (d1:Developer {uid: 1, name: "John", age: 30})
    CREATE (d2:Developer {uid: 2, name: "Sam", age: 25})
    CREATE (d3:Developer {uid: 3, name: "Alice", age: 27})
    CREATE (d4:Developer {uid: 4, name: "Bob", age: 32})

    CREATE (s1)-[:SELLS]->(c1)
    CREATE (s1)-[:SELLS]->(c4)
    CREATE (s1)<-[:BESTSELLER_OF]-(c4)

    CREATE (s2)-[:SELLS]->(c1)
    CREATE (s2)-[:SELLS]->(c3)
    CREATE (s2)-[:SELLS]->(c5)
    CREATE (s2)<-[:BESTSELLER_OF]-(c3)

    CREATE (s3)-[:SELLS]->(c2)
    CREATE (s3)-[:SELLS]->(c5)
    CREATE (s3)<-[:BESTSELLER_OF]-(c5)

    CREATE (d1)-[:LIKES_TO_DRINK {liked: True}]->(c1)
    CREATE (d1)-[:LIKES_TO_DRINK {liked: False}]->(c2)
    CREATE (d2)-[:LIKES_TO_DRINK {liked: True}]->(c3)
    CREATE (d3)-[:LIKES_TO_DRINK {liked: True}]->(c4)
    CREATE (d3)-[:LIKES_TO_DRINK {liked: False}]->(c5)
    CREATE (d3)-[:LIKES_TO_DRINK {liked: False}]->(c1)

    CREATE (d1)-[:WAS_WORK_BUDDY_WITH {language: "Python"}]->(d2)
    CREATE (d1)-[:WAS_WORK_BUDDY_WITH {language: "Java"}]->(d2)
    CREATE (d1)-[:WAS_WORK_BUDDY_WITH {language: "Python"}]->(d3)
    CREATE (d2)-[:WAS_WORK_BUDDY_WITH {language: "Lisp"}]->(d4)
    CREATE (d3)-[:WAS_WORK_BUDDY_WITH {language: "Javascript"}]->(d1)
    CREATE (d3)-[:WAS_WORK_BUDDY_WITH {language: "Javascript"}]->(d4)
    CREATE (d4)-[:WAS_WORK_BUDDY_WITH {language: "Go"}]->(d3)
    """
    )

    result = await session.run(
        """
    MATCH ()-[r]->()
    WITH DISTINCT collect(r) as relationships
    MATCH (n)
    WITH DISTINCT collect(n) as nodes, relationships
    RETURN nodes, relationships
    """
    )

    result_values = await result.values()
    await result.consume()

    yield result_values

    client.models = set()


@pytest.fixture
def dev_model_instances(setup_test_data):
    john: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Developer.model_settings().labels and result["uid"] == 1
    ][0]
    sam: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Developer.model_settings().labels and result["uid"] == 2
    ][0]
    alice: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Developer.model_settings().labels and result["uid"] == 3
    ][0]
    bob: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Developer.model_settings().labels and result["uid"] == 4
    ][0]

    john_model = Developer._inflate(john)
    sam_model = Developer._inflate(sam)
    alice_model = Developer._inflate(alice)
    bob_model = Developer._inflate(bob)

    return john_model, sam_model, alice_model, bob_model


@pytest.fixture
def coffee_model_instances(setup_test_data):
    latte: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Coffee.model_settings().labels and result["flavor"] == "Latte"
    ][0]
    mocha: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Coffee.model_settings().labels and result["flavor"] == "Mocha"
    ][0]
    espresso: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == Coffee.model_settings().labels and result["flavor"] == "Espresso"
    ][0]

    latte_model = Coffee._inflate(latte)
    mocha_model = Coffee._inflate(mocha)
    espresso_model = Coffee._inflate(espresso)

    return latte_model, mocha_model, espresso_model


@pytest.fixture
def coffee_shop_model_instances(setup_test_data):
    rating_five: Node = [
        result
        for result in setup_test_data[0][0]
        if result.labels == CoffeeShop.model_settings().labels and result["rating"] == 5
    ][0]

    rating_five_model = CoffeeShop._inflate(rating_five)

    return (rating_five_model,)


if not IS_PYDANTIC_V2:
    Developer.update_forward_refs()
    Coffee.update_forward_refs()
    Consumed.update_forward_refs()
    WorkedWith.update_forward_refs()
    CoffeeShop.update_forward_refs()
    Sells.update_forward_refs()
    Bestseller.update_forward_refs()
