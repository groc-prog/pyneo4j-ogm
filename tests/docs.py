##################### MODELS #####################
# # pylint: disable-all

# from datetime import datetime
# from typing import Any, Dict, List
# from uuid import UUID, uuid4

# from pydantic import BaseModel, Field

# from neo4j_ogm.core.node import NodeModel
# from neo4j_ogm.core.relationship import RelationshipModel
# from neo4j_ogm.fields.property_options import WithOptions
# from neo4j_ogm.fields.relationship_property import RelationshipPropertyCardinality, RelationshipProperty, RelationshipPropertyDirection


# def coffee_pre_hook(model: "Coffee", *args, **kwargs):
#     print("MORE COFFEEEEEE")


# def worked_on_post_hook(model: "WorkingOn", *args, **kwargs):
#     print("WORKING ON IT")


# class WorkingOn(RelationshipModel):
#     role: str

#     class Settings:
#         post_hooks = {"create": worked_on_post_hook}


# class ImplementedFeature(RelationshipModel):
#     name: str
#     amount_of_bugs: int

#     class Settings:
#         type = "IMPLEMENTED"
#         exclude_from_export = {"amount_of_bugs"}


# class ConsumedBy(RelationshipModel):
#     pass


# class HatedBy(RelationshipModel):
#     class Settings:
#         type = "HATED_BY"


# class Coffee(NodeModel):
#     flavour: WithOptions(property_type=str, unique=True)
#     origin: str

#     typescript_developers: RelationshipProperty["TypescriptDeveloper", ConsumedBy] = RelationshipProperty(
#         target_model="TypescriptDeveloper",
#         relationship_model=ConsumedBy,
#         direction=RelationshipPropertyDirection.OUTGOING,
#         allow_multiple=False,
#     )
#     java_developers: RelationshipProperty["JavaDeveloper", ConsumedBy] = RelationshipProperty(
#         target_model="JavaDeveloper",
#         relationship_model=ConsumedBy,
#         direction=RelationshipPropertyDirection.OUTGOING,
#         allow_multiple=False,
#     )

#     class Settings:
#         pre_hooks = {"create": coffee_pre_hook}


# class Developer(NodeModel):
#     id: WithOptions(property_type=UUID, range_index=True, unique=True) = Field(default_factory=uuid4)
#     name: str

#     projects: RelationshipProperty["Project", WorkingOn] = RelationshipProperty(
#         target_model="Project",
#         relationship_model=WorkingOn,
#         direction=RelationshipPropertyDirection.OUTGOING,
#         allow_multiple=False,
#     )
#     project_features: RelationshipProperty["Project", ImplementedFeature] = RelationshipProperty(
#         target_model="Project",
#         relationship_model="ImplementedFeature",
#         direction=RelationshipPropertyDirection.OUTGOING,
#         allow_multiple=True,
#     )
#     coffee: RelationshipProperty[Coffee, ConsumedBy] = RelationshipProperty(
#         target_model=Coffee,
#         relationship_model=ConsumedBy,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=False,
#     )


# class TypescriptDeveloper(Developer):
#     hated_java_developes: RelationshipProperty["JavaDeveloper", HatedBy] = RelationshipProperty(
#         target_model="JavaDeveloper",
#         relationship_model=HatedBy,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=False,
#     )

#     class Settings:
#         labels = {"Developer", "Happy"}


# class JavaDeveloper(Developer):
#     developers_hated_by: RelationshipProperty[TypescriptDeveloper, HatedBy] = RelationshipProperty(
#         target_model=TypescriptDeveloper,
#         relationship_model=HatedBy,
#         direction=RelationshipPropertyDirection.OUTGOING,
#         allow_multiple=False,
#         cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
#     )

#     class Settings:
#         labels = {"Developer", "RegretsLifeDecisions"}


# class Milestone(BaseModel):
#     name: str
#     timestamp: float


# class Project(NodeModel):
#     name: str
#     deadline: datetime
#     metadata: Dict[str, Any]
#     milestones: List[Milestone]

