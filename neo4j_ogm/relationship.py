"""
This module holds the base relationship class `Neo4jRelationship` which is used to define database models for
relationships between nodes.
"""
import json
import logging
from typing import Any, Callable, TypeVar, cast

from neo4j.graph import Node, Relationship
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.exceptions import InflationFailure, InstanceNotHydrated, UnexpectedEmptyResult
from neo4j_ogm.query_builder import QueryBuilder
from neo4j_ogm.utils import RelationshipDirection, build_relationship_match_clause, ensure_alive

T = TypeVar("T", bound="Neo4jRelationship")


def ensure_connections(func: Callable):
    """
    Decorator which ensures that a relationship has both start- and end nodes defined.

    Raises:
        InstanceDestroyed: Raised if the method is called on a instance which has been destroyed
    """

    async def decorator(self: T, *args, **kwargs):
        if getattr(self, "_start_node", None) is None or getattr(self, "_end_node", None) is None:
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class Neo4jRelationship(BaseModel):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __type__: str
    __dict_fields = set()
    __model_fields = set()
    _destroyed: bool = False
    _client = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr(default=QueryBuilder())
    _modified_fields: set[str] = PrivateAttr(default=set())
    _start_node: Node | None = PrivateAttr(default=None)
    _end_node: Node | None = PrivateAttr(default=None)
    _element_id: str | None = PrivateAttr(default=None)
    _direction: RelationshipDirection = PrivateAttr()

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models fields for serialization.
        """
        # Check if relationship type is set, if not fall back to model name
        from neo4j_ogm.client import Neo4jClient

        cls._client = Neo4jClient()

        if not hasattr(cls, "__type__"):
            cls.__type__ = cls.__name__

        for field, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if field is of type None
            if value.type_ is not None:
                if issubclass(value.type_, dict):
                    cls.__dict_fields.add(field)
                elif issubclass(value.type_, BaseModel):
                    cls.__model_fields.add(field)

        return super().__init_subclass__()

    def deflate(self) -> dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            dict[str, Any]: The deflated model instance
        """
        logging.debug("Deflating model to storable dictionary")
        deflated: dict[str, Any] = json.loads(self.json())

        # Serialize nested BaseModel or dict instances to JSON strings
        logging.debug("Serializing nested dictionaries to JSON strings")
        for field in self.__dict_fields:
            deflated[field] = json.dumps(deflated[field])

        logging.debug("Serializing nested models to JSON strings")
        for field in self.__model_fields:
            deflated[field] = self.__dict__[field].json()

        return deflated

    @classmethod
    def inflate(cls, relationship: Relationship) -> T:
        """
        Inflates a relationship instance into a instance of the current model.

        Args:
            relationship (Relationship): Relationship to inflate

        Raises:
            InflationFailure: Raised if inflating the relationship fails

        Returns:
            T: A new instance of the current model with the properties from the relationship instance
        """
        inflated: dict[str, Any] = {}

        logging.debug("Inflating relationship to model instance")
        for relationship_property in relationship.items():
            property_name, property_value = relationship_property

            if property_name in cls.__dict_fields or property_name in cls.__model_fields:
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        return cls(
            _element_id=relationship.element_id,
            _start_node=relationship.start_node,
            _end_node=relationship.end_node,
            **inflated,
        )

    @ensure_alive
    @ensure_connections
    async def update(self) -> None:
        """
        Updates the corresponding relationship in the database with the current instance values.

        Raises:
            UnexpectedEmptyResult: Raised if the query did not return the updated node
        """
        deflated = self.deflate()

        logging.debug(
            "Updating relationship %s of model %s with current properties %s",
            self._element_id,
            self.__class__.__name__,
            deflated,
        )
        results, _ = await self._client.cypher(
            query=f"""
                {build_relationship_match_clause(
                    self._direction,
                    cast(Node, self._start_node),
                    cast(Node, self._end_node),
                    relationship_type=self.__type__
                )}
                WHERE
                    elementId(start) = $start_element_id
                    AND elementId(end) = $end_element_id
                    AND elementId(rel) = $rel_element_id
                SET {", ".join([f"rel.{field} = ${field}" for field in self._modified_fields])}
                RETURN rel
            """,
            parameters={
                "start_element_id": cast(Node, self._start_node).element_id,
                "end_element_id": cast(Node, self._end_node).element_id,
                "rel_element_id": self._element_id,
                **deflated,
            },
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0:
            raise UnexpectedEmptyResult()

        # Reset _modified_fields
        self._modified_fields.clear()

    @ensure_alive
    @ensure_connections
    async def delete(self) -> None:
        """
        Deletes the corresponding relationship in the database marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised
        """
        logging.debug("Deleting node %s of model %s", self._element_id, self.__class__.__name__)
        await self._client.cypher(
            query=f"""
                {build_relationship_match_clause(
                    self._direction,
                    cast(Node, self._start_node),
                    cast(Node, self._end_node),
                    relationship_type=self.__type__
                )}
                WHERE
                    elementId(start) = $start_element_id
                    AND elementId(end) = $end_element_id
                    AND elementId(rel) = $rel_element_id
                DELETE rel
            """,
            parameters={
                "start_element_id": cast(Node, self._start_node).element_id,
                "end_element_id": cast(Node, self._end_node).element_id,
                "rel_element_id": self._element_id,
            },
        )

        logging.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
