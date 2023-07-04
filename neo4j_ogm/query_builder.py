"""
COMPARISON OPERATORS
$eq
$ne
$gt
$gte
$lt
$lte
$in
$nin
$contains
$startsWith
$endsWith
$regex

LOGICAL OPERATORS
$and
$or
$xor
$not
$all

ELEMENT OPERATORS
$exists

ARRAY OPERATORS
$size
"""


from copy import deepcopy
from typing import Any


class QueryBuilder:
    __comparison_operator: dict[str, str] = {
        "$eq": "{property_name} = {value}",
        "$ne": "NOT({property_name} = {value})",
        "$gt": "{property_name} > {value}",
        "$gte": "{property_name} >= {value}",
        "$lt": "{property_name} < {value}",
        "$lte": "{property_name} <= {value}",
        "$in": "{value} IN {property_name}",
        "$nin": "NOT({value} IN {property_name})",
        "$contains": "{property_name} CONTAINS {value}",
        "$startsWith": "{property_name} STARTS WITH {value}",
        "$endsWith": "{property_name} ENDS WITH {value}",
        "$regex": "{property_name} =~ {value}",
    }
    __logical_operator: dict[str, str] = {"$and": "AND", "$or": "OR", "$xor": "XOR"}
    __neo4j_operator: dict[str, str] = {"$elementId": "elementId({ref}) = {value}", "$id": "ID({ref}) = {value}"}
    __element_operator: dict[str, str] = {"$exists": "{property_name} IS NOT NULL"}
    ref: str
    property_name: str

    def build(self, query: dict[str, Any], ref: str = "n") -> tuple[str, dict[str, Any]]:
        normalized_expressions = self._normalize_expressions(query=query)
        self.ref = ref

        return self._build_nested_expressions(normalized_expressions)

    def _build_nested_expressions(
        self, expressions: dict[str, Any], level: int = 0, prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        partial_queries: list[str] = []
        complete_parameters: dict[str, Any] = {}

        for property_or_operator, expression_or_value in expressions.items():
            query = ""
            parameters = {}

            if not property_or_operator.startswith("$"):
                self.property_name = property_or_operator

            if level == 0 and property_or_operator.startswith("$"):
                query, parameters = self._build_neo4j_operator(property_or_operator, expression_or_value)
            elif property_or_operator == "$not":
                query, parameters = self._build_not_operator(expression=expression_or_value)
            elif property_or_operator == "$size":
                query, parameters = self._build_size_operator(expression=expression_or_value, prefix=prefix)
            elif property_or_operator in self.__comparison_operator:
                query, parameters = self._build_comparison_operator(
                    operator=property_or_operator, value=expression_or_value, prefix=prefix
                )
            elif property_or_operator in self.__element_operator:
                query, parameters = self._build_element_operator(operator=property_or_operator)
            elif property_or_operator in self.__logical_operator:
                query, parameters = self._build_logical_operator(
                    operator=property_or_operator,
                    expressions=expression_or_value,
                    prefix=prefix,
                )
            elif not property_or_operator.startswith("$"):
                query, parameters = self._build_nested_expressions(
                    expressions=expression_or_value, level=level + 1, prefix=prefix
                )

            partial_queries.append(query)
            complete_parameters = {**complete_parameters, **parameters}

        complete_query = " AND ".join(partial_queries)
        return complete_query, complete_parameters

    def _build_comparison_operator(
        self, operator: str, value: Any, prefix: str | None = None, property_name_overwrite: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        parameter_name = self._build_parameter_name(operator=operator, prefix=prefix)
        parameters = {}

        query = self.__comparison_operator[operator].format(
            property_name=property_name_overwrite if property_name_overwrite else f"{self.ref}.{self.property_name}",
            value=f"${parameter_name}",
        )
        parameters[parameter_name] = value

        return query, parameters

    def _build_element_operator(self, operator: str) -> tuple[str, dict[str, Any]]:
        parameters = {}

        query = self.__element_operator[operator].format(property_name=f"{self.ref}.{self.property_name}")
        return query, parameters

    def _build_not_operator(self, expression: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        parameter_name = self._build_parameter_name(operator="$not")
        expression, complete_parameters = self._build_nested_expressions(
            expressions=expression, level=1, prefix=parameter_name
        )

        complete_query = f"NOT({expression})"
        return complete_query, complete_parameters

    def _build_size_operator(self, expression: dict[str, Any], prefix: str | None = None) -> tuple[str, dict[str, Any]]:
        comparison_operator = next(iter(expression))
        parameter_name = self._build_parameter_name(operator="$size", prefix=prefix)

        query, parameters = self._build_comparison_operator(
            operator=comparison_operator,
            value=expression[comparison_operator],
            property_name_overwrite=f"SIZE({self.ref}.{self.property_name})",
            prefix=parameter_name,
        )

        return query, parameters

    def _build_logical_operator(
        self, operator: str, expressions: list[dict[str, Any]], prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        partial_queries: list[str] = []
        complete_parameters: dict[str, Any] = {}

        for expression in expressions:
            parameter_name = self._build_parameter_name(operator=operator, prefix=prefix)
            nested_query, parameters = self._build_nested_expressions(
                expressions=expression, level=1, prefix=parameter_name
            )

            partial_queries.append(nested_query)
            complete_parameters = {**complete_parameters, **parameters}

        complete_query = f"({f' {self.__logical_operator[operator]} '.join(partial_queries)})"
        return complete_query, complete_parameters

    def _build_neo4j_operator(self, operator: str, value: Any) -> tuple[str, dict[str, Any]]:
        parameter_name = self._build_parameter_name(operator=operator)
        parameters = {}

        query = self.__neo4j_operator[operator].format(ref=self.ref, value=f"${parameter_name}")
        parameters[parameter_name] = value

        return query, parameters

    def _build_parameter_name(self, operator: str, prefix: str | None = None) -> str:
        if prefix:
            return f"{prefix}_{operator[1:]}"

        return f"{self.ref}_{self.property_name}__{operator[1:]}"

    def _normalize_expressions(self, query: dict[str, Any], level: int = 0) -> dict[str, Any]:
        normalized: dict[str, Any] = deepcopy(query)

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
                normalized[index] = self._normalize_expressions(expression, level + 1)
        elif isinstance(normalized, dict):
            for operant, expression in normalized.items():
                normalized[operant] = self._normalize_expressions(expression, level + 1)

        return normalized