#     typescript_developers: RelationshipProperty[TypescriptDeveloper, WorkingOn] = RelationshipProperty(
#         target_model=TypescriptDeveloper,
#         relationship_model=WorkingOn,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=False,
#     )
#     java_developers: RelationshipProperty[JavaDeveloper, WorkingOn] = RelationshipProperty(
#         target_model=JavaDeveloper,
#         relationship_model=WorkingOn,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=False,
#     )
#     typescript_developer_features: RelationshipProperty[TypescriptDeveloper, ImplementedFeature] = RelationshipProperty(
#         target_model=TypescriptDeveloper,
#         relationship_model=ImplementedFeature,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=True,
#     )
#     java_developer_features: RelationshipProperty[JavaDeveloper, ImplementedFeature] = RelationshipProperty(
#         target_model=JavaDeveloper,
#         relationship_model=ImplementedFeature,
#         direction=RelationshipPropertyDirection.INCOMING,
#         allow_multiple=True,
#     )

#     class Settings:
#         exclude_from_export = {"metadata"}
#         auto_fetch_nodes = True

##################### MAIN.PY #####################
# # pylint: disable-all

# import asyncio
# import logging
# import os

# os.environ["NEO4J_OGM_LOG_LEVEL"] = "WARNING"
# os.environ["NEO4J_OGM_ENABLE_LOGGING"] = str(True)

# from neo4j_ogm.core.client import Neo4jClient
# from tests.models import (
#     Coffee,
#     ConsumedBy,
#     HatedBy,
#     ImplementedFeature,
#     JavaDeveloper,
#     Milestone,
#     Project,
#     TypescriptDeveloper,
#     WorkingOn,
# )


# async def setup():
#     jim = await TypescriptDeveloper(name="Jim", id="2bf37261-30bf-4de5-bcdf-28b579c9fe02").create()
#     martin = await JavaDeveloper(name="Martin", id="b4c2b7e0-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
#     phil = await TypescriptDeveloper(name="Phil", id="c2b7e0b4-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
#     thomas = await TypescriptDeveloper(name="Thomas", id="b7e0b4c2-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()
#     salli = await TypescriptDeveloper(name="Salli", id="e0b4c2b7-eeb1-4b9e-9e4c-6e9c9f1f8d8a").create()

#     project_one = await Project(
#         name="Project One",
#         deadline="2022-01-01T12:00:00Z",
#         metadata={"awesome": True},
#         milestones=[Milestone(name="That hard thing done", timestamp=1691696518)],
#     ).create()
#     project_two = await Project(
#         name="Project Two",
#         deadline="2022-04-23T16:45:00Z",
#         metadata={},
#         milestones=[
#             Milestone(name="Finished talking with important person", timestamp=1691825684),
#             Milestone(name="Got copilot to do the work for me", timestamp=1691682690),
#         ],
#     ).create()

#     macchiato = await Coffee(flavour="Macchiato", origin="Italy").create()
#     espresso = await Coffee(flavour="Espresso", origin="Colombia").create()
#     dark_roast = await Coffee(flavour="Dark Roast", origin="Brazil").create()

#     await jim.projects.connect(project_one, {"role": "Lead"})
#     await jim.projects.connect(project_two, {"role": "Developer"})
#     await martin.projects.connect(project_two, {"role": "Developer"})
#     await phil.projects.connect(project_two, {"role": "Intern"})
#     await salli.projects.connect(project_two, {"role": "Lead"})
#     await thomas.projects.connect(project_two, {"role": "Developer"})

#     await jim.project_features.connect(project_one, {"name": "Implemented the thing", "amount_of_bugs": 3})
#     await jim.project_features.connect(project_one, {"name": "Some more things", "amount_of_bugs": 5})
#     await jim.project_features.connect(project_two, {"name": "Something veeeery important", "amount_of_bugs": 0})
#     await martin.project_features.connect(project_one, {"name": "Implemented the other thing", "amount_of_bugs": 29})
#     await salli.project_features.connect(project_two, {"name": "Serious work", "amount_of_bugs": 7})

#     await martin.developers_hated_by.connect(jim)
#     await martin.developers_hated_by.connect(phil)
#     await martin.developers_hated_by.connect(thomas)
#     await martin.developers_hated_by.connect(salli)

