"""
This module contains the QueryBuilder class which handles queries build from options or operators.
"""
import logging
from copy import deepcopy
from typing import Any, Dict, List, Tuple

from neo4j_ogm.exceptions import InvalidOperator, UnknownRelationshipDirection
from neo4j_ogm.queries.types import (
    RelationshipDirection,
    TypedNodeExpressions,
    TypedPropertyExpressions,
    TypedQueryOptions,
    TypedRelationshipExpressions,
)
from neo4j_ogm.queries.validators import (
    ComparisonValidator,
    ElementValidator,
    LogicalValidator,
    NodeValidator,
    QueryOptionsValidator,
    RelationshipValidator,
)


class QueryBuilder:
    """
    Builder class for generating queries from expressions or options.
    """

    __comparison_operators: Dict[str, str] = {}
    __logical_operators: Dict[str, str] = {}
    __element_operators: Dict[str, str] = {}
    _is_node_expression: bool | None
    _variable_name_overwrite: str | None = None
    _parameter_count: int = 0
    _pattern_count: int = 0
    property_name: str
    ref: str

    def __init__(self) -> None:
        # Get operators and parsing format
        for _, field in ComparisonValidator.__fields__.items():
            self.__comparison_operators[field.alias] = field.field_info.extra["extra"]["parser"]

        for _, field in LogicalValidator.__fields__.items():
            self.__logical_operators[field.alias] = field.field_info.extra["extra"]["parser"]

        for _, field in ElementValidator.__fields__.items():
            self.__element_operators[field.alias] = field.field_info.extra["extra"]["parser"]

    def build_node_expressions(
        self, expressions: TypedNodeExpressions, ref: str = "n"
    ) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds a query for filtering node properties with the given operators.

        Args:
            expressions (TypedNodeExpressions): The expressions defining the operators.
            ref (str, optional): The variable to use inside the generated query. Defaults to "n".

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated query and parameters.
        """
        self.ref = ref
        self._is_node_expression = True

        logging.debug("Building query for node expressions %s", expressions)
        normalized_expressions = self._normalize_expressions(expressions=expressions)
        validated_expressions = self._validate_expressions(expressions=normalized_expressions)

        return self._build_nested_expressions(validated_expressions)

    def build_relationship_expressions(
        self, expressions: TypedRelationshipExpressions, ref: str = "n"
    ) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds a query for filtering relationship properties with the given operators.

        Args:
            expressions (TypedPropertyExpressions): The expressions defining the operators.
            ref (str, optional): The variable to use inside the generated query. Defaults to "n".

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated query and parameters.
        """
        self.ref = ref
        self._is_node_expression = False

        logging.debug("Building query for relationship expressions %s", expressions)
        normalized_expressions = self._normalize_expressions(expressions=expressions)
        validated_expressions = self._validate_expressions(expressions=normalized_expressions)

        return self._build_nested_expressions(validated_expressions)

    def build_property_expressions(
        self, expressions: TypedPropertyExpressions, ref: str = "n"
    ) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds a query for filtering relationship-property (defined on node models) properties with the given operators.

        Args:
            expressions (TypedPropertyExpressions): The expressions defining the operators.
            ref (str, optional): The variable to use inside the generated query. Defaults to "n".

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated query and parameters.
        """
        self.ref = ref
        self._is_node_expression = None

        logging.debug("Building query for property expressions %s", expressions)
        normalized_expressions = self._normalize_expressions(expressions=expressions)
        validated_expressions = self._validate_expressions(expressions=normalized_expressions)

        return self._build_nested_expressions(validated_expressions)

    def build_query_options(self, options: TypedQueryOptions, ref: str = "n") -> str:
        """
        Builds parts of a query with the given query options for paginating and sorting the result.

        Args:
            options (Dict[str, Any]): The options for the result.
            ref (str, optional): The variable to use inside the generated query. Defaults to "n".

        Returns:
            str: The generated query.
        """
        self.ref = ref
        partial_queries: List[str] = []

        logging.debug("Validating options %s", options)
        validated_options = QueryOptionsValidator.parse_obj(options)

        if validated_options.sort and len(validated_options.sort) != 0:
            partial_sort_query: List[str] = []

            for property_name in (
                validated_options.sort if isinstance(validated_options.sort, list) else [validated_options.sort]
            ):
                if property_name == "$elementId":
                    partial_sort_query.append(f"elementId({self.ref})")
                elif property_name == "$id":
                    partial_sort_query.append(f"ID({self.ref})")
                else:
                    partial_sort_query.append(f"{self.ref}.{property_name}")

            partial_queries.append(
                f"ORDER BY {', '.join(partial_sort_query)} {validated_options.order if validated_options.order else ''}"
            )

        if validated_options.skip:
            partial_queries.append(f"SKIP {validated_options.skip}")

        if validated_options.limit:
            partial_queries.append(f"LIMIT {validated_options.limit}")

        return " ".join(partial_queries)

    def build_relationship_query(
        self,
        direction: RelationshipDirection = RelationshipDirection.BOTH,
        relationship_type: str | None = None,
        start_node_labels: List[str] | None = None,
        end_node_labels: List[str] | None = None,
        rel_ref: str = "r",
        start_ref: str = "start",
        end_ref: str = "end",
    ) -> str:
        """
        Builds a relationships `MATCH` clause based on the defined ref names and direction.

        Args:
            direction (RelationshipDirection): The direction that should be used whe building the relationship.
                Defaults to RelationshipDirection.BOTH
            relationship_type (str | None): The relationship type. Defaults to None.
            start_node_labels (List[str] | None): The start node labels. Defaults to None.
            end_node_labels (List[str] | None): The end node labels. Defaults to None.
            rel_ref (str, optional): Variable name to use for the relationship. Defaults to "r".
            start_ref (str, optional): Variable name to use for the start node. Defaults to "start".
            end_ref (str, optional): Variable name to use for the end node. Defaults to "end".

        Raises:
            UnknownRelationshipDirection: Raised if a invalid direction is provided.

        Returns:
            str: The generated `MATCH` clause.
        """
        start_labels = ":".join(start_node_labels if start_node_labels is not None else [])
        end_labels = ":".join(end_node_labels if end_node_labels is not None else [])
        start_node = f"({start_ref}{f':`{start_labels}`' if len(start_labels) > 0 else ''})"
        end_node = f"({end_ref}{f':`{end_labels}`' if len(end_labels) > 0 else ''})"
        relationship = f"[{rel_ref}:`{relationship_type}`]" if relationship_type is not None else f"[{rel_ref}]"

        match direction:
            case RelationshipDirection.BOTH:
                return f"{start_node}-{relationship}-{end_node}"
            case RelationshipDirection.INCOMING:
                return f"{start_node}<-{relationship}-{end_node}"
            case RelationshipDirection.BOTH:
                return f"{start_node}-{relationship}->{end_node}"
            case _:
                raise UnknownRelationshipDirection(
                    expected_directions=[option.value for option in RelationshipDirection],
                    actual_direction=direction,
                )

    def _build_node_pattern(self, patterns: List[Dict[str, Any]]) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds a `$pattern` operator for node expressions.

        Args:
            patterns (List[Dict[str, Any]]): The patterns to build.

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated `MATCH/WHERE` clauses and `parameters`.
        """
        old_ref = deepcopy(self.ref)
        match_queries: List[str] = []
        where_queries: List[str] = []
        parameters: Dict[str, Any] = {}

        for pattern in patterns:
            node_ref = self._get_pattern_ref_name() if "$node" in pattern else ""
            relationship_ref = ""
            relationship = ""

            # Check if relationship is defined and build MATCH clause
            if "$relationship" in pattern:
                relationship_ref = self._get_pattern_ref_name()

                if "$minHops" not in pattern["$relationship"] and "$maxHops" not in pattern["$relationship"]:
                    relationship = f"[{relationship_ref}]"
                else:
                    relationship_min_hops = (
                        pattern["$relationship"]["$minHops"] if "$minHops" in pattern["$relationship"] else ""
                    )
                    relationship_max_hops = (
                        pattern["$relationship"]["$maxHops"] if "$maxHops" in pattern["$relationship"] else ""
                    )

                    relationship = f"[{relationship_ref}*{relationship_min_hops}..{relationship_max_hops}]"

            # Build relationship direction
            match pattern["$direction"]:
                case RelationshipDirection.INCOMING:
                    match_queries.append(f"({self.ref})<-{relationship}-({node_ref})")
                case RelationshipDirection.OUTGOING:
                    match_queries.append(f"({self.ref})-{relationship}->({node_ref})")
                case _:
                    match_queries.append(f"({self.ref})-{relationship}-({node_ref})")

            # Build node and relationship expressions if present
            if "$node" in pattern:
                self.ref = node_ref
                match_query, where_query, node_parameters = self._build_nested_expressions(expressions=pattern["$node"])

                if where_query is not None:
                    where_queries.append(where_query)
                if match_query is not None:
                    match_queries.append(match_query)
                parameters = {**parameters, **node_parameters}

            if "$relationship" in pattern:
                self.ref = relationship_ref
                match_query, where_query, node_parameters = self._build_nested_expressions(
                    expressions=pattern["$relationship"]
                )

                if where_query is not None:
                    where_queries.append(where_query)
                if match_query is not None:
                    match_queries.append(match_query)
                parameters = {**parameters, **node_parameters}

        self.ref = old_ref
        complete_match_query = " AND ".join(match_queries) if len(match_queries) != 0 else None
        complete_where_query = " AND ".join(where_queries) if len(where_queries) != 0 else None
        return complete_match_query, complete_where_query, parameters

    def _build_relationship_pattern(
        self, patterns: List[Dict[str, Any]]
    ) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds a `$pattern` operator for relationship expressions.

        Args:
            patterns (List[Dict[str, Any]]): The patterns to build.

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated `MATCH/WHERE` clauses and `parameters`.
        """
        old_ref = deepcopy(self.ref)
        match_queries: List[str] = []
        where_queries: List[str] = []
        parameters: Dict[str, Any] = {}

        for pattern in patterns:
            start_node_ref = self._get_pattern_ref_name() if "$startNode" in pattern else ""
            end_node_ref = self._get_pattern_ref_name() if "$endNode" in pattern else ""

            # Build relationship direction
            match pattern["$direction"]:
                case RelationshipDirection.INCOMING:
                    match_queries.append(f"({start_node_ref})<-[{self.ref}]-({end_node_ref})")
                case RelationshipDirection.OUTGOING:
                    match_queries.append(f"({start_node_ref})-[{self.ref}]->({end_node_ref})")
                case _:
                    match_queries.append(f"({start_node_ref})-[{self.ref}]-({end_node_ref})")

            # Build node and relationship expressions if present
            if "$startNode" in pattern:
                self.ref = start_node_ref
                match_query, where_query, node_parameters = self._build_nested_expressions(
                    expressions=pattern["$startNode"]
                )

                if where_query is not None:
                    where_queries.append(where_query)
                if match_query is not None:
                    match_queries.append(match_query)
                parameters = {**parameters, **node_parameters}

            if "$endNode" in pattern:
                self.ref = end_node_ref
                match_query, where_query, node_parameters = self._build_nested_expressions(
                    expressions=pattern["$endNode"]
                )

                if where_query is not None:
                    where_queries.append(where_query)
                if match_query is not None:
                    match_queries.append(match_query)
                parameters = {**parameters, **node_parameters}

        self.ref = old_ref
        complete_match_query = " AND ".join(match_queries) if len(match_queries) != 0 else None
        complete_where_query = " AND ".join(where_queries) if len(where_queries) != 0 else None
        return complete_match_query, complete_where_query, parameters

    def _build_nested_expressions(self, expressions: Dict[str, Any]) -> Tuple[str | None, str | None, Dict[str, Any]]:
        """
        Builds nested operators defined in provided expressions.

        Args:
            expressions (Dict[str, Any]): The expressions to build the query from.

        Raises:
            InvalidOperator: If the `expressions` parameter is not a valid dict.

        Returns:
            Tuple[str | None, str | None, Dict[str, Any]]: The generated query and parameters.
        """
        complete_parameters: Dict[str, Any] = {}
        partial_match_queries: List[str] = []
        partial_where_queries: List[str] = []

        if not isinstance(expressions, dict):
            raise InvalidOperator(f"Expressions must be instance of dict, got {type(expressions)}")

        for property_or_operator, expression_or_value in expressions.items():
            parameters: Dict[str, Any] = {}
            where_query = None
            match_query = None

            if not property_or_operator.startswith("$"):
                # Update current property name if the key is not a operator
                self.property_name = property_or_operator

            if property_or_operator in self.__element_operators:
                where_query, parameters = self._build_element_operator(property_or_operator, expression_or_value)
            elif property_or_operator == "$not":
                match_query, where_query, parameters = self._build_not_operator(expression=expression_or_value)
            elif property_or_operator == "$in":
                where_query, parameters = self._build_in_operator(value=expression_or_value)
            elif property_or_operator == "$size":
                where_query, parameters = self._build_size_operator(expression=expression_or_value)
            elif property_or_operator == "$all":
                match_query, where_query, parameters = self._build_all_operator(expressions=expression_or_value)
            elif property_or_operator == "$exists":
                where_query = self._build_exists_operator(exists=expression_or_value)
            elif property_or_operator == "$labels":
                where_query, parameters = self._build_labels_operator(labels=expression_or_value)
            elif property_or_operator == "$type":
                where_query, parameters = self._build_types_operator(relationship_type=expression_or_value)
            elif property_or_operator == "$patterns":
                if self._is_node_expression:
                    match_query, where_query, parameters = self._build_node_pattern(patterns=expression_or_value)
                else:
                    match_query, where_query, parameters = self._build_relationship_pattern(
                        patterns=expression_or_value
                    )
            elif property_or_operator in self.__comparison_operators:
                where_query, parameters = self._build_comparison_operator(
                    operator=property_or_operator, value=expression_or_value
                )
            elif property_or_operator in self.__logical_operators:
                match_query, where_query, parameters = self._build_logical_operator(
                    operator=property_or_operator, expressions=expression_or_value
                )
            elif not property_or_operator.startswith("$"):
                match_query, where_query, parameters = self._build_nested_expressions(expressions=expression_or_value)

            if where_query is not None:
                partial_where_queries.append(where_query)

            if match_query is not None:
                partial_match_queries.append(match_query)

            complete_parameters = {**complete_parameters, **parameters}

        complete_match_query = ", ".join(partial_match_queries) if len(partial_match_queries) != 0 else None
        complete_where_query = " AND ".join(partial_where_queries) if len(partial_where_queries) != 0 else None
        return complete_match_query, complete_where_query, complete_parameters

    def _build_labels_operator(self, labels: List[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds comparison operators.

        Args:
            labels (List[str]): The labels to filter by.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        parameter_name = self._get_parameter_name()
        parameters: Dict[str, Any] = {}

        query = f"ALL(label in ${parameter_name} WHERE label IN labels({self.ref}))"
        parameters[parameter_name] = labels

        return query, parameters

    def _build_types_operator(self, relationship_type: str | List[str]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds comparison operators.

        Args:
            relationship_type (List[str]): The type or types to filter by.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        parameter_name = self._get_parameter_name()
        parameters: Dict[str, Any] = {}

        if isinstance(relationship_type, list):
            query = f"type({self.ref}) IN ${parameter_name}"
        else:
            query = f"type({self.ref}) = ${parameter_name}"
        parameters[parameter_name] = relationship_type

        return query, parameters

    def _build_comparison_operator(self, operator: str, value: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Builds comparison operators.

        Args:
            operator (str): The operator to build.
            value (Any): The provided value for the operator.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        parameter_name = self._get_parameter_name()
        parameters = {}

        query = self.__comparison_operators[operator].format(
            property_name=self._get_variable_name(),
            value=parameter_name,
        )
        parameters[parameter_name] = value

        return query, parameters

    def _build_exists_operator(self, exists: bool) -> str:
        """
        Builds a `IS NOT NULL` or `IS NULL` query based on the defined value.

        Args:
            exists (bool): Whether the query should check if the property exists or not.

        Raises:
            InvalidOperator: If the operator value is not a bool.

        Returns:
            str: The generated query.
        """
        if not isinstance(exists, bool):
            raise InvalidOperator(f"$exists operator value must be a instance of bool, got {type(exists)}")

        query = (
            f"{self._get_variable_name()} IS NULL" if exists is False else f"{self._get_variable_name()} IS NOT NULL"
        )
        return query

    def _build_not_operator(self, expression: Dict[str, Any]) -> Tuple[str | None, str, Dict[str, Any]]:
        """
        Builds a `NOT()` clause with the defined expressions.

        Args:
            expression (Dict[str, Any]): The expressions defined for the `$not` operator.

        Returns:
            Tuple[str | None, str, Dict[str, Any]]: The generated query and parameters.
        """
        match_query, where_query, complete_parameters = self._build_nested_expressions(expressions=expression)

        complete_where_query = f"NOT({where_query})"
        return match_query, complete_where_query, complete_parameters

    def _build_in_operator(self, value: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Builds a query containing a `IN` operator.

        Args:
            expression (Dict[str, Any]): The expressions defined for the `$in` operator.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        parameter_name = self._get_parameter_name()
        complete_parameters = {parameter_name: value}

        if isinstance(value, list):
            complete_query = f"ALL(i IN ${parameter_name} WHERE i IN {self._get_variable_name()})"
        else:
            complete_query = f"${parameter_name} IN {self._get_variable_name()}"

        return complete_query, complete_parameters

    def _build_size_operator(self, expression: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Builds a `SIZE()` clause with the defined comparison operator.

        Args:
            expression (Dict[str, Any]): The expression defined fot the `$size` operator.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        comparison_operator = next(iter(expression))
        self._variable_name_overwrite = f"SIZE({self._get_variable_name()})"

        query, parameters = self._build_comparison_operator(
            operator=comparison_operator, value=expression[comparison_operator]
        )

        self._variable_name_overwrite = None

        return query, parameters

    def _build_all_operator(self, expressions: List[Dict[str, Any]]) -> Tuple[str | None, str, Dict[str, Any]]:
        """
        Builds a `ALL()` clause with the defined expressions.

        Args:
            expressions (List[Dict[str, Any]]): Expressions to apply inside the `$all` operator.

        Raises:
            InvalidOperator: If the operator value is not a list.

        Returns:
            Tuple[str | None, str, Dict[str, Any]]: The generated query and parameters.
        """
        self._variable_name_overwrite = "i"
        complete_parameters: Dict[str, Any] = {}
        partial_match_queries: List[str] = []
        partial_where_queries: List[str] = []

        if not isinstance(expressions, list):
            raise InvalidOperator(f"Value of $all operator must be list, got {type(expressions)}")

        for expression in expressions:
            match_query, where_query, parameters = self._build_nested_expressions(expressions=expression)

            partial_where_queries.append(where_query)
            partial_match_queries.append(match_query)
            complete_parameters = {**complete_parameters, **parameters}

        self._variable_name_overwrite = None

        complete_where_query = f"ALL(i IN {self._get_variable_name()} WHERE {' AND '.join(partial_where_queries)})"
        complete_match_query = " AND ".join(partial_match_queries) if len(partial_match_queries) != 0 else None
        return complete_match_query, complete_where_query, complete_parameters

    def _build_logical_operator(
        self, operator: str, expressions: List[Dict[str, Any]]
    ) -> Tuple[str | None, str, Dict[str, Any]]:
        """
        Builds all expressions defined inside a logical operator.

        Args:
            operator (str): The logical operator.
            expressions (List[Dict[str, Any]]): The expressions chained together by the operator.

        Raises:
            InvalidOperator: If the operator value is not a list.

        Returns:
            Tuple[str | None, str, Dict[str, Any]]: The query and parameters.
        """
        complete_parameters: Dict[str, Any] = {}
        partial_match_queries: List[str] = []
        partial_where_queries: List[str] = []

        if not isinstance(expressions, list):
            raise InvalidOperator(f"Value of {operator} operator must be list, got {type(expressions)}")

        for expression in expressions:
            match_query, where_query, parameters = self._build_nested_expressions(expressions=expression)

            partial_where_queries.append(where_query)
            partial_match_queries.append(match_query)
            complete_parameters = {**complete_parameters, **parameters}

        complete_where_query = f"({f' {self.__logical_operators[operator]} '.join(partial_where_queries)})"
        complete_match_query = " AND ".join(partial_match_queries) if len(partial_match_queries) != 0 else None
        return complete_match_query, complete_where_query, complete_parameters

    def _build_element_operator(self, operator: str, value: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Builds operators for Neo4j-specific `elementId()` and `ID()`.

        Args:
            operator (str): The operator to build.
            value (Any): The value to use for building the operator.

        Returns:
            Tuple[str, Dict[str, Any]]: The generated query and parameters.
        """
        variable_name = self._get_parameter_name()

        query = self.__element_operators[operator].format(ref=self.ref, value=variable_name)
        parameters = {variable_name: value}

        return query, parameters

    def _get_parameter_name(self) -> str:
        """
        Builds the parameter name and increment the parameter count by one.

        Returns:
            str: The generated parameter name.
        """
        parameter_name = f"{self.ref}_{self._parameter_count}"
        self._parameter_count += 1

        return parameter_name

    def _get_pattern_ref_name(self) -> str:
        """
        Builds the pattern ref to use increments the pattern count by one.

        Returns:
            str: The generated pattern name.
        """
        pattern_ref_name = f"r_{self._pattern_count}"
        self._pattern_count += 1

        return pattern_ref_name

    def _get_variable_name(self) -> str:
        """
        Builds the variable name used in the query.

        Returns:
            str: The generated variable name.
        """
        if self._variable_name_overwrite:
            return self._variable_name_overwrite

        return f"{self.ref}.{self.property_name}"

    def _normalize_expressions(self, expressions: Dict[str, Any], level: int = 0) -> Dict[str, Any]:
        """
        Normalizes and formats the provided expressions into usable expressions for the builder.

        Args:
            expressions (Dict[str, Any]): The expressions to normalize
            level (int, optional): The recursion depth level. Should not be modified outside the function itself.
                Defaults to 0.

        Returns:
            Dict[str, Any]: The normalized expressions.
        """
        logging.debug("Normalizing expressions %s", expressions)
        normalized: Dict[str, Any] = deepcopy(expressions)

        if isinstance(normalized, dict) and level == 0:
            # Transform values without a operator to a `$eq` operator
            for operator, value in normalized.items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    # If the operator is a `$not` operator or just a property name, add a `$eq` operator
                    if operator in ["$not", "$size"] or not operator.startswith("$"):
                        logging.debug("Normalizing operator %s and value %s to $eq operator", operator, value)
                        normalized[operator] = {"$eq": value}

            if len(normalized.keys()) > 1 and level > 0:
                # If more than one operator is defined in a dict, transform operators to `$and` operator
                logging.debug("Normalizing %s to $and operator", normalized)
                normalized = {"$and": [{operator: expression} for operator, expression in normalized.items()]}

        # Normalize nested operators
        if isinstance(normalized, list):
            for index, expression in enumerate(normalized):
                normalized[index] = self._normalize_expressions(expression, level + 1)
        elif isinstance(normalized, dict):
            for operator, expression in normalized.items():
                if operator == "$patterns":
                    for index, pattern in enumerate(expression):
                        for pattern_operator, pattern_expression in pattern.items():
                            normalized[operator][index][pattern_operator] = self._normalize_expressions(
                                pattern_expression, 0
                            )
                else:
                    normalized[operator] = self._normalize_expressions(expression, level + 1)

        return normalized

    def _validate_expressions(self, expressions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates given expressions.

        Args:
            expressions (Dict[str, Any]): The expressions to validate.

        Returns:
            Dict[str, Any]: The validated expressions.
        """
        logging.debug("Validating expressions %s", expressions)
        is_node_expression = getattr(self, "_is_node_expression", None)

        if is_node_expression is True:
            validated = NodeValidator.parse_obj(expressions)
            validated = validated.dict(by_alias=True, exclude_none=True, exclude_unset=True)
        elif is_node_expression is False:
            validated = RelationshipValidator.parse_obj(expressions)
            validated = validated.dict(by_alias=True, exclude_none=True, exclude_unset=True)
        else:
            validated = ElementValidator.parse_obj(expressions)
            validated = validated.dict(by_alias=True, exclude_none=True, exclude_unset=True)

        # Remove empty objects which remained from pydantic validation
        self._remove_invalid_expressions(validated)

        return validated

    def _remove_invalid_expressions(self, expressions: Dict[str, Any], level: int = 0) -> None:
        """
        Recursively removes empty objects and nested fields which do not start with a `$` and are not top level keys
        from nested dictionaries and lists.

        Args:
            expressions (Dict[str, Any]): The expression to check.
            level (int, optional): The recursion depth level. Should not be modified outside the function itself.
                Defaults to 0.
        """
        logging.debug("Removing invalid expressions from expression %s", expressions)
        operators_to_remove: List[str] = []

        if not isinstance(expressions, dict):
            return

        for operator, expression in expressions.items():
            if isinstance(expression, dict):
                # Search through all operators nested within
                self._remove_invalid_expressions(expressions=expression, level=level + 1)

                if not expression:
                    logging.debug("Invalid operator found: %s omitted", operator)
                    operators_to_remove.append(operator)
            elif isinstance(expression, list):
                # Handle logical operators
                indexes_to_remove: List[str] = []

                for index, nested_expression in enumerate(expression):
                    # Search through all operators nested within
                    self._remove_invalid_expressions(expressions=nested_expression, level=level + 1)

                    if not nested_expression:
                        logging.debug("Invalid operator found at index %s: %s omitted", index, operator)
                        indexes_to_remove.append(index)

                # Remove all invalid indexes
                for index in indexes_to_remove:
                    expression.pop(index)
            elif not operator.startswith("$") and level != 0:
                logging.debug("Invalid operator found: %s omitted", operator)
                operators_to_remove.append(operator)

        for operator in operators_to_remove:
            expressions.pop(operator)
