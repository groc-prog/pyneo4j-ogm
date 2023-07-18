from neo4j_ogm.queries.query_builder import QueryBuilder

builder = QueryBuilder()

expressions = {
    #     "$elementId": 12,
    #     "$patterns": [
    #         {
    #             "$node": {"$labels": ["A", "B"], "a": 12, "b": {"eq": 1}, "$id": 1},
    #             "$direction": "INCOMING",
    #             "$relationship": {"$types": ["C", "D"], "a": 2, "b": {"eq": 2}, "$id": 2},
    #         }
    #     ],
    #     "a": 3,
    #     "b": {"eq": 3},
    #     "$labels": ["D"],
}

match_query, where_query, parameters = builder.build_node_expressions(expressions=expressions)

print("DONE")
