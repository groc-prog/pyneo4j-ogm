"""
This module provides a helper class for converting property filters used in methods like `update_one` or
`find_many` into their corresponding cypher queries.
"""
from copy import deepcopy
from typing import Any, cast

BASIC_OPERANTS: dict[str, Any] = {
    "$eq": "=",
    "$gt": ">",
    "$gte": ">=",
    "$lt": "<",
    "$lte": "<=",
    "$in": "IN",
    "$starts_with": "STARTS WITH",
    "$ends_with": "ENDS WITH",
    "$contains": "CONTAINS",
    "$regex": "=~",
}

COMBINED_OPERANTS: list[str] = [
    "$and",
    "$or",
    "$xor",
]


class QueryBuilder:
    ref: str = ""
    parameters: dict[str, Any] = {}
    queries: list[str] = []

    def build_operant_queries(self, ref: str, filters: dict[str, Any]) -> str:
        parsed_filters = deepcopy(filters)
        self.parameters = {}
        self.queries = []
        self.ref = ref

        # Replace $eq shorthand with operant so all top-level operants can be treated the same
        for property_name, operants_or_value in parsed_filters.items():
            if not isinstance(operants_or_value, dict):
                parsed_filters[property_name] = {"$eq": operants_or_value}

        for property_name, operants in parsed_filters.items():
            for operant_name, operant_value in operants.items():
                query, parameter = self._build_operant(property_name, operant_name, operant_value)

                self.queries.append(query)
                self.parameters = {**self.parameters, **parameter}

        query = f"WHERE {' AND '.join(self.queries)}"
        return query, self.parameters

    def _build_operant(
        self, property_name: str, operant_name: str, operant_value: Any, param_prefix: str | None = None
    ):
        parameter: dict[str, Any] = {}
        query = ""

        if operant_name in BASIC_OPERANTS:
            parameter_name = (
                f"{property_name}_{operant_name[1:]}"
                if param_prefix is None
                else f"{property_name}_{param_prefix}_{operant_name[1:]}"
            )
            query = f"{self.ref}.{property_name} {BASIC_OPERANTS[operant_name]} ${parameter_name}"
            parameter[parameter_name] = operant_value
        elif operant_name == "$not":
            not_operant_name, not_operator_value = next(iter(cast(dict, operant_value).items()))
            partial_query, param = self._build_operant(property_name, not_operant_name, not_operator_value, "not")

            query = f"NOT ({partial_query})"
            parameter = param
        elif operant_name == "$exists":
            if operant_value:
                query = f"{self.ref}.{property_name} IS NOT NULL"
            else:
                query = f"{self.ref}.{property_name} IS NULL"
        else:
            parameter_name = f"{property_name}_eq" if param_prefix is None else f"{property_name}_{param_prefix}_eq"
            query = f"{self.ref}.{property_name} {BASIC_OPERANTS['$eq']} ${parameter_name}"
            parameter[parameter_name] = operant_value

        return query, parameter

        # for operant_name, operant_value in operants.items():
        #     # Handle basic operants
        #     if operant_name in BASIC_OPERANTS:
        #         parameter_name = (
        #             f"{property_name}_{operant_name[1:]}"
        #             if param_prefix is None
        #             else f"{property_name}_{param_prefix}_{operant_name[1:]}"
        #         )
        #         query = f"{self.ref}.{property_name} {BASIC_OPERANTS[operant_name]} ${parameter_name}"

        #         self.queries.append(query)
        #         self.parameters[parameter_name] = operant_value
        #     # Handle operants which combine other operants
        #     elif operant_name in COMBINED_OPERANTS:
        #         pass
        #     # Handle special operant `$exists` for property existence checks
        #     elif operant_name == "$not":
        #         self.
        #     elif operant_name == "$exists":
        #         query = (
        #             f"{self.ref}.{property_name} IS NOT NULL"
        #             if operant_value
        #             else f"{self.ref}.{property_name} IS NULL"
        #         )

        #         self.queries.append(query)


test_filter = {
    "prop1": {"$gt": 30},
    "prop2": {"$in": [1, 2, 3]},
    "prop3": {"$contains": "abc"},
    "prop4": 12,
    "prop5": {"$exists": True},
    "prop6": {"$not": {"$lte": 20}},
    # "prop7": {"$and": [{"$starts_with": "foo"}, {"$ends_with": "bar"}]},
}

builder = QueryBuilder()
complete_query, params = builder.build_operant_queries("n", test_filter)
print("DONE")


# WHERE (n.prop4 < 40 AND (n.prop4 > 20 OR n.prop4 = 18))
# WHERE n.prop1 > $prop1_gt AND n.prop2 IN $prop2_in AND n.prop3 STARTS WITH $prop3_starts_with AND (n.prop4 > $prop4_and_gt AND n.prop4 < $prop4_and_lt)

# scaffold = {
#     "property_name": "property_value",
#     "property_filter": {
#         "$eq": "property_value",  # Same as "property_name": "property_value"
#         "$gt": 30,  # value greater than
#         "$gte": 30,  # value greater than or equals
#         "$lt": 30,  # value less than
#         "$lte": 30,  # value less than or equals
#         "$in": [1, 2, 3, 4],  # Value in list
#         "$and": [  # Combination of multiple filters, logical AND
#             {"$lt": 30},
#             {"$gt": 30},
#         ],
#         "$or": [  # logical OR
#             {"$lt": 30},
#             {"$gt": 30},
#         ],
#         "$xor": [  # logical XOR
#             {"$lt": 30},
#             {"$gt": 30},
#         ],
#         "$not": {  # Logical NOT
#             "$lt": 30,  # value less than
#         },
#         "$exists": True,  # Checks IS NOT NULL
#         "$starts_with": "abc",  # checks if string starts with prefix
#         "$ends_with": "abc",  # checks if string ends with suffix
#         "$contains": "abc",  # checks if string contains substring
#         "$regex": "stajfoafe",  # REGEX
#     },
# }
