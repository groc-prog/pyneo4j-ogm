"""
Class for building the query for the database.
"""
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union, cast

from neo4j_ogm.exceptions import InvalidRelationshipHops
from neo4j_ogm.logger import logger
from neo4j_ogm.queries.types import (
    MultiHopFilters,
    MultiHopRelationship,
    NodeFilters,
    QueryDataTypes,
    RelationshipFilters,
    RelationshipMatchDirection,
    RelationshipPropertyFilters,
)
from neo4j_ogm.queries.validators import (
    MultiHopFiltersModel,
    NodeFiltersModel,
    QueryOptionModel,
    RelationshipFiltersModel,
    RelationshipPropertyFiltersModel,
)


class FilterQueries(TypedDict):
    """
    Type definition for `query` attribute.
    """

    match: str
    where: str
    options: str
    projections: str


# TODO: Add support for projections
# MATCH (n:Developer), path = (n)-[r*]->(m:Coffee)
# WHERE
#     ID(n) = 66 AND
#     ALL(_n_0 IN relationships(path) WHERE
#         CASE type(_n_0)
#             WHEN 'SELLS' THEN _n_0.ok = True
#             ELSE true
#         END
#     )
# WITH [x IN r WHERE type(x) = "SELLS" | {ok: x.ok, foo: x.foo}] as sells, m -> Generates a projection for relationship properties
# RETURN DISTINCT  collect({name: m.name, sells: sells }) -> Projection for node properties


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
    query: FilterQueries = {
        "match": "",
        "where": "",
        "projections": "",
        "options": "",
    }

    def node_filters(self, filters: NodeFilters, ref: str = "n") -> None:
        """
        Builds the node filters for the query.

        Args:
            filters (Dict[str, Any]): The filters to build.
            ref (str, optional): The reference to the node. Defaults to "n".
        """
        logger.debug("Building node filters %s", filters)
        self.ref = ref
        cast(dict, self.query).update({"where": "", "options": ""})
        self.parameters = {}
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = NodeFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        self.query["where"] = self._build_query(filters=validated_filters)

    def relationship_filters(self, filters: RelationshipFilters, ref: str = "r") -> None:
        """
        Builds the relationship filters for the query.

        Args:
            filters (Dict[str, Any]): The filters to build.
            ref (str, optional): The reference to the relationship. Defaults to "r".
        """
        logger.debug("Building relationship filters %s", filters)
        self.ref = ref
        cast(dict, self.query).update({"where": "", "options": ""})
        self.parameters = {}
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = RelationshipFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        self.query["where"] = self._build_query(filters=validated_filters)

    def relationship_property_filters(
        self, filters: RelationshipPropertyFilters, ref: str = "r", node_ref: str = "end"
    ) -> None:
        """
        Builds the relationship and node filters for relationship property queries.

        Args:
            filters (Dict[str, Any]): The filters to build.
            ref (str, optional): The reference to the relationship. Defaults to "r".
            node_ref (str, optional): The reference to the node. Defaults to "end".
        """
        logger.debug("Building relationship property filters %s", filters)
        cast(dict, self.query).update({"where": "", "options": ""})
        self.parameters = {}
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = RelationshipPropertyFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        where_queries = []

        if "$relationship" in validated_filters:
            self.ref = ref
            where_queries.append(self._build_query(filters=validated_filters["$relationship"]))

            # Remove relationship filters from validated filters before building node filters
            validated_filters.pop("$relationship")

        self.ref = node_ref
        where_queries.append(self._build_query(filters=validated_filters))

        self.query["where"] = " AND ".join([query for query in where_queries if query != ""])

    def multi_hop_filters(self, filters: MultiHopFilters, start_ref: str = "n", end_ref: str = "m") -> None:
        """
        Builds the filters for a multi hop query.

        Args:
            filters (Dict[str, Any]): The filters to build.
            start_ref (str, optional): The reference to the start node. Defaults to "n".
            end_ref (str, optional): The reference to the end node. Defaults to "m".
        """
        logger.debug("Building multi hop filters %s", filters)
        self.ref = start_ref
        cast(dict, self.query).update({"where": "", "options": "", "match": ""})
        self.parameters = {}
        normalized_filters = self._normalize_expressions(filters)

        # Validate filters with pydantic model
        validated_filters = MultiHopFiltersModel(**normalized_filters)
        validated_filters = validated_filters.dict(by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._remove_invalid_expressions(validated_filters)

        original_ref = deepcopy(self.ref)
        relationship_ref = self._build_param_var()

        # Build path match
        relationship_match = self.relationship_match(
            direction=RelationshipMatchDirection.OUTGOING,
            start_node_ref=start_ref,
            end_node_ref=end_ref,
            min_hops=validated_filters["$minHops"] if "$minHops" in validated_filters else None,
            max_hops=validated_filters["$maxHops"] if "$maxHops" in validated_filters else None,
        )
        self.query["match"] = f", path = {relationship_match}"

        # Build node filters
        self.ref = end_ref
        where_node_query = self._build_query(filters=validated_filters["$node"]) if "$node" in validated_filters else ""

        # Build relationship filters
        where_relationship_queries: Dict[str, str] = {}
        self.ref = relationship_ref

        if "$relationships" in validated_filters:
            for relationship in validated_filters["$relationships"]:
                relationship_type = relationship["$type"]

                relationship_filters = deepcopy(cast(MultiHopRelationship, relationship))
                relationship_filters.pop("$type")
                build_filters = self._build_query(filters=relationship_filters)

                if build_filters != "":
                    where_relationship_queries[relationship_type] = build_filters

        # Build WHERE query
        relationship_where_query = ""

        if len(where_relationship_queries.keys()) > 0:
            relationship_where_query = f"""
                ALL({relationship_ref} IN relationships(path) WHERE
                    CASE type({relationship_ref})
                        {"".join([f"WHEN '{relationship_name}' THEN {relationship_query}" for relationship_name, relationship_query in where_relationship_queries.items()])}
                        ELSE true
                    END
                )"""

        self.ref = original_ref
        self.query[
            "where"
        ] = f"{where_node_query}{' AND ' if where_node_query != '' and relationship_where_query != '' else ''}{relationship_where_query}"

    def query_options(self, options: Dict[str, Any], ref: str = "n") -> None:
        """
        Builds the query options for the query.

        Args:
            options (Dict[str, Any]): The options to build.
            ref (str, optional): The reference to the node or relationship. Defaults to "n".
        """
        logger.debug("Building query options %s", options)
        self.query["options"] = ""

        # Validate options with pydantic model
        validated_options = QueryOptionModel(**options)
        validated_options = validated_options.dict(exclude_none=True)

        sort_query: str = ""
        limit_query: str = ""
        skip_query: str = ""

        if "sort" in validated_options:
            sorted_properties = [f"{ref}.{property_name}" for property_name in validated_options["sort"]]
            sort_query = f"ORDER BY {', '.join(sorted_properties)}"

        if "order" in validated_options:
            if sort_query != "":
                sort_query = f"{sort_query} {validated_options['order']}"
            else:
                sort_query = f"ORDER BY {ref} {validated_options['order']}"

        if "limit" in validated_options:
            limit_query = f"LIMIT {validated_options['limit']}"

        if "skip" in validated_options:
            skip_query = f"SKIP {validated_options['skip']}"

        self.query["options"] = f"{sort_query} {skip_query} {limit_query}".strip()

    def node_match(self, labels: Optional[List[str]] = None, ref: Optional[str] = "n") -> str:
        """
        Builds a node to match in the query.

        Args:
            labels (List[str]): The labels to build.
            ref (str, optional): The reference to the node. Defaults to "n".

        Returns:
            str: The node to match.
        """
        logger.debug("Building node match with labels %s and node ref %s", labels, ref)
        node_ref = ref if ref is not None else ""
        node_labels = f":{':'.join(labels)}" if labels is not None else ""

        return f"({node_ref}{node_labels})"

    def relationship_match(
        self,
        ref: Optional[str] = "r",
        type_: Optional[str] = None,
        direction: RelationshipMatchDirection = RelationshipMatchDirection.BOTH,
        start_node_ref: Optional[str] = None,
        start_node_labels: Optional[List[str]] = None,
        end_node_ref: Optional[str] = None,
        end_node_labels: Optional[List[str]] = None,
        min_hops: Optional[int] = None,
        max_hops: Optional[Union[int, Literal["*"]]] = None,
    ) -> str:
        """
        Builds a relationship to match in the query.

        Args:
            type_ (str): The type of the relationship.
            ref (str, optional): The reference to the relationship. Defaults to "r".
            start_node_ref (Optional[str], optional): The reference to the start node. Defaults to None.
            start_node_labels (Optional[List[str]], optional): The labels of the start node. Defaults to None.
            end_node_ref (Optional[str], optional): The reference to the end node. Defaults to None.
            end_node_labels (Optional[List[str]], optional): The labels of the end node. Defaults to None.
            min_hops (Optional[Union[int, str]], optional): The minimum number of hops. Defaults to None.
            max_hops (Optional[Union[int, str]], optional): The maximum number of hops. Defaults to None.

        Raises:
            InvalidRelationshipHops: Raised when the min_hops or max_hops are invalid.

        Returns:
            str: The relationship to match.
        """
        logger.debug(
            """Building relationship match with type %s, relationship ref %s, start node ref %s, start node labels %s,
            end node ref %s, end node labels %s, min hops %s and max hops %s""",
            type_,
            ref,
            start_node_ref,
            start_node_labels,
            end_node_ref,
            end_node_labels,
            min_hops,
            max_hops,
        )
        start_node_match = self.node_match(labels=start_node_labels, ref=start_node_ref)
        end_node_match = self.node_match(labels=end_node_labels, ref=end_node_ref)
        hops = ""

        if any(
            [
                (isinstance(min_hops, int) and min_hops < 0),
                (isinstance(max_hops, str) and max_hops != "*"),
                (isinstance(max_hops, int) and max_hops < 0),
            ]
        ):
            raise InvalidRelationshipHops()

        if min_hops is None and max_hops == "*":
            hops = "*"
        elif min_hops is not None and max_hops is not None and max_hops != "*":
            hops = f"*{min_hops}..{max_hops}"
        elif min_hops is not None:
            hops = f"*{min_hops}.."
        elif max_hops is not None and max_hops != "*":
            hops = f"*..{max_hops}"

        relationship_ref = ref if ref is not None else ""
        relationship_type = f":{type_}" if type_ is not None else ""
        relationship_match = f"[{relationship_ref}{relationship_type}{hops}]"

        match direction:
            case RelationshipMatchDirection.INCOMING:
                return f"{start_node_match}<-{relationship_match}-{end_node_match}"
            case RelationshipMatchDirection.OUTGOING:
                return f"{start_node_match}-{relationship_match}->{end_node_match}"
            case RelationshipMatchDirection.BOTH:
                return f"{start_node_match}-{relationship_match}-{end_node_match}"

    def node_projection(self, projections: Dict[str, str], ref: str = "n") -> List[str]:
        """
        Builds a projection which only returns the node properties defined in the projection.

        Args:
            ref (str): The reference to the node. Defaults to "n".
            projections (Dict[str, str]): The projections to build.

        Returns:
            list[str]: The projection queries.
        """
        self.query["projections"] = ""

        if not isinstance(projections, dict):
            return

        projection_queries: List[str] = [
            f"{str(projection)}: {ref}.{str(property_name)}" for projection, property_name in projections.items()
        ]

        if len(projection_queries) > 0:
            self.query["projections"] = (
                f"DISTINCT collect({{{', '.join(projection_queries)}}})" if len(projection_queries) > 0 else ""
            )

    def _build_query(self, filters: Dict[str, Any]) -> str:
        where_queries: List[str] = []

        for property_or_operator, expression_or_value in filters.items():
            # Set the property name here so it can be used in the operators
            if not property_or_operator.startswith("$"):
                self._property_name = property_or_operator

            match property_or_operator:
                case operator if operator in [key for key, _ in self._operators.items()]:
                    param_var = self._build_param_var()
                    self.parameters[param_var] = expression_or_value

                    where_query = self._operators[operator].format(
                        property_var=self._build_property_var(), param_var=param_var
                    )
                    where_queries.append(where_query)
                case "$patterns":
                    for pattern in expression_or_value:
                        where_queries.append(self._patterns_operator(expression=pattern))
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
                normalized[index] = self._normalize_expressions(expressions=expression, level=level + 1)
        elif isinstance(normalized, dict):
            for operator, expression in normalized.items():
                # Handle $relationships operators
                if operator == "$relationships":
                    for index, relationship_expression in enumerate(expression):
                        normalized[operator][index] = self._normalize_expressions(
                            expressions=relationship_expression, level=0
                        )
                # Handle $node operator
                elif operator == "$node":
                    normalized[operator] = self._normalize_expressions(expressions=expression, level=0)
                # Handle $patterns operator
                elif operator == "$patterns":
                    for index, pattern in enumerate(expression):
                        if "$node" in pattern:
                            normalized[operator][index]["$node"] = self._normalize_expressions(
                                expressions=pattern["$node"], level=0
                            )

                        if "$relationship" in pattern:
                            normalized[operator][index]["$relationship"] = self._normalize_expressions(
                                expressions=pattern["$relationship"], level=0
                            )
                else:
                    normalized[operator] = self._normalize_expressions(expressions=expression, level=level + 1)

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

        return f"ALL(i IN labels({self.ref}) WHERE i IN ${param_var})"

    def _type_operator(self, types: Union[str, List[str]]) -> str:
        """
        Builds the query for the `$type` operator.

        Args:
            types (Union[str, List[str]]): Relationship types to match by.

        Returns:
            str: The operator query.
        """
        param_var = self._build_param_var()
        self.parameters[param_var] = types

        if isinstance(types, str):
            return f"type({self.ref}) = ${param_var}"

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
        Builds the query for the `$and` operator.

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
        Builds the query for the `$or` operator.

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
        Builds the query for the `$xor` operator.

        Args:
            expressions (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        xor_queries: List[str] = []

        for expression in expressions:
            xor_queries.append(self._build_query(filters=expression))

        return f"({' XOR '.join(xor_queries)})"

    def _patterns_operator(self, expression: Dict[str, Any]) -> str:
        """
        Builds the query for the `$patterns` operator.

        Args:
            expression (Dict[str, Any]): The provided expression for the operator.

        Returns:
            str: The operator query.
        """
        original_ref = deepcopy(self.ref)
        where_queries: List[str] = []

        relationship_ref = self._build_param_var()
        node_ref = self._build_param_var()

        # Build node queries
        self.ref = node_ref
        node_queries = self._build_query(filters=expression["$node"])

        if node_queries != "":
            where_queries.append(node_queries)

        # Build relationship queries
        self.ref = relationship_ref
        relationship_queries = self._build_query(filters=expression["$relationship"])

        if relationship_queries != "":
            where_queries.append(relationship_queries)

        self.ref = original_ref

        # Build final queries
        match_query = self.relationship_match(
            ref=relationship_ref,
            start_node_ref=self.ref,
            end_node_ref=node_ref,
            direction=expression["$direction"],
        )
        exists_query = "NOT EXISTS" if expression["$not"] else "EXISTS"
        where_query = " AND ".join(where_queries) if len(where_queries) > 0 else ""

        return (
            f"{exists_query} {{MATCH {match_query} {f'WHERE {where_query}' if where_query != '' else where_queries}}}"
        )

    def _build_param_var(self) -> str:
        """
        Builds a new parameter variable name. This method exists to ensure no duplicate variable
        names occur when using the builder.

        Returns:
            str: The unique variable name.
        """
        param_var = f"_n_{self._parameter_indent}"

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
