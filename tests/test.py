# pylint: disable-all

import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

from neo4j_ogm.core.client import Neo4jClient
from tests.models import (
    Coffee,
    ConsumedBy,
    HatedBy,
    ImplementedFeature,
    JavaDeveloper,
    Milestone,
    Project,
    TypescriptDeveloper,
    WorkingOn,
)


async def main():
    client = Neo4jClient()

    client.connect("bolt://localhost:7687", ("neo4j", "password"))
    await client.drop_nodes()
    await client.register_models(
        [Coffee, TypescriptDeveloper, JavaDeveloper, Project, ConsumedBy, WorkingOn, HatedBy, ImplementedFeature]
    )

    jim = await TypescriptDeveloper(name="Jim", id="2bf37261-30bf-4de5-bcdf-28b579c9fe02").create()
    martin = await JavaDeveloper(name="Martin", id="b4c2b7e0-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
    phil = await TypescriptDeveloper(name="Phil", id="c2b7e0b4-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
    thomas = await TypescriptDeveloper(name="Thomas", id="b7e0b4c2-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
    salli = await TypescriptDeveloper(name="Salli", id="e0b4c2b7-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()

    project_one = await Project(
        name="Project One",
        deadline="2022-01-01T12:00:00Z",
        metadata={"awesome": True},
        milestones=[Milestone(name="That hard thing done", timestamp=1691696518)],
    ).create()
    project_two = await Project(
        name="Project Two",
        deadline="2022-04-23T16:45:00Z",
        metadata={},
        milestones=[
            Milestone(name="Finished talking with important person", timestamp=1691825684),
            Milestone(name="Got copilot to do the work for me", timestamp=1691682690),
        ],
    ).create()

    macchiato = await Coffee(flavour="Macchiato", origin="Italy").create()
    espresso = await Coffee(flavour="Espresso", origin="Colombia").create()
    dark_roast = await Coffee(flavour="Dark Roast", origin="Brazil").create()

    await jim.projects.connect(project_one, {"role": "Lead"})
    await jim.projects.connect(project_two, {"role": "Developer"})
    await martin.projects.connect(project_two, {"role": "Developer"})
    await phil.projects.connect(project_two, {"role": "Intern"})
    await salli.projects.connect(project_two, {"role": "Lead"})
    await thomas.projects.connect(project_two, {"role": "Developer"})

    await jim.project_features.connect(project_one, {"name": "Implemented the thing", "amount_of_bugs": 3})
    await jim.project_features.connect(project_one, {"name": "Some more things", "amount_of_bugs": 5})
    await jim.project_features.connect(project_two, {"name": "Something veeeery important", "amount_of_bugs": 0})
    await martin.project_features.connect(project_one, {"name": "Implemented the other thing", "amount_of_bugs": 29})
    await salli.project_features.connect(project_two, {"name": "Serious work", "amount_of_bugs": 7})

    await martin.developers_hated_by.connect(jim)
    await martin.developers_hated_by.connect(phil)
    await martin.developers_hated_by.connect(thomas)
    await martin.developers_hated_by.connect(salli)

    await espresso.typescript_developers.connect(jim)
    await espresso.java_developers.connect(martin)
    await dark_roast.typescript_developers.connect(phil)
    await macchiato.typescript_developers.connect(phil)

    print("DONE")


asyncio.run(main())
