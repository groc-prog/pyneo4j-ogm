# import asyncio
# import logging

# logging.basicConfig(level=logging.DEBUG)

# from neo4j_ogm import Neo4jClient
# from tests.models import Actor, Actress, Friends, WorkedTogether


# def hook(*args, **kwargs):
#     print("HOOK")


# async def main():
#     client = Neo4jClient().connect("bolt://localhost:7687", ("neo4j", "password"))

#     await client.drop_indexes()
#     await client.drop_constraints()
#     await client.drop_nodes()
#     await client.register_models([Actress, Actor, WorkedTogether, Friends])

#     Actress.register_post_hooks("create", hook)

#     async with client.batch():
#         scarlett = await Actress(name="Scarlett Johansson", age=35).create()
#         gal = await Actress(name="Gal Gadot", age=29).create()
#         margot = await Actress(name="Margot Robbie", age=39).create()
#         arnold = await Actor(name="Arnold Schwarzenegger", age=31).create()
#         robert = await Actor(name="Robert Downey Jr", age=34).create()
#         henry = await Actor(name="Henry Cavil", age=41).create()

#     print("DONE")


# asyncio.run(main())


from neo4j_ogm.queries.query_builder import QueryBuilder

builder = QueryBuilder()

builder.relationship_property_filters({"$relationship": {"name": "foo"}, "age": 12})

print("DONE")
