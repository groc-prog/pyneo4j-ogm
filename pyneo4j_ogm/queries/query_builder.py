"""
Builds parts of queries related to filters and options.
"""
from copy import deepcopy
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
    cast,
)

from pyneo4j_ogm.exceptions import InvalidRelationshipDirection, InvalidRelationshipHops
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import get_model_dump
from pyneo4j_ogm.queries.operators import Operators
from pyneo4j_ogm.queries.types import (
    MultiHopFilters,
    NodeFilters,
    Projection,
    QueryOptions,
    RelationshipFilters,
    RelationshipMatchDirection,
    RelationshipPropertyFilters,
)
from pyneo4j_ogm.queries.validators import (
    MultiHopFiltersModel,
    NodeFiltersModel,
    QueryOptionModel,
    RelationshipFiltersModel,
    RelationshipPropertyFiltersModel,
)

if TYPE_CHECKING:
    from pyneo4j_ogm.fields.relationship_property import RelationshipPropertyDirection
else:
    RelationshipPropertyDirection = object


class FilterQueries(TypedDict):
    """
    Type definition for `query` attribute.
    """

    match: str
    where: str
    options: str
    projections: str


class QueryBuilder:
    """
    Builds parts of the database query for available query filters and options.
    """

    _operator_builder: Operators = Operators()
    parameters: Dict[str, Any] = {}
    query: FilterQueries = {
        "match": "",
        "where": "",
        "projections": "",
        "options": "",
    }

    def reset_query(self) -> None:
        """
        Resets the previously generate query parts.
        """
        self.query = {
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
            ref (str, optional): The reference to the node. Defaults to `'n'`.
        """
        logger.debug("Building node filters %s", filters)
        self._operator_builder.ref = ref
        self._operator_builder.reset_state()
        normalized_filters = self._operator_builder.normalize_expressions(expressions=cast(Dict[str, Any], filters))

        # Validate filters with pydantic model
        validated_filters = NodeFiltersModel(**cast(Dict[str, Any], normalized_filters))
        validated_filters = get_model_dump(validated_filters, by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._operator_builder.remove_invalid_expressions(validated_filters)

        where_query = self._operator_builder.build_operators(filters=validated_filters)

        if where_query is not None and where_query != "":
            self.query["where"] = where_query

        self.parameters = self._operator_builder.parameters

    def relationship_filters(self, filters: RelationshipFilters, ref: str = "r") -> None:
        """
        Builds the relationship filters for the query.

        Args:
            filters (Dict[str, Any]): The filters to build.
            ref (str, optional): The reference to the relationship. Defaults to `'r'`.
        """
        logger.debug("Building relationship filters %s", filters)
        self._operator_builder.ref = ref
        self._operator_builder.reset_state()
        normalized_filters = self._operator_builder.normalize_expressions(expressions=cast(Dict[str, Any], filters))

        # Validate filters with pydantic model
        validated_filters = RelationshipFiltersModel(**cast(Dict[str, Any], normalized_filters))
        validated_filters = get_model_dump(validated_filters, by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._operator_builder.remove_invalid_expressions(validated_filters)

        where_query = self._operator_builder.build_operators(filters=validated_filters)

        if where_query is not None and where_query != "":
            self.query["where"] = where_query

        self.parameters = self._operator_builder.parameters

    def relationship_property_filters(
        self, filters: RelationshipPropertyFilters, ref: str = "r", node_ref: str = "end"
    ) -> None:
        """
        Builds the relationship and node filters for relationship property queries.

        Args:
            filters (Dict[str, Any]): The filters to build.
            ref (str, optional): The reference to the relationship. Defaults to `'r'`.
            node_ref (str, optional): The reference to the node. Defaults to `'end'`.
        """
        logger.debug("Building relationship property filters %s", filters)
        self._operator_builder.reset_state()
        normalized_filters = self._operator_builder.normalize_expressions(expressions=cast(Dict[str, Any], filters))

        # Validate filters with pydantic model
        validated_filters = RelationshipPropertyFiltersModel(**cast(Dict[str, Any], normalized_filters))
        validated_filters = get_model_dump(validated_filters, by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._operator_builder.remove_invalid_expressions(validated_filters)

        where_queries = []

        if "$relationship" in validated_filters:
            self._operator_builder.ref = ref
            where_queries.append(self._operator_builder.build_operators(filters=validated_filters["$relationship"]))

            # Remove relationship filters from validated filters before building node filters
            validated_filters.pop("$relationship")

        self._operator_builder.ref = node_ref
        where_queries.append(self._operator_builder.build_operators(filters=validated_filters))

        self.query["where"] = " AND ".join([query for query in where_queries if query != ""])
        self.parameters = self._operator_builder.parameters

    def multi_hop_filters(
        self, filters: MultiHopFilters, start_ref: str = "n", end_ref: str = "m", rel_ref: str = "r"
    ) -> None:
        """
        Builds the filters for a multi hop query.

        Args:
            filters (Dict[str, Any]): The filters to build.
            start_ref (str, optional): The reference to the start node. Defaults to `'n'`.
            end_ref (str, optional): The reference to the end node. Defaults to `'m'`.
            rel_ref (str, optional): The reference to the relationship. Defaults to `'r'`.
        """
        logger.debug("Building multi hop filters %s", filters)
        self._operator_builder.ref = start_ref
        self._operator_builder.reset_state()
        normalized_filters = self._operator_builder.normalize_expressions(expressions=cast(Dict[str, Any], filters))

        # Validate filters with pydantic model
        validated_filters = MultiHopFiltersModel(**cast(Dict[str, Any], normalized_filters))
        validated_filters = get_model_dump(validated_filters, by_alias=True, exclude_none=True)

        # Remove invalid expressions
        self._operator_builder.remove_invalid_expressions(validated_filters)

        original_ref = deepcopy(self._operator_builder.ref)

        # Build path match
        relationship_match = self.relationship_match(
            direction=validated_filters["$direction"]
            if "$direction" in validated_filters
            else RelationshipMatchDirection.OUTGOING,
            start_node_ref=start_ref,
            end_node_ref=end_ref,
            min_hops=validated_filters["$minHops"] if "$minHops" in validated_filters else None,
            max_hops=validated_filters["$maxHops"] if "$maxHops" in validated_filters else None,
        )
        self.query["match"] = f", path = {relationship_match}"

        # Build node filters
        self._operator_builder.ref = end_ref
        where_node_query = (
            self._operator_builder.build_operators(filters=validated_filters["$node"])
            if "$node" in validated_filters
            else ""
        )

        # Build relationship filters
        where_relationship_queries: Dict[str, str] = {}
        self._operator_builder.ref = rel_ref

        if "$relationships" in validated_filters:
            for relationship in validated_filters["$relationships"]:
                relationship_type = relationship["$type"]

                relationship_filters = deepcopy(relationship)
                cast(Dict[str, Any], relationship_filters).pop("$type")
                build_filters = self._operator_builder.build_operators(filters=relationship_filters)

                if build_filters != "" and build_filters is not None:
                    where_relationship_queries[relationship_type] = build_filters

        # Build WHERE query
        relationship_where_query = ""

        if len(where_relationship_queries.keys()) > 0:
            relationship_where_query = f"""
                ALL({rel_ref} IN relationships(path) WHERE
                    CASE type({rel_ref})
                        {" ".join([f"WHEN '{relationship_name}' THEN {relationship_query}" for relationship_name, relationship_query in where_relationship_queries.items()])}
                        ELSE true
                    END
                )"""

        self._operator_builder.ref = original_ref

        chain_with_and = " AND " if where_node_query != "" and relationship_where_query != "" else ""
        self.query["where"] = f"{where_node_query}{chain_with_and}{relationship_where_query}"
        self.parameters = self._operator_builder.parameters

    def query_options(self, options: QueryOptions, ref: str = "n") -> None:
        """
        Builds the query options for the query.

        Args:
            options (QueryOptions): The options to build.
            ref (str, optional): The reference to the node or relationship. Defaults to `'n'`.
        """
        logger.debug("Building query options %s", options)

        # Validate options with pydantic model
        validated_options = QueryOptionModel(**cast(Dict[str, Any], options))
        validated_options = get_model_dump(validated_options, exclude_none=True)

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
        normalized_labels = [label for label in labels if label != ""] if labels is not None else []

        node_ref = ref if ref is not None else ""
        node_labels = (
            f":{':'.join(normalized_labels)}" if normalized_labels is not None and len(normalized_labels) > 0 else ""
        )

        return f"({node_ref}{node_labels})"

    def relationship_match(
        self,
        ref: Optional[str] = "r",
        type_: Optional[str] = None,
        direction: Union[RelationshipMatchDirection, RelationshipPropertyDirection] = RelationshipMatchDirection.BOTH,
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
            ref (str, optional): The reference to the relationship. Defaults to `'r'`.
            start_node_ref (Optional[str], optional): The reference to the start node. Defaults to `None`.
            start_node_labels (Optional[List[str]], optional): The labels of the start node. Defaults to `None`.
            end_node_ref (Optional[str], optional): The reference to the end node. Defaults to `None`.
            end_node_labels (Optional[List[str]], optional): The labels of the end node. Defaults to `None`.
            min_hops (Optional[Union[int, str]], optional): The minimum number of hops. Defaults to `None`.
            max_hops (Optional[Union[int, str]], optional): The maximum number of hops. Defaults to `None`.

        Raises:
            InvalidRelationshipHops: If the min_hops or max_hops are invalid.

        Returns:
            str: The relationship to match.
        """
        from pyneo4j_ogm.fields.relationship_property import (
            RelationshipPropertyDirection,
        )

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
        relationship_type = f":{type_}" if type_ is not None and type_ != "" else ""
        relationship_match = f"[{relationship_ref}{relationship_type}{hops}]"

        match direction:
            case RelationshipMatchDirection.INCOMING | RelationshipPropertyDirection.INCOMING:
                return f"{start_node_match}<-{relationship_match}-{end_node_match}"
            case RelationshipMatchDirection.OUTGOING | RelationshipPropertyDirection.OUTGOING:
                return f"{start_node_match}-{relationship_match}->{end_node_match}"
            case RelationshipMatchDirection.BOTH:
                return f"{start_node_match}-{relationship_match}-{end_node_match}"
            case _:
                raise InvalidRelationshipDirection(direction)

    def build_projections(self, projections: Projection, ref: str = "n") -> None:
        """
        Builds a projection which only returns the node properties defined in the projection.

        Args:
            ref (str): The reference to the node. Defaults to `'n'`.
            projections (Projection): The projections to build.
        """
        if not isinstance(projections, dict):
            return

        projection_queries: List[str] = []

        for projection, property_name in projections.items():
            if property_name == "$elementId":
                projection_queries.append(f"{str(projection)}: elementId({ref})")
            elif property_name == "$id":
                projection_queries.append(f"{str(projection)}: ID({ref})")
            else:
                projection_queries.append(f"{str(projection)}: {ref}.{str(property_name)}")

        if len(projection_queries) > 0:
            self.query["projections"] = (
                f"""WITH DISTINCT {ref}
                RETURN DISTINCT collect({{{', '.join(projection_queries)}}})"""
                if len(projection_queries) > 0
                else ""
            )
