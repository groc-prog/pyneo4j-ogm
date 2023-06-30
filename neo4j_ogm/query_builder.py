from copy import deepcopy
from typing import Any, cast

BASIC_OPERANTS = {
    "$eq": "{prop} = ${val}",
    "$gt": "{prop} > ${val}",
    "$gte": "{prop} >= ${val}",
    "$lt": "{prop} < ${val}",
    "$lte": "{prop} <= ${val}",
    "$regex": "{prop} =~ ${val}",
    "$in": "{prop} IN ${val}",
    "$all": "ALL(i IN ${val} WHERE i IN {prop})",
    "$startsWith": "{prop} STARTS WITH {val}",
    "$endsWith": "{prop} ENDS WITH {val}",
    "$contains": "{prop} CONTAINS {val}",
}

LOGICAL_OPERANTS = {
    "$and": "AND",
    "$or": "OR",
    "$xor": "XOR",
}

NEO4J_OPERANTS = {"$elementId": "elementId({ref}) = ${val}", "$id": "ID({ref}) = ${val}"}


class OperantQueryBuilder:
    ref: str = "n"
    property_name: str

    def build_query(self, expressions: dict[str, Any], prefix: str | None = None) -> tuple[str, dict[str, Any]]:
        operant_queries: list[str] = []
        operant_parameters: dict[str, Any] = {}

        if isinstance(expressions, dict):
            for operant_or_property, expression_or_value in expressions.items():
                if operant_or_property in NEO4J_OPERANTS:
                    # Build special Neo4j operants
                    parameter_name = self._build_parameter_name(operant_or_property, "_")

                    operant_queries.append(NEO4J_OPERANTS[operant_or_property].format(ref=self.ref, val=parameter_name))
                    operant_parameters[parameter_name] = expression_or_value
                elif operant_or_property in BASIC_OPERANTS:
                    # Build Basic operants, no more nesting possible at this point
                    parameter_name = self._build_parameter_name(operant_or_property, prefix)

                    operant_queries.append(
                        BASIC_OPERANTS[operant_or_property].format(
                            prop=f"{self.ref}.{self.property_name}", val=parameter_name
                        )
                    )
                    operant_parameters[parameter_name] = expression_or_value
                elif operant_or_property == "$not":
                    # Build nested operants inside `$not`
                    parameter_name = self._build_parameter_name(operant_or_property, prefix)

                    nested_query, parameters = self.build_query(expression_or_value, parameter_name)

                    operant_queries.append(f"NOT ({nested_query})")
                    operant_parameters = {**operant_parameters, **parameters}
                elif operant_or_property == "$exists":
                    # Handle `$exists` separately because it does not have parameters
                    query = (
                        f"{self.ref}.{self.property_name} IS NOT NULL"
                        if expression_or_value
                        else f"{self.ref}.{self.property_name} IS NULL"
                    )
                    operant_queries.append(query)
                else:
                    # Recursion is at top level, can only be a property
                    self.property_name = operant_or_property
                    query, parameters = self.build_query(expression_or_value)

                    operant_queries.append(query)
                    operant_parameters = {**operant_parameters, **parameters}

            complete_query = " AND ".join(operant_queries)
            return complete_query, operant_parameters

    def _build_parameter_name(self, operant: str, prefix: str | None = None) -> str:
        return f"{prefix}_{operant[1:]}" if prefix else f"{self.property_name}__{operant[1:]}"

    def _normalize_operant_filters(self, filters: dict[str, Any], level: int = 0) -> dict[str, Any]:
        """
        Normalizes the operants inside a given filter.

        Args:
            filters (dict[str, Any]): The filter to normalize

        Returns:
            dict[str, Any]: The normalized filter
        """
        normalized: dict[str, Any] = deepcopy(filters)

        if isinstance(normalized, dict):
            # Transform values without a operant to a `$eq` operant
            for operant, value in normalized.items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    # If the operator is a `$not` operant or just a property name, add a `$eq` operant
                    if operant in ["$not", "$size"] or not operant.startswith("$"):
                        normalized[operant] = {"$eq": value}

            if len(normalized.keys()) > 1 and level > 0:
                # If more than one operator is defined in a dict, transform operants to `$and` operant
                normalized = {"$and": [{operant: expression} for operant, expression in normalized.items()]}

        # Normalize nested operants
        if isinstance(normalized, list):
            for index, expression in enumerate(normalized):
                normalized[index] = self._normalize_operant_filters(expression, level + 1)
        elif isinstance(normalized, dict):
            for operant, expression in normalized.items():
                normalized[operant] = self._normalize_operant_filters(expression, level + 1)

        return normalized


test_filter = {
    "g": {"$size": 12},
    # "a": {"$gt": 1, "$lt": 4, "$not": 3},
    # "i": {"$not": 12},
    # "b": 20,
    # "c": {"$not": {"$in": [1, 2, 3, 4]}},
    # "$elementId": "SOME_ELEMENT_ID",
    # # "d": {"$or": [{"$not": 10}, {"$and": [{"$gte": 20}, {"$lte": 30}]}]},
    # "e": {"$exists": False},
    # "f": {"$all": [1, 2, 3, 4]},
    # "h": {"$gte": 40},
}

builder = OperantQueryBuilder()
normalized_filters = builder._normalize_operant_filters(test_filter)
result = builder.build_query(normalized_filters)
print("DONE")

# BASIC
# $eq n.prop = val
# $gt n.prop > val
# $gte n.prop >= val
# $lt n.prop < val
# $lte n.prop <= val
# $regex n.prop =~ val

# TEXT
# $startsWith n.prop STARTS WITH val
# $endsWith n.prop ENDS WITH val
# $contains n.prop CONTAINS val

# ARRAY
# $in n.prop IN val
# $all ALL(item IN val WHERE item in n.prop)
# $size SIZE(n.prop) = val

# LOGICAL
# $not NOT(exp)
# $and (exp1 AND exp2 AND exp3)
# $or (exp1 OR exp2 OR exp3)
# $xor (exp1 XOR exp2 XOR exp3)

# ELEMENT
# $exists NOT NULL

# NEO4J
# $elementId elementId(n)=val
# $id ID(n)=val
