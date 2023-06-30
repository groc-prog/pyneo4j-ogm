from copy import deepcopy
from typing import Any


class OperantQueryBuilder:
    def _normalize_operant_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
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
                    if operant == "$not" or not operant.startswith("$"):
                        normalized[operant] = {"$eq": value}

            if len(normalized.keys()) > 1:
                # If more than one operator is defined in a dict, transform operants to `$and` operant
                normalized = [{operant: expression} for operant, expression in normalized.items()]

        # Normalize nested operants
        if isinstance(normalized, list):
            for index, expression in enumerate(normalized):
                normalized[index] = self._normalize_operant_filters(expression)
        elif isinstance(normalized, dict):
            for operant, expression in normalized.items():
                normalized[operant] = self._normalize_operant_filters(expression)

        return normalized


test_filter = {
    "a": {"$gt": 1, "$lt": 4, "$not": 3},
    "b": 20,
    "c": {"$not": {"$in": [1, 2, 3, 4]}},
    "$elementId": "sahfkahkfkauefhaef",
    "d": {"$or": [{"$not": 10}, {"$and": [{"$gte": 20}, {"$lte": 30}]}]},
    "e": {"$exists": True},
}

builder = OperantQueryBuilder()
normalized = builder._normalize_operant_filters(test_filter)
print("DONE")

# BASIC
# $eq =
# $gt >
# $gte >=
# $lt <
# $lte <=
# $regex =~

# TEXT
# $startsWith STARTS
# $endsWith ENDS
# $contains CONTAINS

# ARRAY
# $in IN
# $all ALL(item IN [] WHERE item in node.prop)
# $size SIZE(n.prop)

# LOGICAL
# $not NOT()
# $and (exp1 AND exp2 AND exp3)
# $or (exp1 OR exp2 OR exp3)
# $xor (exp1 XOR exp2 XOR exp3)

# ELEMENT
# $exists NOT NULL

# NEO4J
# $label (n:L1:L2:L3)
# $type (r:T1)
# $elementId elementId(n)=elementid
# $id ID(n)=id
