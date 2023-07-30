"""
This module contains a class for building parts of the database query.
"""
from copy import deepcopy
from typing import Any, Dict, List, Optional, TypedDict

from neo4j_ogm.queries.types import NodeFilters, QueryDataTypes, RelationshipFilters
from neo4j_ogm.queries.validators import NodeFiltersModel, RelationshipFiltersModel


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
    }
    _property_name: Optional[str] = None
    _property_var_overwrite: Optional[str] = None
    ref: str
    parameters: Dict[str, QueryDataTypes] = {}
    query: FilterQueries = {}

    def node_filters(self, filters: NodeFilters, ref: str = "n") -> None:
        """
        Builds the node filters for the query.

        Args:
            filters (Dict[str, Any]): The filters to build.
        """
        self.ref = ref
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = NodeFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True, exclude_unset=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        self.query["where"] = self._build_query(filters=validated_filters)

    def relationship_filters(self, filters: RelationshipFilters, ref: str = "r") -> None:
        """
        Builds the relationship filters for the query.

        Args:
            filters (Dict[str, Any]): The filters to build.
        """
        self.ref = ref
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = RelationshipFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True, exclude_unset=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        self.query["where"] = self._build_query(filters=validated_filters)

    def _build_query(self, filters: Dict[str, Any]) -> str:
        where_queries: List[str] = []

        for property_or_operator, expression_or_value in filters.items():
            # Set the property name here so it can be used in the operators
            if not property_or_operator.startswith("$"):
                self._property_name = property_or_operator

            match property_or_operator:
                case operator if operator in self._operators.keys():
                    param_var = self._build_param_var()
                    self.parameters[param_var] = expression_or_value

                    where_query = self._operators[operator].format(
                        property_var=self._build_property_var(), param_var=param_var
                    )
                    where_queries.append(where_query)
                case "$and":
                    where_queries.append(self._and_operator(expressions=expression_or_value))
                case "$or":
                    where_queries.append(self._or_operator(expressions=expression_or_value))
                case "$xor":
                    where_queries.append(self._xor_operator(expressions=expression_or_value))
                case "$elementId":
                    where_queries.append(self._element_id_operator(element_id=expression_or_value))
                case "$id":
                    where_queries.append(self._id_operator(id_=expression_or_value))
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

    def _normalize_expressions(self, expressions: Dict[str, Any], level: int = 0) -> Dict[str, Any]:
        """
        Normalizes and formats the provided expressions into usable expressions for the builder.

        Args:
            expressions (Dict[str, Any]): The expressions to normalize
            level (int, optional): The recursion depth level. Should not be modified outside the
                function itself. Defaults to 0.

        Returns:
            Dict[str, Any]: The normalized expressions.
        """
        normalized: Dict[str, Any] = deepcopy(expressions)

        if isinstance(normalized, dict):
            # Transform values without a operator to a `$eq` operator
            for operator, value in normalized.items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    # If the operator is a `$not` operator or just a property name, add a `$eq`
                    # operator
                    if operator in ["$not", "$size"] or not operator.startswith("$"):
                        normalized[operator] = {"$eq": value}

            if len(normalized.keys()) > 1 and level > 0:
                # If more than one operator is defined in a dict, transform operators to `$and`
                # operator
                normalized = {"$and": [{operator: expression} for operator, expression in normalized.items()]}

        # Normalize nested operators
        if isinstance(normalized, list):
            for index, expression in enumerate(normalized):
                normalized[index] = self._normalize_expressions(expression, level + 1)
        elif isinstance(normalized, dict):
            for operator, expression in normalized.items():
                normalized[operator] = self._normalize_expressions(expression, level + 1)

        return normalized

    def _remove_invalid_expressions(self, expressions: Dict[str, Any], level: int = 0) -> None:
        """
        Recursively removes empty objects and nested fields which do not start with a `$` and are
        not top level keys from nested dictionaries and lists.

        Args:
            expressions (Dict[str, Any]): The expression to check.
            level (int, optional): The recursion depth level. Should not be modified outside the
                function itself. Defaults to 0.
        """
        operators_to_remove: List[str] = []

        if not isinstance(expressions, dict):
            return

        for operator, expression in expressions.items():
            if isinstance(expression, dict):
                # Search through all operators nested within
                self._remove_invalid_expressions(expressions=expression, level=level + 1)

                if not expression:
                    operators_to_remove.append(operator)
            elif isinstance(expression, list):
                # Handle logical operators
                indexes_to_remove: List[str] = []

                for index, nested_expression in enumerate(expression):
                    # Search through all operators nested within
                    self._remove_invalid_expressions(expressions=nested_expression, level=level + 1)

                    if not nested_expression:
                        indexes_to_remove.append(index)

                # Remove all invalid indexes
                for index in indexes_to_remove:
                    expression.pop(index)
            elif not operator.startswith("$") and level != 0:
                operators_to_remove.append(operator)

        for operator in operators_to_remove:
            expressions.pop(operator)

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

    def _id_operator(self, id_: str) -> str:
        """
        Builds the query for the `$id` operator.

        Args:
            id_ (str): The ID to match by.

        Returns:
            str: The operator query.
        """
        param_var = self._build_param_var()
        self.parameters[param_var] = id_

        return f"ID({self.ref}) = ${param_var}"

    def _element_id_operator(self, element_id: str) -> str:
        """
        Builds the query for the `$elementId` operator.

        Args:
            element_id (str): The element ID to match by.

        Returns:
            str: The operator query.
        """
        param_var = self._build_param_var()
        self.parameters[param_var] = element_id

        return f"elementId({self.ref}) = ${param_var}"

    def _and_operator(self, expressions: Dict[str, Any]) -> str:
        """
        Builds the query for the `$and`  operator.

        Args:
            expressions (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        and_queries: List[str] = []

        for expression in expressions:
            and_queries.append(self._build_query(filters=expression))

        return f"({' AND '.join(and_queries)})"

    def _or_operator(self, expressions: Dict[str, Any]) -> str:
        """
        Builds the query for the `$or`  operator.

        Args:
            expressions (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        or_queries: List[str] = []

        for expression in expressions:
            or_queries.append(self._build_query(filters=expression))

        return f"({' OR '.join(or_queries)})"

    def _xor_operator(self, expressions: Dict[str, Any]) -> str:
        """
        Builds the query for the `$xor`  operator.

        Args:
            expressions (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        xor_queries: List[str] = []

        for expression in expressions:
            xor_queries.append(self._build_query(filters=expression))

        return f"({' XOR '.join(xor_queries)})"

    def _build_param_var(self) -> str:
        """
        Builds a new parameter variable name. This method exists to ensure no duplicate variable
        names occur when using the builder.

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
