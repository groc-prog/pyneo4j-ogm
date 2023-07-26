# pylint: disable=missing-class-docstring missing-module-docstring
import logging

from neo4j_ogm.queries.types import RelationshipDirection

logging.basicConfig(level=logging.INFO)

import asyncio
import random
from datetime import datetime

from neo4j_ogm.core.client import Neo4jClient
from tests.adult_model import Adult, Friends, Married
from tests.child_model import Child, HasChild
from tests.toy_model import OwnsToy, Toy

client = Neo4jClient()
client.connect(uri="neo4j://localhost:7687", auth=("neo4j", "password"))


async def setup() -> None:
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()

    adult1 = await Adult(name="James", favorite_numbers=[1, 4, 6], age=23).create()
    adult2 = await Adult(name="Alice", favorite_numbers=[1, 7, 8], age=30).create()
    adult3 = await Adult(name="John", favorite_numbers=[4, 6], age=40).create()
    adult4 = await Adult(name="Emma", favorite_numbers=[9], age=28).create()
    adult5 = await Adult(name="John", favorite_numbers=[11, 24], age=35).create()
    adult6 = await Adult(name="Sophia", favorite_numbers=[15], age=25).create()

    child1 = await Child(name="Jamie").create()
    child2 = await Child(name="Emma").create()
    child3 = await Child(name="Noah").create()

    toy1 = await Toy(make="ToysAreUs", produced_at=random.randint(0, int(datetime.timestamp(datetime.now())))).create()
    toy2 = await Toy(make="PlayTime", produced_at=random.randint(0, int(datetime.timestamp(datetime.now())))).create()
    toy3 = await Toy(make="FunFuntime", produced_at=random.randint(0, int(datetime.timestamp(datetime.now())))).create()
    toy4 = await Toy(make="KidsJoy", produced_at=random.randint(0, int(datetime.timestamp(datetime.now())))).create()

    await adult1.partner.connect(adult2)
    await adult5.partner.connect(adult6)

    await adult1.friends.connect(adult3, {"since": datetime.now(), "best_friends": False})
    await adult1.friends.connect(adult4, {"since": datetime.now(), "best_friends": True})
    await adult2.friends.connect(adult4, {"since": datetime.now(), "best_friends": False})
    await adult3.friends.connect(adult4, {"since": datetime.now(), "best_friends": True})
    await adult3.friends.connect(adult4, {"since": datetime.now(), "best_friends": True})
    await adult5.friends.connect(adult4, {"since": datetime.now(), "best_friends": False})
    await adult6.friends.connect(adult4, {"since": datetime.now(), "best_friends": False})

    await adult1.children.connect(child1)
    await adult2.children.connect(child1)
    await adult5.children.connect(child2)
    await adult5.children.connect(child3)
    await adult6.children.connect(child2)
    await adult6.children.connect(child3)

    await child3.toys.connect(toy1)
    await child3.toys.connect(toy2)
    await child2.toys.connect(toy2)
    await child2.toys.connect(toy3)
    await child1.toys.connect(toy4)
    await child1.toys.connect(toy4)


async def main():
    await client.register_models([Adult, Married, Friends, Child, HasChild, Toy, OwnsToy])

    # await setup()

    # adults = await Adult.find_one(
    #     {
    #         "$patterns": [
    #             {
    #                 "$direction": RelationshipDirection.OUTGOING,
    #                 "$node": {"$labels": ["Adult"], "age": {"$gte": 20, "$lt": 28}},
    #                 "$relationship": {
    #                     "$type": "MARRIED",
    #                 },
    #             }
    #         ]
    #     }
    # )
    from neo4j_ogm.queries.query_builder import QueryBuilder

    builder = QueryBuilder()
    query, params = builder.build_node_expressions(
        {
            "$patterns": [
                {
                    "$direction": RelationshipDirection.OUTGOING,
                    "$node": {"$labels": ["Adult"]},
                    "$relationship": {
                        "$type": "MARRIED",
                    },
                    "$negate": True,
                },
                {
                    "$direction": RelationshipDirection.INCOMING,
                    "$relationship": {
                        "$type": "FRIENDS",
                    },
                    "$negate": False,
                },
                {
                    "$direction": RelationshipDirection.BOTH,
                    "$node": {"$labels": ["Child"]},
                    "$relationship": {
                        "$type": "SOMETHING",
                    },
                },
            ]
        }
    )

    print("DONE")


asyncio.run(main())
