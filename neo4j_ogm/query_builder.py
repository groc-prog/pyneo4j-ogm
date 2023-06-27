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

COMBINED_OPERANTS: dict[str, Any] = {
    "$and": "AND",
    "$or": "OR",
    "$xor": "XOR",
}


class QueryBuilder:
    """
    Helper class for building `WHERE` clauses based in the provided filter operants.
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
            filters (dict[str, Any]): The filters containing the operants

        Returns:
            tuple[str, dict[str, Any]]: The complete query string and the query parameters
        """
        parsed_filters = deepcopy(filters)
        self.parameters = {}
        self.queries = []
        self.ref = ref

        # Replace $eq shorthand with operant so all top-level operants can be treated the same
        for property_name, operants_or_value in parsed_filters.items():
            if not isinstance(operants_or_value, dict):
                parsed_filters[property_name] = {"$eq": operants_or_value}

        for property_name, operants in parsed_filters.items():
            self.property_name = property_name

            for operant_name, operant_value in operants.items():
                query = ""
                parameter = {}

                # Build partial query string based on the operant type
                if operant_name in BASIC_OPERANTS:
                    query, parameter = self._build_basic_operant(operant_name, operant_value)
                elif operant_name in COMBINED_OPERANTS:
                    query, parameter = self._build_combined_operant(operant_name, operant_value)
                elif operant_name == "$exists":
                    query = self._build_exists_operant(operant_value)
                elif operant_name == "$not":
                    query, parameter = self._build_not_operant(operant_value)
                else:
                    # If not operant is defined, treat it as `$eq` operant
                    query, parameter = self._build_basic_operant("$eq", operant_value)

                self.queries.append(query)
                self.parameters = {**self.parameters, **parameter}

        # Build final query string
        query = f"{' AND '.join(self.queries)}"
        return query, self.parameters

    def _build_basic_operant(
        self, operant_type: str, operant_value: Any, param_prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds partial query strings with basic operants.

        Args:
            operant_type (str): The type of operant to use for the query
            operant_value (Any): The value applied used with the operant
            param_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined operants to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the basic operant
        """
        parameter: dict[str, Any] = {}

        parameter_name = (
            f"{self.property_name}__{operant_type[1:]}"
            if param_prefix is None
            else f"{self.property_name}__{param_prefix}_{operant_type[1:]}"
        )

        query = f"{self.ref}.{self.property_name} {BASIC_OPERANTS[operant_type]} ${parameter_name}"
        parameter[parameter_name] = operant_value

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

    def _build_not_operant(self, operant_value: Any, param_prefix: str | None = None) -> tuple[str, dict[str, Any]]:
        """
        Builds a `$not` query.

        Args:
            operant_value (Any): The query operator dictionary
            param_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined operants to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the `$not` operant
        """
        # Only first key-value pair is used
        not_operant_type, not_operator_value = next(iter(cast(dict, operant_value).items()))  #

        prefix = f"{param_prefix}_not" if param_prefix is not None else "not"
        # Build basic operant
        basic_operant_query, basic_operant_parameter = self._build_basic_operant(
            not_operant_type, not_operator_value, param_prefix=prefix
        )

        query = f"NOT ({basic_operant_query})"
        return query, basic_operant_parameter

    def _build_combined_operant(
        self, operant_type: str, operants: list[dict[str, Any]], param_prefix: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        Builds a combined operant.

        Args:
            operant_type (str): Operant type to build
            operants (list[dict[str, Any]]): The operants nested inside the combined operant
            param_prefix (str | None, optional): A optional prefix to use for the parameter. Needed
                for combined operants to prevent duplicate parameters. Defaults to None.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters for the combined operant
        """
        prefix = f"{param_prefix}_{operant_type[1:]}" if param_prefix is not None else operant_type[1:]
        queries = []
        parameters = {}

        for operant in operants:
            for operant_name, operant_value in operant.items():
                query = ""
                parameter = {}

                # Check all possible options again because combined operants can include all other operants
                if operant_name in BASIC_OPERANTS:
                    query, parameter = self._build_basic_operant(operant_name, operant_value, prefix)
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

        query = f"({f' {COMBINED_OPERANTS[operant_type]} '.join(queries)})"
        return query, parameters
