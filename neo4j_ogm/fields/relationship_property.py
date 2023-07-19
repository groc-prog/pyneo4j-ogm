"""
This module holds the `RelationshipProperty` class which can be used to make relationship related methods available
on a `NodeModel` models field.
"""
import logging
from typing import Any, Dict, List, Type

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.core.relationship import RelationshipDirection, RelationshipModel
from neo4j_ogm.exceptions import InstanceDestroyed, InstanceNotHydrated, InvalidTargetNode, UnregisteredModel
from neo4j_ogm.queries.query_builder import QueryBuilder


class RelationshipProperty:
    """
    Class used to define relationships between the model this class is used on and a target node, which defines the
    other end of the relationship.
    """

    _client: Neo4jClient
    _query_builder: QueryBuilder
    _target_model: Type[NodeModel]
    _source_node: NodeModel
    _direction: RelationshipDirection
    _relationship: Type[RelationshipModel] | str
    _relationship_is_model: bool = False

    def __init__(
        self,
        target_model: Type[NodeModel] | str,
        relationship: Type[RelationshipModel] | str,
        direction: RelationshipDirection,
    ) -> None:
        """
        Verifies that the defined target model has been registered with the client. If not, a `UnregisteredModel`
        will be raised.

        Args:
            target_model (Type[NodeModel] | str): The model which is the target of the relationship. Can be a
                model class or a string which matches the name of the model class.
            relationship (Type[RelationshipModel] | str): The relationship model or the relationship type as a string.
            direction (RelationshipDirection): The direction of the relationship.

        Raises:
            UnregisteredModel: Raised if the target model or the relationship model have not been registered with the client.
        """
        self._client = Neo4jClient()

        # Check if target model has been registered with client
        target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

        logging.debug("Checking if target model %s has been registered with client", target_model_name)
        registered_target_model = [model for model in self._client.models if model.__name__ == target_model_name]
        if len(registered_target_model) == 0:
            raise UnregisteredModel(unregistered_model=target_model_name)

        if issubclass(relationship, RelationshipModel):
            if relationship not in self._client.models:
                raise UnregisteredModel(unregistered_model=relationship.__name__)
            else:
                self._relationship_is_model = True

        self._target_model = registered_target_model
        self._direction = direction

    def _build_property(self, source_model: NodeModel) -> None:
        """
        Sets the source node and returns self.

        Args:
            source_model (NodeModel): The source model instance.

        Raises:
            UnregisteredModel: Raised if the source model has not been registered with the client.
        """
        logging.debug("Checking if source model %s has been registered with client", source_model.__class__.__name__)
        if source_model.__class__ not in self._client.models:
            raise UnregisteredModel(unregistered_model=source_model.__name__)

        self._source_node = source_model
        return self

    async def relationship(self, node: NodeModel) -> RelationshipModel | Dict[str, Any] | None:
        """
        Gets the relationship between the current node instance and the provided node. If the nodes are not connected
        the defined relationship, `None` will be returned.

        Args:
            node (NodeModel): The node to which to get the relationship.

        Returns:
            (RelationshipModel | None): Returns a `relationship model instance` describing relationship between
                the nodes or a `dictionary` if the relationship model has not been registered or `None` if no
                relationship exists between the two.
        """
        self._ensure_alive(node)

        logging.info(
            "Getting relationship between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.build_relationship_match(
            direction=self._direction,
            relationship_type=self._relationship.__type__ if self._relationship_is_model else self._relationship,
            start_node_labels=self._source_node.__labels__,
            end_node_labels=node.__labels__,
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

    def _ensure_alive(self, nodes: NodeModel | List[NodeModel]) -> None:
        """
        Ensures that the provided nodes are alive.

        Args:
            nodes (NodeModel | List[NodeModel]): Nodes to check for hydration and alive.

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
