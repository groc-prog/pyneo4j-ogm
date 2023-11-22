"""
Builds query operators from provided filters.
"""
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union, cast


class Operators:
    """
    Builds parts of the query from given operators, which are provided as filters.
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
    ref: str = "n"
    parameters: Dict[str, Union[Any, List[str]]] = {}

    def reset_state(self) -> None:
        self._parameter_indent = 0
        self.parameters = {}

    def build_operators(self, filters: Dict[str, Any]) -> Optional[str]:
        """
        Builds the operators from the provided filters and returns the generated query
        string.

        Args:
            filters (Dict[str, Any]): The filters defining the operators.

        Returns:
            Optional[str]: The query string for the provided filters or `None` if the filter is invalid.
        """
        where_queries: List[str] = []

        if not isinstance(filters, dict):
            return None

        for property_or_operator, expression_or_value in filters.items():
            # Set the property name here so it can be used in the operators
            if not property_or_operator.startswith("$"):
                self._property_name = property_or_operator

            match property_or_operator:
                case operator if operator in [key for key, _ in self._operators.items()]:
                    param_var = self.build_param_var()
                    self.parameters[param_var] = expression_or_value

                    where_query = self._operators[operator].format(
                        property_var=self.build_property_var(), param_var=param_var
                    )
                    where_queries.append(where_query)
                case "$patterns":
                    for pattern in expression_or_value:
                        where_queries.append(self.patterns_operator(expression=pattern))
                case "$and":
                    where_queries.append(self.and_operator(expressions=expression_or_value))
                case "$or":
                    where_queries.append(self.or_operator(expressions=expression_or_value))
                case "$xor":
                    where_queries.append(self.xor_operator(expressions=expression_or_value))
                case "$elementId":
                    where_queries.append(self.element_id_operator(element_id=expression_or_value))
                case "$id":
                    where_queries.append(self.id_operator(id_=expression_or_value))
                case "$size":
                    query = self.size_operator(expression=expression_or_value)

                    if query is not None:
                        where_queries.append(query)
                case "$not":
                    where_queries.append(self.not_operator(expression=expression_or_value))
                case "$exists":
                    where_queries.append(self.exists_operator(exists=expression_or_value))
                case "$labels":
                    where_queries.append(self.labels_operator(labels=expression_or_value))
                case "$type":
                    where_queries.append(self.type_operator(types=expression_or_value))
                case _:
                    query = self.build_operators(filters=expression_or_value)

                    if query is not None:
                        where_queries.append(query)

        return " AND ".join([partial_query for partial_query in where_queries if partial_query != ""])

    def normalize_expressions(
        self, expressions: Union[Dict[str, Any], List[Any]], level: int = 0
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Normalizes and formats the provided expressions into usable expressions for the builder.

        Args:
            expressions (Union[Dict[str, Any], List[Any]]): The expressions to normalize.
            level (int, optional): The recursion depth level. Should not be modified outside the
                function itself. Defaults to `0`.

        Returns:
            Union[Dict[str, Any], List[Any]]: The normalized expressions.
        """
        normalized = deepcopy(expressions)

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
            for index, expression in enumerate((normalized)):
                normalized[index] = self.normalize_expressions(expressions=expression, level=level + 1)
        elif isinstance(normalized, dict):
            for operator, expression in normalized.items():
                # We don't need to do anything with the $direction operator
                if operator == "$direction":
                    continue
                # Handle $relationships operators
                elif operator == "$relationships":
                    for index, relationship_expression in enumerate(expression):
                        cast(Dict[str, List[Any]], normalized)[operator][index] = self.normalize_expressions(
                            expressions=relationship_expression, level=0
                        )
                # Handle $node operator
                elif operator == "$node":
                    cast(Dict[str, Any], normalized)[operator] = self.normalize_expressions(
                        expressions=expression, level=0
                    )
                # Handle $patterns operator
                elif operator == "$patterns":
                    for index, pattern in enumerate(expression):
                        if "$node" in pattern:
                            normalized[operator][index]["$node"] = self.normalize_expressions(
                                expressions=pattern["$node"], level=0
                            )

                        if "$relationship" in pattern:
                            normalized[operator][index]["$relationship"] = self.normalize_expressions(
                                expressions=pattern["$relationship"], level=0
                            )
                else:
                    cast(Dict[str, Any], normalized)[operator] = self.normalize_expressions(
                        expressions=expression, level=level + 1
                    )

        return normalized

    def remove_invalid_expressions(self, expressions: Dict[str, Any], level: int = 0) -> None:
        """
        Recursively removes empty objects and nested fields which do not start with a `$` and are
        not top level keys from nested dictionaries and lists.

        Args:
            expressions (Dict[str, Any]): The expression to check.
            level (int, optional): The recursion depth level. Should not be modified outside the
                function itself. Defaults to `0`.
        """
        operators_to_remove: List[str] = []

        if not isinstance(expressions, dict):
            return

        for operator, expression in expressions.items():
            if isinstance(expression, dict):
                # Search through all operators nested within
                self.remove_invalid_expressions(expressions=expression, level=level + 1)

                if not expression:
                    operators_to_remove.append(operator)
            elif isinstance(expression, list):
                if expression == []:
                    operators_to_remove.append(operator)
                    continue

                # Handle logical operators
                indexes_to_remove: List[int] = []

                for index, nested_expression in enumerate(expression):
                    # Search through all operators nested within
                    self.remove_invalid_expressions(expressions=nested_expression, level=level + 1)

                    if not nested_expression:
                        indexes_to_remove.append(index)

                # Remove all invalid indexes
                expression_copy = deepcopy(expression)

                for index in sorted(indexes_to_remove, reverse=True):
                    expression_copy.pop(index)

                expressions[operator] = expression_copy

                if not expression_copy:
                    operators_to_remove.append(operator)
            elif not operator.startswith("$") and level != 0:
                operators_to_remove.append(operator)

        for operator in operators_to_remove:
            expressions.pop(operator)

    def size_operator(self, expression: Dict[str, Any]) -> Optional[str]:
        """
        Builds the query for the `$size` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            Optional[str]: The operator query.
        """
        self._property_var_overwrite = f"SIZE({self.build_property_var()})"
        size_query = self.build_operators(filters=expression)

        self._property_var_overwrite = None
        return size_query

    def not_operator(self, expression: Dict[str, Any]) -> str:
        """
        Builds the query for the `$not` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        not_query = self.build_operators(filters=expression)
        return f"NOT({not_query})"

    def exists_operator(self, exists: bool) -> str:
        """
        Builds the query for the `$exists` operator.

        Args:
            exists (bool): Whether to match nodes/relationships where the property exists or not.

        Returns:
            str: The operator query.
        """
        if exists:
            return f"{self.build_property_var()} IS NOT NULL"

        return f"{self.build_property_var()} IS NULL"

    def labels_operator(self, labels: List[str]) -> str:
        """
        Builds the query for the `$labels` operator.

        Args:
            labels (List[str]): Node labels to match by.

        Returns:
            str: The operator query.
        """
        param_var = self.build_param_var()
        self.parameters[param_var] = labels

        return f"ALL(i IN labels({self.ref}) WHERE i IN ${param_var})"

    def type_operator(self, types: Union[str, List[str]]) -> str:
        """
        Builds the query for the `$type` operator.

        Args:
            types (Union[str, List[str]]): Relationship types to match by.

        Returns:
            str: The operator query.
        """
        param_var = self.build_param_var()
        self.parameters[param_var] = types

        if isinstance(types, str):
            return f"type({self.ref}) = ${param_var}"

        return f"type({self.ref}) IN ${param_var}"

    def id_operator(self, id_: int) -> str:
        """
        Builds the query for the `$id` operator.

        Args:
            id_ (int): The ID to match by.

        Returns:
            str: The operator query.
        """
        param_var = self.build_param_var()
        self.parameters[param_var] = id_

        return f"ID({self.ref}) = ${param_var}"

    def element_id_operator(self, element_id: str) -> str:
        """
        Builds the query for the `$elementId` operator.

        Args:
            element_id (str): The element ID to match by.

        Returns:
            str: The operator query.
        """
        param_var = self.build_param_var()
        self.parameters[param_var] = element_id

        return f"elementId({self.ref}) = ${param_var}"

    def and_operator(self, expressions: List[Dict[str, Any]]) -> str:
        """
        Builds the query for the `$and` operator.

        Args:
            expressions (List[Dict[str, Any]]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        and_queries: List[str] = []

        for expression in expressions:
            query = self.build_operators(filters=expression)

            if query is not None:
                and_queries.append(query)

        return f"({' AND '.join(and_queries)})"

    def or_operator(self, expressions: List[Dict[str, Any]]) -> str:
        """
        Builds the query for the `$or` operator.

        Args:
            expressions (List[Dict[str, Any]]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        or_queries: List[str] = []

        for expression in expressions:
            query = self.build_operators(filters=expression)

            if query is not None:
                or_queries.append(query)

        return f"({' OR '.join(or_queries)})"

    def xor_operator(self, expressions: List[Dict[str, Any]]) -> str:
        """
        Builds the query for the `$xor` operator.

        Args:
            expressions (List[Dict[str, Any]]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        xor_queries: List[str] = []

        for expression in expressions:
            query = self.build_operators(filters=expression)

            if query is not None:
                xor_queries.append(query)

        return f"({' XOR '.join(xor_queries)})"

    def patterns_operator(self, expression: Dict[str, Any]) -> str:
        """
        Builds the query for the `$patterns` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        from pyneo4j_ogm.queries.query_builder import (  # pylint: disable=import-outside-toplevel
            QueryBuilder,
        )

        builder = QueryBuilder()

        original_ref = deepcopy(self.ref)
        where_queries: List[str] = []

        relationship_ref = self.build_param_var()
        node_ref = self.build_param_var()

        # Build node queries
        if "$node" in expression:
            self.ref = node_ref
            node_queries = self.build_operators(filters=expression["$node"])

            if node_queries != "" and node_queries is not None:
                where_queries.append(node_queries)

        # Build relationship queries
        if "$relationship" in expression:
            self.ref = relationship_ref
            relationship_queries = self.build_operators(filters=expression["$relationship"])

            if relationship_queries != "" and relationship_queries is not None:
                where_queries.append(relationship_queries)

        self.ref = original_ref

        # Build final queries
        match_query = builder.relationship_match(
            ref=relationship_ref,
            start_node_ref=self.ref,
            end_node_ref=node_ref,
            direction=expression["$direction"],
        )
        exists_query = "EXISTS" if expression["$exists"] else "NOT EXISTS"
        where_query = " AND ".join(where_queries) if len(where_queries) > 0 else ""

        return f"{exists_query} {{MATCH {match_query}{f' WHERE {where_query}' if where_query != '' else where_query}}}"

    def build_param_var(self) -> str:
        """
        Builds a new parameter variable name. This method exists to ensure no duplicate variable
        names occur when using the builder.

        Returns:
            str: The unique variable name.
        """
        param_var = f"_n_{self._parameter_indent}"

        self._parameter_indent += 1
        return param_var

    def build_property_var(self) -> str:
        """
        Returns the node or relationship property to use.

        Returns:
            str: The property to use in the query.
        """
        if self._property_var_overwrite is not None:
            return self._property_var_overwrite

        property_var = f"{self.ref}.{self._property_name}"
        return property_var