#     await espresso.typescript_developers.connect(jim)
#     await espresso.java_developers.connect(martin)
#     await dark_roast.typescript_developers.connect(phil)
#     await macchiato.typescript_developers.connect(phil)


# async def main():
#     client = Neo4jClient()

#     client.connect("bolt://localhost:7687", ("neo4j", "password"))
#     await client.drop_nodes()
#     await client.drop_constraints()
#     await client.drop_indexes()
#     await client.register_models(
#         [Coffee, TypescriptDeveloper, JavaDeveloper, Project, ConsumedBy, WorkingOn, HatedBy, ImplementedFeature]
#     )

#     await setup()

#     print("DONE")


# asyncio.run(main())

##################### CYPHER QUERY #####################
# CREATE
#   (jim:Developer:Happy {name:'Jim', id:'2bf37261-30bf-4de5-bcdf-28b579c9fe02'}),
#   (martin:Developer:RegretsLifeDecisions {name:'Martin', id:'b4c2b7e0-eeb1-4b9e-9e4c-6e9c9f1f8d8a'}),
#   (phil:Developer:Happy {name:'Phil', id:'c2b7e0b4-eeb1-4b9e-9e4c-6e9c9f1f8d8a'}),
#   (thomas:Developer:Happy {name:'Thomas', id:'b7e0b4c2-eeb1-4b9e-9e4c-6e9c9f1f8d8a'}),
#   (salli:Developer:Happy {name:'Salli', id:'e0b4c2b7-eeb1-4b9e-9e4c-6e9c9f1f8d8a'}),
#   (project_one:Project {name:'Project One', deadline:'2022-01-01T12:00:00Z', metadata: '{\"awesome\": true}', milestones: ['{\"name\": \"That hard thing done\", \"timestamp\": 1691696518}']}),
#   (project_two:Project {name:'Project Two', deadline:'2022-04-23T16:45:00Z', metadata: '{}', milestones: ['{\"name\": \"Finished talking with important person\", \"timestamp\": 1691825684}', '{\"name\": \"Got copilot to do the work for me\", \"timestamp\": 1691682690}']}),
#   (macchiato:Coffee {flavour:'Macchiato', origin:'Italy'}),
#   (espresso:Coffee {flavour:'Espresso', origin:'Colombia'}),
#   (dark_roast:Coffee {flavour:'Dark Roast', origin:'Brazil'}),
#   (jim)-[:WORKS_ON {role:'Lead'}]->(project_one),
#   (jim)-[:WORKS_ON {role:'Developer'}]->(project_two),
#   (martin)-[:WORKS_ON {role:'Developer'}]->(project_one),
#   (phil)-[:WORKS_ON {role:'Intern'}]->(project_two),
#   (salli)-[:WORKS_ON {role:'Lead'}]->(project_two),
#   (thomas)-[:WORKS_ON {role:'Developer'}]->(project_two),
#   (jim)-[:IMPLEMENTED {name:'Implemented the thing', amount_of_bugs: 3}]->(project_one),
#   (jim)-[:IMPLEMENTED {name:'Some more things', amount_of_bugs: 5}]->(project_one),
#   (jim)-[:IMPLEMENTED {name:'Something veeeery important', amount_of_bugs: 0}]->(project_two),
#   (martin)-[:IMPLEMENTED {name:'Implemented the other thing', amount_of_bugs: 29}]->(project_one),
#   (salli)-[:IMPLEMENTED {name:'Serious work', amount_of_bugs: 7}]->(project_two),
#   (martin)-[:HATED_BY]->(jim),
#   (martin)-[:HATED_BY]->(phil),
#   (martin)-[:HATED_BY]->(thomas),
#   (martin)-[:HATED_BY]->(salli),
#   (espresso)-[:CONSUMED_BY]->(jim),
#   (espresso)-[:CONSUMED_BY]->(martin),
#   (dark_roast)-[:CONSUMED_BY]->(phil),
#   (macchiato)-[:CONSUMED_BY]->(phil)
