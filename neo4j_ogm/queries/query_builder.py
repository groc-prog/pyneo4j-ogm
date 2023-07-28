"""
This module contains a class for building parts of the database query.
"""
from typing import Any, Dict, List, Optional, TypedDict

from neo4j_ogm.queries.types import QueryDataTypes


class FilterQueries(TypedDict):
    """
    Type definition for `query` attribute.
    """

    where: List[str]


class QueryBuilder:
    """
    This class builds parts of the database query for available query filters and options.
    """

    _parameter_indent: int = 0
    _operators: Dict[str, str] = {
        "$eq": "{property_var} = ${param_var}",
        "$neq": "{property_var} <> ${param_var}",
        "$gt": "{property_var} > ${param_var}",
        "$gte": "{property_var} >= ${param_var}",
        "$lt": "{property_var} < ${param_var}",
        "$lte": "{property_var} <= ${param_var}",
        "$in": "ANY(i IN {property_var} WHERE i IN ${param_var})",
        "$nin": "NONE(i IN {property_var} WHERE i IN ${param_var})",
        "$all": "ALL(i IN {property_var} WHERE i IN ${param_var})",
        "$contains": "{property_var} CONTAINS ${param_var}",
        "$icontains": "toLower({property_var}) CONTAINS toLower(${param_var})",
        "$startsWith": "{property_var} STARTS WITH ${param_var}",
        "$istartsWith": "toLower({property_var}) STARTS WITH toLower(${param_var})",
        "$endsWith": "{property_var} ENDS WITH ${param_var}",
        "$iendsWith": "toLower({property_var}) ENDS WITH toLower(${param_var})",
        "$regex": "{property_var} =~ ${param_var}",
        "$elementId": "elementId({property_var})",
        "$id": "ID({property_var})",
        "$and": " AND ",
        "$or": " OR ",
        "$xor": " XOR ",
    }
    _property_name: Optional[str] = None
    _property_var_overwrite: Optional[str] = None
    ref: str
    parameters: Dict[str, QueryDataTypes] = {}
    query: FilterQueries = {}

    def _build_query(self, filters: Dict[str, Any]) -> str:
        where_queries: List[str] = []

        for field_or_operator, expression_or_value in filters.items():
            match field_or_operator:
                case operator if operator in self._operators.keys():
                    where_query = self._operators[operator].format(
                        property_var=self._build_property_var(), param_var=self._build_param_var()
                    )
                    where_queries.append(where_query)
                case "$size":
                    where_queries.append(self._size_operator(expression=expression_or_value))
                case "$not":
                    where_queries.append(self._not_operator(expression=expression_or_value))
                case "$exists":
                    where_queries.append(self._exists_operator(exists=expression_or_value))
                case "$labels":
                    where_queries.append(self._labels_operator(labels=expression_or_value))
                case "$type":
                    where_queries.append(self._type_operator(types=expression_or_value))
                case _:
                    where_queries.append(self._build_query(filters=expression_or_value))

        return " AND ".join(where_queries)

    def _size_operator(self, expression: Dict[str, Any]) -> str:
        """
        Builds the query for the `$size` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        self._property_var_overwrite = f"SIZE({self._build_property_var()})"
        size_query = self._build_query(filters=expression)

        self._property_var_overwrite = None
        return size_query

    def _not_operator(self, expression: Dict[str, Any]) -> str:
        """
        Builds the query for the `$not` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        not_query = self._build_query(filters=expression)
        return f"NOT({not_query})"

    def _exists_operator(self, exists: bool) -> str:
        """
        Builds the query for the `$exists` operator.

        Args:
            exists (bool): Whether to match nodes/relationships where the property exists or not.

        Returns:
            str: The operator query.
        """
        if exists:
            return f"{self._build_property_var()} IS NOT NULL"

        return f"{self._build_property_var()} IS NULL"

    def _labels_operator(self, labels: List[str]) -> str:
        """
        Builds the query for the `$labels` operator.

        Args:
            labels (List[str]): Node labels to match by.

        Returns:
            str: The operator query.
        """
        param_var = self._build_param_var()
        self.parameters[param_var] = labels

        return f"ANY(i IN labels({self.ref}) WHERE i IN ${param_var})"

    def _type_operator(self, types: List[str]) -> str:
        """
        Builds the query for the `$type` operator.

        Args:
            types (List[str]): Relationship types to match by.

        Returns:
            str: The operator query.
        """
        param_var = self._build_param_var()
        self.parameters[param_var] = types

        return f"type({self.ref}) IN ${param_var}"

    def _build_param_var(self) -> str:
        """
        Builds a new parameter variable name. This method exists to ensure no duplicate variable names
        occur when using the builder.

        Returns:
            str: The unique variable name.
        """
        param_var = f"n_{self._parameter_indent}"

        self._parameter_indent += 1
        return param_var

    def _build_property_var(self) -> str:
        """
        Returns the node or relationship property to use.

        Returns:
            str: The property to use in the query.
        """
        if self._property_var_overwrite is not None:
            return self._property_var_overwrite

        property_var = f"{self.ref}.{self._property_name}"
        return property_var
