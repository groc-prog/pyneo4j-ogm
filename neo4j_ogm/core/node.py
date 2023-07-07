"""
This module holds the base node class `Neo4jNode` which is used to define database models for nodes.
"""
import json
import logging
from typing import Any, Type, TypeVar, cast

from neo4j.graph import Node
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.core.client import EntityTypes, IndexTypes, Neo4jClient
from neo4j_ogm.exceptions import InflationFailure, UnexpectedEmptyResult
from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.utils import ensure_alive

T = TypeVar("T", bound="Neo4jNode")


class Neo4jNode(BaseModel):
    """
    Base model for all node models. Every node model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __model_type__: str = "NODE"
    __labels__: tuple[str]
    __dict_properties = set()
    __model_properties = set()
    _client: Neo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _modified_properties: set[str] = PrivateAttr(default=set())
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: str | None = PrivateAttr(default=None)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        for _, property_name in self.__dict__.items():
            if hasattr(property_name, "build_source"):
                property_name.build_source(self.__class__)

    async def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models properties for serialization.
        """
        # Check if node labels is set, if not fall back to model name
        cls._client = Neo4jClient()
        cls._query_builder = QueryBuilder()

        if not hasattr(cls, "__labels__"):
            logging.warning("No labels have been defined for model %s, using model name as label", cls.__name__)
            cls.__labels__ = tuple(cls.__name__)

        logging.debug("Collecting dict and model fields")
        for property_name, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if property_name is of type None
            if value.type_ is not None:
                if issubclass(value.type_, dict):
                    cls.__dict_properties.add(property_name)
                elif issubclass(value.type_, BaseModel):
                    cls.__model_properties.add(property_name)

        return super().__init_subclass__()

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__fields__ and not name.startswith("_"):
            logging.debug("Adding %s to modified properties", name)
            self._modified_properties.add(name)

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
        for property_name in self.__dict_properties:
            deflated[property_name] = json.dumps(deflated[property_name])

        logging.debug("Serializing nested models to JSON strings")
        for property_name in self.__model_properties:
            deflated[property_name] = self.__dict__[property_name].json()

        return deflated

    @classmethod
    def inflate(cls: Type[T], node: Node) -> T:
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
        for node_property in node.items():
            property_name, property_value = node_property

            if property_name in cls.__dict_properties or property_name in cls.__model_properties:
                logging.debug("Inflating models and dict properties")
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    logging.error("Failed to inflate property %s of model %s", property_name, cls.__name__)
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        return cls(_element_id=node.element_id, **inflated)

    async def create(self) -> None:
        """
        Creates a new node from the current instance. After the method is finished, a newly created
        instance is seen as `alive`.

        Raises:
            UnexpectedEmptyResult: Raised if the query did not return the created node
        """
        logging.info("Creating new node from model instance %s", self.__class__.__name__)
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
        logging.info("Created new node %s", self._element_id)

    @ensure_alive
    async def update(self) -> None:
        """
        Updates the corresponding node in the database with the current instance values.

        Raises:
            UnexpectedEmptyResult: Raised if the query did not return the updated node
        """
        deflated = self.deflate()

        logging.info(
            "Updating node %s of model %s with current properties %s",
            self._element_id,
            self.__class__.__name__,
            deflated,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH (n:{":".join(self.__labels__)})
                WHERE elementId(n) = $element_id
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in self._modified_properties])}
                RETURN n
            """,
            parameters={"element_id": self._element_id, **deflated},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0:
            raise UnexpectedEmptyResult()

        # Reset _modified_properties
        logging.debug("Resetting modified properties")
        self._modified_properties.clear()
        logging.info("Updated node %s", self._element_id)

    @ensure_alive
    async def delete(self) -> None:
        """
        Deletes the corresponding node in the database and marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised.
        """
        logging.info("Deleting node %s of model %s", self._element_id, self.__class__.__name__)
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
        logging.info("Deleted node %s", self._element_id)

    @classmethod
    async def find_one(cls: Type[T], expressions: dict[str, Any] | None = None) -> T | dict[str, Any] | None:
        """
        Finds the first node that matches `expressions` and returns it. If no matching node is found, `None`
        is returned instead.

        Args:
            expressions (dict[str, Any], optional): Expressions applied to the query. Defaults to {}.

        Returns:
            T | dict[str, Any] | None: A instance of the model or a dictionary if the model has not been registered or
                None if no match is found.
        """
        logging.info("Getting first node model %s matching expressions %s", cls.__name__, expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions if expressions is not None else {}
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:{":".join(cls.__labels__)})
                {f'WHERE {expression_query}' if expressions is not None else ''}
                RETURN n
                LIMIT 1
            """,
            parameters=expression_parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0:
            return None

        return results[0][0]

    @classmethod
    async def find_many(cls: Type[T], expressions: dict[str, Any] | None = None) -> list[T | dict[str, Any]]:
        """
        Finds the all nodes that matches `expressions` and returns them. If no matching nodes are found.

        Args:
            expressions (dict[str, Any], optional): Expressions applied to the query. Defaults to {}.

        Returns:
            list[T | dict[str, Any]]: A list of instances of the model or a list of dictionaries if the model
                has not been registered.
        """
        logging.info("Getting nodes of model %s matching expressions %s", cls.__name__, expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions if expressions is not None else {}
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:{":".join(cls.__labels__)})
                {f'WHERE {expression_query}' if expressions is not None else ''}
                RETURN n
            """,
            parameters=expression_parameters,
        )

        instances: list[T | dict[str, Any]] = []

        for result_list in results:
            for result in result_list:
                instances.append(result)

        return instances

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
