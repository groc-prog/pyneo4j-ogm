"""
This module holds the `RelationshipProperty` class which can be used to make relationship related methods available
on a `NodeModel` models field.
"""
import logging
from typing import Any, Dict, List, Type, TypeVar

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
from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.queries.types import RelationshipDirection, TypedPropertyExpressions, TypedQueryOptions

T = TypeVar("T", bound=NodeModel)
U = TypeVar("U", bound=RelationshipModel)


class RelationshipProperty:
    """
    Class used to define relationships between the model this class is used on and a target node, which defines the
    other end of the relationship.
    """

    _client: Neo4jClient
    _query_builder: QueryBuilder
    _target_model: Type[T]
    _target_model_name: str
    _source_node: T
    _direction: RelationshipDirection
    _relationship_model: Type[U]
    _relationship_model_name: str
    _allow_multiple: bool

    def __init__(
        self,
        target_model: Type[T] | str,
        relationship_model: Type[U] | str,
        direction: RelationshipDirection,
        allow_multiple: bool = False,
    ) -> None:
        """
        Verifies that the defined target model has been registered with the client. If not, a `UnregisteredModel`
        will be raised.

        Args:
            target_model (Type[T] | str): The model which is the target of the relationship. Can be a
                model class or a string which matches the name of the model class.
            direction (RelationshipDirection): The relationship direction.
            relationship_model (Type[U] | str): The relationship model or the relationship type as a string.
            direction (RelationshipDirection): The direction of the relationship.
            allow_multiple (bool): Whether to use `MERGE` when creating new relationships. Defaults to False.

        Raises:
            UnregisteredModel: Raised if the target model or the relationship model have not been registered with the
                client.
        """
        self._allow_multiple = allow_multiple
        self._direction = direction
        self._relationship_model_name = (
            relationship_model if isinstance(relationship_model, str) else relationship_model.__name__
        )
        self._target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

    async def relationship(self, node: T) -> U | Dict[str, Any] | None:
        """
        Gets the relationship between the current node instance and the provided node. If the nodes are not connected
        the defined relationship, `None` will be returned.

        Args:
            node (T): The node to which to get the relationship.

        Returns:
            (U | Dict[str, Any] | None): Returns a `relationship model instance` describing relationship between
                the nodes or a `dictionary` if the relationship model has not been registered or `None` if no
                relationship exists between the two.
        """
        self._ensure_alive(node)

        logging.info(
            "Getting relationship between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.build_relationship_query(
            direction=self._direction,
            relationship_type=getattr(self._relationship_model.__model_settings__, "type"),
            start_node_labels=getattr(self._source_node.__model_settings__, "labels"),
            end_node_labels=getattr(node.__model_settings__, "labels"),
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $startId AND elementId(end) = $endId
                RETURN r
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
                "endId": getattr(node, "_element_id", None),
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None
        return results[0][0]

    async def connect(self, node: T, properties: Dict[str, Any]) -> U | Dict[str, Any]:
        """
        Connects the given node to the source node. By default only one relationship will be created between nodes.
        If `allow_multiple` has been set to `True` and a relationship already exists between the nodes, a duplicate
        relationship will be created.

        Args:
            node (T): Node instance to create a relationship to.
            properties (Dict[str, Any]): Properties defined on the relationship model. If no model has been provided,
                the properties will be omitted.

        Raises:
            NoResultsFound: Raised if the query did not return the new relationship.

        Returns:
            U | Dict[str, Any]: The created relationship.
        """
        self._ensure_alive(node)

        logging.info(
            "Creating relationship between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        relationship_query = self._query_builder.build_relationship_query(
            direction=self._direction,
            relationship_type=getattr(self._relationship_model.__model_settings__, "type"),
            start_node_labels=getattr(self._source_node.__model_settings__, "labels"),
            end_node_labels=getattr(node.__model_settings__, "labels"),
        )

        # Build properties if relationship is defined as model
        deflated_properties: Dict[str, Any] = self._relationship_model.deflate(properties)

        # Build MERGE/CREATE part of query depending on if duplicate relationships are allowed or not
        logging.debug("Building create/merge query")
        if self._allow_multiple:
            build_query = f"""
                CREATE {relationship_query}
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties])}
            """
        else:
            build_query = f"""
                MERGE {relationship_query}
                ON CREATE
                    SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties])}
            """

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {relationship_query}
                WHERE elementId(start) = $startId AND elementId(end) = $endId
                {build_query}
                RETURN r
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
                "endId": getattr(node, "_element_id", None),
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

        logging.info(
            "Deleting relationships between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.build_relationship_query(
            direction=self._direction,
            relationship_type=getattr(self._relationship_model.__model_settings__, "type"),
            start_node_labels=getattr(self._source_node.__model_settings__, "labels"),
            end_node_labels=getattr(node.__model_settings__, "labels"),
        )

        logging.debug("Getting relationship count between source and target node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $startId AND elementId(end) = $endId
                RETURN count(r)
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
                "endId": getattr(node, "_element_id", None),
            },
            resolve_models=False,
        )

        if len(count_results) == 0 or len(count_results[0]) == 0 or count_results[0][0] is None:
            logging.debug(
                "No relationships found between source node %s and target node %s",
                getattr(self._source_node, "_element_id", None),
                getattr(node, "_element_id", None),
            )
            return 0

        logging.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $startId AND elementId(end) = $endId
                DELETE r
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
                "endId": getattr(node, "_element_id", None),
            },
        )

        return count_results[0][0]

    async def disconnect_all(self) -> int:
        """
        Disconnects all nodes.

        Returns:
            int: The number of disconnected nodes.
        """
        logging.info(
            "Deleting all relationships associated with source node %s", getattr(self._source_node, "_element_id", None)
        )
        match_query = self._query_builder.build_relationship_query(
            direction=self._direction,
            relationship_type=getattr(self._relationship_model.__model_settings__, "type"),
            start_node_labels=getattr(self._source_node.__model_settings__, "labels"),
        )

        logging.debug("Getting relationship count for source node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $startId
                RETURN count(r)
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
            },
            resolve_models=False,
        )

        if len(count_results) == 0 or len(count_results[0]) == 0 or count_results[0][0] is None:
            logging.debug("No relationships found for source node %s", getattr(self._source_node, "_element_id", None))
            return 0

        logging.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $startId
                DELETE r
            """,
            parameters={
                "startId": getattr(self._source_node, "_element_id", None),
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

        logging.info(
            "Replacing old node %s with new node %s",
            getattr(old_node, "_element_id", None),
            getattr(new_node, "_element_id", None),
        )
        relationship = await self.relationship(node=old_node)

        if relationship is None:
            raise NotConnectedToSourceNode()

        deflated_properties = (
            relationship if not issubclass(relationship, RelationshipModel) else relationship.deflate()
        )

        await self.disconnect(node=old_node)
        new_relationship = await self.connect(node=new_node, properties=deflated_properties)

        return new_relationship

    async def find_connected_nodes(
        self, expressions: TypedPropertyExpressions | None = None, options: TypedQueryOptions | None = None
    ) -> List[T]:
        """
        Finds the all nodes that matches `expressions` and are connected to the source node.

        Args:
            expressions (TypedPropertyExpressions | None, optional): Expressions applied to the query. Defaults to None.
            options (TypedQueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T]: A list of model instances.
        """
        logging.info("Getting connected nodes matching expressions %s", expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = self._query_builder.build_node_expressions(
            expressions=expressions if expressions is not None else {}, ref="end"
        )
        match_query = self._query_builder.build_relationship_query(
            direction=self._direction,
            relationship_type=getattr(self._relationship_model.__model_settings__, "type"),
            start_node_labels=getattr(self._source_node.__model_settings__, "labels"),
        )
        options_query = self._query_builder.build_query_options(options=options if options else {}, ref="end")

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query} {f', {expression_match_query}' if expression_match_query is not None else ""}
                {expression_where_query if expression_where_query is not None else ""}
                RETURN end
                {options_query}
            """,
            parameters=expression_parameters,
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

    def _build_property(self, source_model: Type[T]) -> None:
        """
        Sets the source node and returns self.

        Args:
            source_model (T): The source model instance.

        Raises:
            UnregisteredModel: Raised if the source model has not been registered with the client.
        """
        self._client = Neo4jClient()

        logging.debug("Checking if source model %s has been registered with client", source_model.__name__)
        if source_model not in self._client.models:
            raise UnregisteredModel(unregistered_model=source_model.__name__)

        self._source_node = source_model

        logging.debug("Checking if target model %s has been registered with client", self._target_model_name)
        registered_relationship_model = [
            model for model in self._client.models if model.__name__ == self._target_model_name
        ]
        if len(registered_relationship_model) == 0:
            raise UnregisteredModel(unregistered_model=self._target_model_name)

        self._target_model = registered_relationship_model

        logging.debug(
            "Checking if relationship model %s has been registered with client", self._relationship_model_name
        )
        registered_relationship_model = [
            model for model in self._client.models if model.__name__ == self._relationship_model_name
        ]
        if len(registered_relationship_model) == 0:
            raise UnregisteredModel(unregistered_model=self._relationship_model_name)

        self._relationship_model = registered_relationship_model

        return self

    def _ensure_alive(self, nodes: T | List[T]) -> None:
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
            logging.debug("Checking if node %s is alive and of correct type", getattr(node, "_element_id", None))
            if getattr(node, "_element_id", None) is None:
                raise InstanceNotHydrated()

            if getattr(node, "_destroyed", True):
                raise InstanceDestroyed()

            if self._target_model.__name__ != node.__class__.__name__:
                raise InvalidTargetNode(expected_type=self._target_model.__name__, actual_type=node.__class__.__name__)
