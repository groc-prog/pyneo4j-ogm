from neo4j_ogm.query_builder import QueryBuilder

builder = QueryBuilder()

test_query = {
    # "field1": 1,
    # "field2": {"$eq": 2},
    # "field3": {"$contains": 3},
    # "$elementId": 4,
    # "$id": 5,
    # "field7": {"$not": {"$gt": 12}},
    # "field8": {"$or": [{"$eq": 8, "$gt": 9, "$lte": 30}, {"ne": 20}]},
    # "field9": {"$not": {"$exists": {}}},
    # "field10": {"$size": 1},
    "field11": {"$size": {"$gte": 12}},
}

build_query, build_parameters = builder.build(test_query)
print("DONE")
