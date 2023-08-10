"""
Relationship property class used to define relationships between the model this class is used on and a target node,
which defines the other end of the relationship.
"""
from enum import Enum
from typing import Any, Dict, Generic, List, Type, TypeVar, Union, cast

from neo4j.graph import Node

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipModel
from neo4j_ogm.exceptions import (
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidTargetNode,
    NoResultsFound,
    NotConnectedToSourceNode,
    UnregisteredModel,
)
from neo4j_ogm.logger import logger
from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.queries.types import QueryOptions, RelationshipPropertyFilters

T = TypeVar("T", bound=NodeModel)
U = TypeVar("U", bound=RelationshipModel)


class RelationshipPropertyDirection(str, Enum):
    """
    Available relationship directions for relationship properties.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class RelationshipProperty(Generic[T, U]):
    """
    Class used to define relationships between the model this class is used on and a target node, which defines the
    other end of the relationship.

    Accepts two generic types, the first being the target node and the second being the relationship model.
    """

    _client: Neo4jClient
    _query_builder: QueryBuilder
    _target_model: Type[T]
    _target_model_name: str
    _source_node: T
    _direction: RelationshipPropertyDirection
    _relationship_model: Type[U]
    _relationship_model_name: str
    _allow_multiple: bool
    _nodes: List[T]

    def __init__(
        self,
        target_model: Union[Type[T], str],
        relationship_model: Union[Type[U], str],
        direction: RelationshipPropertyDirection,
        allow_multiple: bool = False,
    ) -> None:
        """
        Verifies that the defined target model has been registered with the client. If not, a `UnregisteredModel`
        will be raised.

        Args:
            target_model (Type[T] | str): The model which is the target of the relationship. Can be a
                model class or a string which matches the name of the model class.
            direction (RelationshipPropertyDirection): The relationship direction.
            relationship_model (Type[U] | str): The relationship model or the relationship type as a string.
            direction (RelationshipPropertyDirection): The direction of the relationship.
            allow_multiple (bool): Whether to use `MERGE` when creating new relationships. Defaults to False.

        Raises:
            UnregisteredModel: Raised if the target model or the relationship model have not been registered with the
                client.
        """
        self._nodes = []
        self._allow_multiple = allow_multiple
        self._direction = direction
        self._relationship_model_name = (
            relationship_model if isinstance(relationship_model, str) else relationship_model.__name__
        )
        self._target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

    async def relationship(self, node: T) -> Union[U, None]:
        """
        Gets the relationship between the current node instance and the provided node. If the nodes are not connected
        the defined relationship, `None` will be returned.

        Args:
            node (T): The node to which to get the relationship.

        Returns:
            (U | None): Returns a `relationship model instance` describing relationship between
                the nodes  or `None` if no relationship exists between the two.
        """
        self._ensure_alive(node)

        logger.info("Getting relationship between target node %s and source node %s", node, self._source_node)
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            start_node_labels=self._source_node.__settings__.labels,
            end_node_ref="end",
            end_node_labels=self._target_model.__settings__.labels,
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None
        return results[0][0]

    async def connect(self, node: T, properties: Union[Dict[str, Any], None] = None) -> U:
        """
        Connects the given node to the source node. By default only one relationship will be created between nodes.
        If `allow_multiple` has been set to `True` and a relationship already exists between the nodes, a duplicate
        relationship will be created.

        Args:
            node (T): Node instance to create a relationship to.
            properties (Dict[str, Any] | None): Properties defined on the relationship model. Defaults to None.

        Raises:
            NoResultsFound: Raised if the query did not return the new relationship.

        Returns:
            U: The created relationship.
        """
        self._ensure_alive(node)

        logger.info(
            "Creating relationship between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )

        # Build properties if relationship is defined as model
        relationship_instance = self._relationship_model.validate(properties if properties is not None else {})
        deflated_properties: Dict[str, Any] = relationship_instance.deflate()

        relationship_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            end_node_ref="end",
        )

        # Build MERGE/CREATE part of query depending on if duplicate relationships are allowed or not
        logger.debug("Building queries")
        if self._allow_multiple:
            build_query = f"CREATE {relationship_query}"
        else:
            build_query = f"MERGE {relationship_query}"

        set_query = (
            f"SET {', '.join([f'r.{property_name} = ${property_name}' for property_name in deflated_properties])}"
            if len(deflated_properties.keys()) != 0
            else ""
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH
                    {self._query_builder.node_match(ref="start")},
                    {self._query_builder.node_match(ref="end")}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                {build_query}
                {set_query}
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
                **deflated_properties,
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()
        return results[0][0]

    async def disconnect(self, node: T) -> int:
        """
        Disconnects the provided node from the source node. If the nodes are `not connected`, the query will not modify
        any of the nodes and `return 0`. If multiple relationships exists, all will be deleted.

        Args:
            node (T): The node to disconnect.

        Returns:
            int: The number of disconnected nodes.
        """
        self._ensure_alive(node)

        logger.info(
            "Deleting relationships between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            start_node_labels=self._source_node.__settings__.labels,
            end_node_ref="end",
            end_node_labels=self._target_model.__settings__.labels,
        )

        logger.debug("Getting relationship count between source and target node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN count(r)
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
            },
            resolve_models=False,
        )

        if len(count_results) == 0 or len(count_results[0]) == 0 or count_results[0][0] is None:
            logger.debug(
                "No relationships found between source node %s and target node %s",
                getattr(self._source_node, "_element_id", None),
                getattr(node, "_element_id", None),
            )
            return 0

        logger.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
            },
        )

        return count_results[0][0]

    async def disconnect_all(self) -> int:
        """
        Disconnects all nodes.

        Returns:
            int: The number of disconnected nodes.
        """
        logger.info(
            "Deleting all relationships associated with source node %s",
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            start_node_labels=self._source_node.__settings__.labels,
            end_node_ref="end",
            end_node_labels=self._target_model.__settings__.labels,
        )

        logger.debug("Getting relationship count for source node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id
                RETURN count(r)
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
            },
            resolve_models=False,
        )

        if len(count_results) == 0 or len(count_results[0]) == 0 or count_results[0][0] is None:
            logger.debug(
                "No relationships found for source node %s",
                getattr(self._source_node, "_element_id", None),
            )
            return 0

        logger.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
            },
        )

        return count_results[0][0]

    async def replace(self, old_node: T, new_node: T) -> U:
        """
        Disconnects a old node and replaces it with a new node. All relationship properties will be carried over to
        the new relationship.

        Args:
            old_node (T): The currently connected node.
            new_node (T): The node which replaces the currently connected node.

        Returns:
            U: The new relationship between the source node and the newly connected node.
        """
        self._ensure_alive([old_node, new_node])

        logger.info(
            "Replacing old node %s with new node %s",
            getattr(old_node, "_element_id", None),
            getattr(new_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            start_node_labels=self._source_node.__settings__.labels,
            end_node_ref="end",
            end_node_labels=self._target_model.__settings__.labels,
        )

        logger.debug("Getting relationship between source node and old node")
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(old_node, "_element_id", None),
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NotConnectedToSourceNode()

        deflated_properties = cast(U, results[0][0]).deflate()

        logger.debug("Deleting relationship between source node and old node")
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(old_node, "_element_id", None),
            },
        )

        logger.debug("Creating relationship between source node and new node")
        create_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            end_node_ref="end",
        )

        set_query = (
            f"SET {', '.join([f'r.{property_name} = ${property_name}' for property_name in deflated_properties])}"
            if len(deflated_properties.keys()) != 0
            else ""
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH
                    {self._query_builder.node_match(labels=self._source_node.__settings__.labels, ref="start")},
                    {self._query_builder.node_match(labels=self._target_model.__settings__.labels, ref="end")}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                CREATE {create_query}
                {set_query}
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(new_node, "_element_id", None),
                **deflated_properties,
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()
        return cast(U, results[0][0])

    async def find_connected_nodes(
        self,
        filters: Union[RelationshipPropertyFilters, None] = None,
        options: Union[QueryOptions, None] = None,
    ) -> List[T]:
        """
        Finds the all nodes that matches `filters` and are connected to the source node.

        Args:
            filters (RelationshipPropertyFilters | None, optional): Expressions applied to the query. Defaults to None.
            options (QueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T]: A list of model instances.
        """
        logger.info("Getting connected nodes matching filters %s", filters)
        if filters is not None:
            self._query_builder.relationship_property_filters(filters=filters, ref="r", node_ref="end")
        if options is not None:
            self._query_builder.query_options(options=options, ref="end")

        match_query = self._query_builder.relationship_match(
            ref="r",
            direction=self._direction,
            type_=self._relationship_model.__settings__.type,
            start_node_ref="start",
            start_node_labels=self._source_node.__settings__.labels,
            end_node_ref="end",
            end_node_labels=self._target_model.__settings__.labels,
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE
                    elementId(start) = $start_element_id
                    {f"AND {self._query_builder.query['where']}" if self._query_builder.query['where'] != "" else ""}
                RETURN end
                {self._query_builder.query['options']}
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                **self._query_builder.parameters,
            },
        )

        instances: List[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(results[0][0], Node):
                    instances.append(self._target_model.inflate(node=results[0][0]))
                else:
                    instances.append(result)

        return instances

    def _build_property(self, source_model: T) -> None:
        """
        Sets the source node and returns self.

        Args:
            source_model (T): The source model instance.

        Raises:
            UnregisteredModel: Raised if the source model has not been registered with the client.
        """
        self._client = Neo4jClient()
        self._query_builder = QueryBuilder()

        logger.debug(
            "Checking if source model %s has been registered with client",
            source_model.__class__.__name__,
        )
        if source_model.__class__ not in self._client.models:
            raise UnregisteredModel(model=source_model.__class__.__name__)

        self._source_node = source_model

        logger.debug(
            "Checking if target model %s has been registered with client",
            self._target_model_name,
        )
        registered_node_model = [model for model in self._client.models if model.__name__ == self._target_model_name]
        if len(registered_node_model) == 0:
            raise UnregisteredModel(model=source_model.__class__.__name__)

        self._target_model = registered_node_model[0]

        logger.debug(
            "Checking if relationship model %s has been registered with client",
            self._relationship_model_name,
        )
        registered_relationship_model = [
            model for model in self._client.models if model.__name__ == self._relationship_model_name
        ]
        if len(registered_relationship_model) == 0:
            raise UnregisteredModel(model=source_model.__class__.__name__)

        self._relationship_model = registered_relationship_model[0]

        return self

    @property
    def nodes(self) -> List[T]:
        """
        Auto-fetched nodes. Must set `auto_fetch_nodes` in settings or `find_one, find_many or
        find_connected_nodes` to `True` fot this to work.

        Returns:
            List[T]: The auto-fetched nodes.
        """
        return self._nodes

    def _ensure_alive(self, nodes: Union[T, List[T]]) -> None:
        """
        Ensures that the provided nodes are alive.

        Args:
            nodes (T | List[T]): Nodes to check for hydration and alive.

        Raises:
            InstanceNotHydrated: Raised if a node is not hydrated yet.
            InstanceDestroyed: Raised if a node has been marked as destroyed.
        """
        nodes_to_check = nodes if isinstance(nodes, list) else [nodes]

        for node in nodes_to_check:
            logger.debug(
                "Checking if node %s is alive and of correct type",
                getattr(node, "_element_id", None),
            )
            if getattr(node, "_element_id", None) is None:
                raise InstanceNotHydrated()

            if getattr(node, "_destroyed", True):
                raise InstanceDestroyed()

            if self._target_model.__name__ != node.__class__.__name__:
                raise InvalidTargetNode(
                    expected_type=self._target_model.__name__,
                    actual_type=node.__class__.__name__,
                )
