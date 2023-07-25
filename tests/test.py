# pylint: disable=missing-class-docstring missing-module-docstring
import logging

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
    await client.register_models([Adult, Married, Friends, Child, HasChild, Toy, OwnsToy])
    await client.drop_constraints()
    await client.drop_indexes()
    await client.drop_nodes()

    adult1 = await Adult(name="James", age=23).create()
    adult2 = await Adult(name="Alice", age=30).create()
    adult3 = await Adult(name="John", age=40).create()
    adult4 = await Adult(name="Emma", age=28).create()
    adult5 = await Adult(name="Michael", age=35).create()
    adult6 = await Adult(name="Sophia", age=25).create()

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


async def main():
    await setup()
    print("DONE")


asyncio.run(main())
