"""
This module provides a helper class for converting filter expressions used in methods like `update_one` or
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

COMBINED_OPERANTS: dict[str, Any] = {
    "$and": "AND",
    "$or": "OR",
    "$xor": "XOR",
}


class QueryBuilder:
    """
    Helper class for building `WHERE` clauses based in the provided filter expressions.
    """

    parameters: dict[str, Any] = {}
    property_name: str = ""
    queries: list[str] = []
    ref: str = ""

    def build_operant_query(self, ref: str, filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Builds a `WHERE` clauses with the given operants in the filters.

        Args:
            ref (str): The ref to use for the entity the filters are applied on
            filters (dict[str, Any]): The filters containing expressions

        Returns:
            tuple[str, dict[str, Any]]: The complete query string and the query parameters
        """
        parsed_filters = deepcopy(filters)
        self.parameters = {}
        self.queries = []
        self.ref = ref

        # Replace $eq shorthand with operant so all top-level expressions can be treated the same
        for property_name, expression_or_value in parsed_filters.items():
            if not isinstance(expression_or_value, dict):
                parsed_filters[property_name] = {"$eq": expression_or_value}

        for property_name, expression in parsed_filters.items():
            self.property_name = property_name

            for operant, expression_or_value in expression.items():
                query = ""
                parameter = {}

                # Build partial query string based on the operant
                if operant in BASIC_OPERANTS:
                    query, parameter = self._build_basic_operant(operant, expression_or_value)
                elif operant in COMBINED_OPERANTS:
                    query, parameter = self._build_combined_operant(operant, expression_or_value)
                elif operant == "$element_id":
                    query = self._build_element_id_operant(expression_or_value)
                elif operant == "$exists":
                    query = self._build_exists_operant(expression_or_value)
                elif operant == "$not":
                    query, parameter = self._build_not_operant(expression_or_value)
                else:
                    # If no operant is defined, treat it as `$eq` expression
                    query, parameter = self._build_basic_operant("$eq", expression_or_value)

                self.queries.append(query)
                self.parameters = {**self.parameters, **parameter}

        # Build final query string
        query = f"{' AND '.join(self.queries)}"
        return query, self.parameters

    def _build_basic_operant(
        self, operant: str, value: Any, parameter_prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds partial query strings with basic operants.

        Args:
            operant (str): The operant to use for the query
            value (Any): The value used with the operant
            parameter_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined expressions to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the basic operant
        """
        parameter: dict[str, Any] = {}

        parameter_name = (
            f"{self.property_name}__{operant[1:]}"
            if parameter_prefix is None
            else f"{self.property_name}__{parameter_prefix}_{operant[1:]}"
        )

        query = f"{self.ref}.{self.property_name} {BASIC_OPERANTS[operant]} ${parameter_name}"
        parameter[parameter_name] = value

        return query, parameter

    def _build_element_id_operant(
        self, element_id: str, parameter_prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds a element id query.

        Args:
            element_id (str): The element id to filter by
            parameter_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined expressions to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the `$element_id` operant
        """
        parameter: dict[str, Any] = {}

        parameter_name = (
            f"{self.property_name}__element_id"
            if parameter_prefix is None
            else f"{self.property_name}__{parameter_prefix}_element_id"
        )

        query = f"elementId({self.ref}) = ${parameter_name}"
        parameter[parameter_name] = element_id

        return query, parameter

    def _build_exists_operant(self, exists: bool) -> str:
        """
        Builds the special `$exists` query.

        Args:
            exists (bool): If the query should be created with `IS NOT NULL` or `IS NULL`

        Returns:
            str: The partial query
        """
        return f"{self.ref}.{self.property_name} IS NOT NULL" if exists else f"{self.ref}.{self.property_name} IS NULL"

    def _build_not_operant(self, value: Any, parameter_prefix: str | None = None) -> tuple[str, dict[str, Any]]:
        """
        Builds a `$not` query.

        Args:
            value (Any): The query operator dictionary
            parameter_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined expressions to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the `$not` operant
        """
        # Only first key-value pair is used
        operant, operant_value = next(iter(cast(dict, value).items()))  #

        prefix = f"{parameter_prefix}_not" if parameter_prefix is not None else "not"
        # Build basic operant
        basic_operant_query, basic_operant_parameter = self._build_basic_operant(
            operant, operant_value, parameter_prefix=prefix
        )

        query = f"NOT ({basic_operant_query})"
        return query, basic_operant_parameter

    def _build_combined_operant(
        self, operant: str, expressions: list[dict[str, Any]], parameter_prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds a combined operant.

        Args:
            operant (str): Operant type to build
            expressions (list[dict[str, Any]]): The expressions nested inside the combined operant
            parameter_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined expressions to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the combined operant
        """
        prefix = f"{parameter_prefix}_{operant[1:]}" if parameter_prefix is not None else operant[1:]
        queries = []
        parameters = {}

        for operant_type in expressions:
            for operant_name, operant_value in operant_type.items():
                query = ""
                parameter = {}

                # Check all possible options again because combined operants can include all other operants
                if operant_name in BASIC_OPERANTS:
                    query, parameter = self._build_basic_operant(operant_name, operant_value, prefix)
                elif operant_name == "$element_id":
                    query = self._build_element_id_operant(operant_value, prefix)
                elif operant_name == "$exists":
                    query = self._build_exists_operant(operant_value)
                elif operant_name == "$not":
                    query, parameter = self._build_not_operant(operant_value, prefix)
                elif operant_name in COMBINED_OPERANTS:
                    query, parameter = self._build_combined_operant(operant_name, operant_value, prefix)
                else:
                    query, parameter = self._build_basic_operant("$eq", operant_value, prefix)

                queries.append(query)
                parameters = {**parameters, **parameter}

        query = f"({f' {COMBINED_OPERANTS[operant]} '.join(queries)})"
        return query, parameters
