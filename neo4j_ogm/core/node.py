"""
This module holds the base node class `Neo4jNode` which is used to define database models for nodes.
"""
import json
import logging
from typing import Any, TypeVar, cast

from neo4j.graph import Node
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.exceptions import InflationFailure, UnexpectedEmptyResult
from neo4j_ogm.core.utils import ensure_alive, validate_instance

T = TypeVar("T", bound="Neo4jNode")


class Neo4jNode(BaseModel):
    """
    Base model for all node models. Every node model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __labels__: tuple[str]
    __dict_fields = set()
    __model_fields = set()
    _client: Neo4jClient = PrivateAttr()
    _modified_fields: set[str] = PrivateAttr(default=set())
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: str | None = PrivateAttr(default=None)

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models fields for serialization.
        """
        # Check if relationship type is set, if not fall back to model name
        if not hasattr(cls, "__labels__"):
            cls.__labels__ = tuple(cls.__name__)

        logging.debug("Initializing client for model %s", cls.__name__)
        cls._client = Neo4jClient()

        for field, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if field is of type None
            if value.type_ is not None:
                if issubclass(value.type_, dict):
                    cls.__dict_fields.add(field)
                elif issubclass(value.type_, BaseModel):
                    cls.__model_fields.add(field)

        return super().__init_subclass__()

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__fields__ and not name.startswith("_"):
            self._modified_fields.add(name)
        return super().__setattr__(name, value)

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
    def inflate(cls, node: Node) -> T:
        """
        Inflates a node instance into a instance of the current model.

        Args:
            node (Node): Node to inflate

        Raises:
            InflationFailure: Raised if inflating the node fails

        Returns:
            T: A new instance of the current model with the properties from the node instance
        """
        inflated: dict[str, Any] = {}

        logging.debug("Inflating node to model instance")
        for relationship_property in node.items():
            property_name, property_value = relationship_property

            if property_name in cls.__dict_fields or property_name in cls.__model_fields:
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        return cls(_element_id=node.element_id, **inflated)

    @validate_instance
    async def create(self) -> None:
        """
        Creates a new node from the current instance. After the method is finished, a newly created
        instance is seen as `alive`.

        Raises:
            UnexpectedEmptyResult: Raised if the query did not return the created node
        """
        logging.debug("Creating new node from model instance %s", self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                CREATE (n:{":".join(self.__labels__)} $properties)
                RETURN n
            """,
            parameters={
                "properties": self.deflate(),
            },
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0:
            raise UnexpectedEmptyResult()

        logging.debug("Hydrating instance values")
        setattr(self, "_element_id", cast(Node, results[0][0]).element_id)

    @ensure_alive
    @validate_instance
    async def update(self) -> None:
        """
        Updates the corresponding node in the database with the current instance values.

        Raises:
            UnexpectedEmptyResult: Raised if the query did not return the updated node
        """
        deflated = self.deflate()

        logging.debug(
            "Updating node %s of model %s with current properties %s",
            self._element_id,
            self.__class__.__name__,
            deflated,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH (n:{":".join(self.__labels__)})
                WHERE elementId(n) = $element_id
                SET {", ".join([f"n.{field} = ${field}" for field in self._modified_fields])}
                RETURN n
            """,
            parameters={"element_id": self._element_id, **deflated},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0:
            raise UnexpectedEmptyResult()

        # Reset _modified_fields
        self._modified_fields.clear()

    @ensure_alive
    async def delete(self) -> None:
        """
        Deletes the corresponding node in the database and marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised.
        """
        logging.debug("Deleting node %s of model %s", self._element_id, self.__class__.__name__)
        await self._client.cypher(
            query=f"""
                MATCH (n:{":".join(self.__labels__)})
                WHERE elementId(n) = $element_id
                DETACH DELETE n
            """,
            parameters={"element_id": self._element_id},
        )

        logging.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
