import asyncio
import logging
import os

os.environ["NEO4J_OGM_LOG_LEVEL"] = str(logging.DEBUG)

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.fields.relationship_property import (
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)


class Developer(NodeModel):
    name: str
    age: int

    bar: RelationshipProperty["Bar", "GoesTo"] = RelationshipProperty(
        target_model="Bar",
        relationship_model="GoesTo",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )


class Coffee(NodeModel):
    name: str

    bar: RelationshipProperty["Bar", "Sells"] = RelationshipProperty(
        target_model="Bar",
        relationship_model="Sells",
        direction=RelationshipPropertyDirection.INCOMING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )


class Bar(NodeModel):
    coffee: RelationshipProperty["Coffee", "Sells"] = RelationshipProperty(
        target_model="Coffee",
        relationship_model="Sells",
        direction=RelationshipPropertyDirection.OUTGOING,
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple=False,
    )


class Sells(RelationshipModel):
    ok: bool


class GoesTo(RelationshipModel):
    pass


async def main():
    client = Neo4jClient()
    client.connect("bolt://localhost:7687", ("neo4j", "password"), max_connection_pool_size=10)
    # await client.drop_nodes()
    await client.register_models([Developer, Coffee, GoesTo, Sells, Bar])

    # dev = Developer(name="John", age=30)
    # bar = Bar()
    # coffee1 = Coffee(name="Espresso")
    # coffee2 = Coffee(name="Cappuccino")
    # coffee3 = Coffee(name="Latte")
    # coffee4 = Coffee(name="Mocha")

    # await dev.create()
    # await bar.create()
    # await coffee1.create()
    # await coffee2.create()
    # await coffee3.create()
    # await coffee4.create()

    # await dev.bar.connect(bar)
    # await bar.coffee.connect(coffee1, {"ok": True})
    # await bar.coffee.connect(coffee2, {"ok": True})
    # await bar.coffee.connect(coffee3, {"ok": False})
    # await bar.coffee.connect(coffee4, {"ok": True})

    # result = await dev.find_connected_nodes(
    #     {
    #         "$node": {},
    #         "$relationships": [{"$type": Sells.model_settings()["type"], "ok": True}],
    #     }
    # )

    from neo4j_ogm.queries.query_builder import QueryBuilder

    builder = QueryBuilder()

    builder.node_filters({"$projections": {}})

    dev = await Developer.find_one({"name": "John"})

    if dev is not None:
        result = await dev.find_connected_nodes(
            {
                "$node": {"$labels": ["Coffee"]},
                "$relationships": [{"$type": Sells.model_settings()["type"], "ok": True}],
            },
            auto_fetch_nodes=True,
        )

    print("DONE")


asyncio.run(main())
