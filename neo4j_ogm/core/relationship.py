"""
This module holds the base relationship class `Neo4jRelationship` which is used to define database models for relationships.
"""
import json
import logging
from enum import Enum
from typing import Any, Type, TypeVar, cast

from neo4j.graph import Node, Relationship
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.core.node import Neo4jNode
from neo4j_ogm.exceptions import InflationFailure, InvalidExpressions, NoResultsFound, UnknownRelationshipDirection
from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.queries.types import TypedExpressions, TypedQueryOptions
from neo4j_ogm.utils import ensure_alive

T = TypeVar("T", bound="Neo4jRelationship")


class Direction(str, Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    BOTH = "BOTH"


class Neo4jRelationship(BaseModel):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __model_type__: str = "RELATIONSHIP"
    __type__: str
    __dict_properties = set()
    __model_properties = set()
    _client: Neo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _modified_properties: set[str] = PrivateAttr(default=set())
    _destroyed: bool = PrivateAttr(default=False)
    _direction: Direction = PrivateAttr()
    _element_id: str | None = PrivateAttr(default=None)
    _start_node_id: str | None = PrivateAttr(default=None)
    _end_node_id: str | None = PrivateAttr(default=None)
    _start_node_model: Type["Neo4jNode"] = PrivateAttr()
    _end_node_model: Type["Neo4jNode"] = PrivateAttr()

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models properties for serialization.
        """
        cls._client = Neo4jClient()
        cls._query_builder = QueryBuilder()

        # Check if relationship type is set, else fall back to class name
        if not hasattr(cls, "__type__"):
            logging.warning("No type has been defined for model %s, using model name as type", cls.__name__)
            cls.__type__ = cls.__name__

        logging.debug("Collecting dict and model fields")
        for property_name, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if property_name is of type None
            if value.type_ is not None:
                if isinstance(value.default, dict):
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
            if isinstance(getattr(self, property_name), BaseModel):
                deflated[property_name] = self.__dict__[property_name].json()
            else:
                deflated[property_name] = json.dumps(deflated[property_name])

        return deflated

    @classmethod
    def inflate(cls: Type[T], relationship: Relationship) -> T:
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

        logging.debug("Inflating relationship %s to model instance", relationship.element_id)
        for node_property in relationship.items():
            property_name, property_value = node_property

            if property_name in cls.__dict_properties or property_name in cls.__model_properties:
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    logging.error("Failed to inflate property %s of model %s", property_name, cls.__name__)
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        instance = cls(**inflated)
        setattr(instance, "_element_id", relationship.element_id)
        setattr(instance, "_start_node_id", cast(Node, relationship.start_node).element_id)
        setattr(instance, "_end_node_id", cast(Node, relationship.end_node).element_id)
        return instance

    @ensure_alive
    async def update(self) -> None:
        """
        Updates the corresponding relationship in the database with the current instance values.

        Raises:
            NoResultsFound: Raised if the query did not return the updated relationship.
        """
        deflated = self.deflate()

        logging.info(
            "Updating relationship %s of model %s with current properties %s",
            self._element_id,
            self.__class__.__name__,
            deflated,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._build_relationship_match()}
                WHERE elementId(r) = $element_id
                SET {", ".join([f"r.{property_name} = ${property_name}" for property_name in deflated])}
                RETURN r
            """,
            parameters={
                "element_id": self._element_id,
                **deflated,
            },
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        # Reset _modified_properties
        logging.debug("Resetting modified properties")
        self._modified_properties.clear()
        logging.info("Updated relationship %s", self._element_id)

    @ensure_alive
    async def delete(self) -> None:
        """
        Deletes the corresponding relationship in the database and marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised.

        Raises:
            NoResultsFound: Raised if the query did not return the updated relationship.
        """
        logging.info("Deleting relationship %s of model %s", self._element_id, self.__class__.__name__)
        await self._client.cypher(
            query=f"""
                MATCH {self._build_relationship_match()}
                WHERE elementId(r) = $element_id
                DELETE r
            """,
            parameters={
                "element_id": self._element_id,
            },
        )

        logging.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
        logging.info("Deleted relationship %s", self._element_id)

    @ensure_alive
    async def start_node(self) -> Type[Neo4jNode]:
        """
        Returns the start node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the start node.

        Returns:
            Type[Neo4jNode]: A instance of the start node model.
        """
        logging.info(
            "Getting start node %s relationship %s of model %s",
            self._start_node_id,
            self._element_id,
            self.__class__.__name__,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._build_relationship_match()}
                WHERE elementId(r) = $element_id
                RETURN start
            """,
            parameters={
                "element_id": self._element_id,
            },
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    @ensure_alive
    async def end_node(self) -> Type[Neo4jNode]:
        """
        Returns the end node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the end node.

        Returns:
            Type[Neo4jNode]: A instance of the end node model.
        """
        logging.info(
            "Getting end node %s relationship %s of model %s",
            self._end_node_id,
            self._element_id,
            self.__class__.__name__,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._build_relationship_match()}
                WHERE elementId(r) = $element_id
                RETURN end
            """,
            parameters={
                "element_id": self._element_id,
            },
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    @classmethod
    async def find_one(cls: Type[T], expressions: TypedExpressions) -> T | None:
        """
        Finds the first relationship that matches `expressions` and returns it. If no matching relationship is found,
        `None` is returned instead.

        Args:
            expressions (TypedExpressions): Expressions applied to the query.

        Returns:
            T | None: A instance of the model or None if no match is found.
        """
        logging.info(
            "Getting first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
        )
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions, ref="r"
        )

        if expression_query == "":
            raise InvalidExpressions(expressions=expressions)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                RETURN n
                LIMIT 1
            """,
            parameters=expression_parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None

        logging.debug("Checking if relationship has to be parsed to instance")
        if isinstance(results[0][0], Relationship):
            return cls.inflate(relationship=results[0][0])

        return results[0][0]

    @classmethod
    async def find_many(
        cls: Type[T], expressions: TypedExpressions | None = None, options: TypedQueryOptions | None = None
    ) -> list[T]:
        """
        Finds the all relationships that matches `expressions` and returns them. If no matching relationships are found.

        Args:
            expressions (TypedExpressions | None, optional): Expressions applied to the query. Defaults to None.
            options (TypedQueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            list[T]: A list of model instances.
        """
        logging.info("Getting relationships of model %s matching expressions %s", cls.__name__, expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions if expressions is not None else {}, ref="r"
        )

        options_query = cls._query_builder.build_query_options(options=options if options else {}, ref="r")

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                RETURN r
                {options_query}
            """,
            parameters=expression_parameters,
        )

        instances: list[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(results[0][0], Relationship):
                    instances.append(cls.inflate(relationship=results[0][0]))
                else:
                    instances.append(result)

        return instances

    @classmethod
    async def update_one(
        cls: Type[T], update: dict[str, Any], expressions: TypedExpressions, new: bool = False
    ) -> T | None:
        """
        Finds the first relationship that matches `expressions` and updates it with the values defined by `update`. If
        no match is found, a `NoResultsFound` is raised.

        Args:
            update (dict[str, Any]): Values to update the relationship properties with. If `upsert` is set to `True`,
                all required values defined on model must be present, else the model validation will fail.
            expressions (TypedExpressions): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationship. By default, the old relationship is
                returned. Defaults to False.

        Raises:
            NoResultsFound: Raised if the query did not return the relationship.

        Returns:
            T | None: By default, the old relationship instance is returned. If `new` is set to `True`, the result
                will be the `updated instance`.
        """
        new_instance: T

        logging.info(
            "Updating first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
        )
        old_instance = await cls.find_one(expressions=expressions)

        logging.debug("Checking if query returned a result")
        if old_instance is None:
            raise NoResultsFound()

        # Update existing instance with values and save
        logging.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instance.dict())

        new_instance.__dict__.update(update)
        setattr(new_instance, "_element_id", getattr(old_instance, "_element_id", None))

        # Create query depending on whether upsert is active or not
        await new_instance.update()
        logging.info("Successfully updated relationship %s", getattr(new_instance, "_element_id"))

        if new:
            return new_instance

        return old_instance

    @classmethod
    async def update_many(
        cls: Type[T],
        update: dict[str, Any],
        expressions: TypedExpressions | None = None,
        new: bool = False,
    ) -> list[T] | T | None:
        """
        Finds all relationships that match `expressions` and updates them with the values defined by `update`.

        Args:
            update (dict[str, Any]): Values to update the relationship properties with. If `upsert` is set to `True`,
                all required values defined on model must be present, else the model validation will fail.
            expressions (TypedExpressions): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationships. By default, the old relationships is
                returned. Defaults to False.

        Returns:
            list[T] | T | None: By default, the old relationship instances are returned. If `new` is set to `True`, the
                result will be the `updated instance`.
        """
        new_instance: T

        logging.info("Updating all relationships of model %s matching expressions %s", cls.__name__, expressions)
        old_instances = await cls.find_many(expressions=expressions)

        logging.debug("Checking if query returned a result")
        if len(old_instances) == 0:
            logging.debug("No results found")
            return []

        # Try and parse update values into random instance to check validation
        logging.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instances[0].dict())
        new_instance.__dict__.update(update)

        deflated_properties = new_instance.deflate()
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions if expressions is not None else {}, ref="r"
        )

        # Update instances
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
                RETURN n
            """,
            parameters={**deflated_properties, **expression_parameters},
        )

        if new:
            instances: list[T] = []

            for result_list in results:
                for result in result_list:
                    if result is not None:
                        instances.append(result)

            logging.info(
                "Successfully updated %s relationships %s",
                len(instances),
                [getattr(instance, "_element_id") for instance in instances],
            )
            return instances

        logging.info(
            "Successfully updated %s relationships %s",
            len(old_instances),
            [getattr(instance, "_element_id") for instance in old_instances],
        )
        return old_instances

    @classmethod
    async def delete_one(cls: Type[T], expressions: TypedExpressions) -> int:
        """
        Finds the first relationship that matches `expressions` and deletes it. If no match is found, a
        `NoResultsFound` is raised.

        Args:
            expressions (TypedExpressions): Expressions applied to the query. Defaults to None.

        Raises:
            NoResultsFound: Raised if the query did not return the relationship.

        Returns:
            int: The number of deleted relationships.
        """
        logging.info(
            "Deleting first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
        )
        relationship = await cls.find_one(expressions=expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions, ref="r"
        )

        if expression_query == "":
            raise InvalidExpressions(expressions=expressions)

        await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                DELETE r
            """,
            parameters={**expression_parameters},
        )

        logging.info("Deleted relationship %s", getattr(relationship, "_element_id"))
        return len(relationship)

    @classmethod
    async def delete_many(cls: Type[T], expressions: TypedExpressions | None = None) -> int:
        """
        Finds all relationships that match `expressions` and deletes them.

        Args:
            expressions (TypedExpressions): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of deleted relationships.
        """
        logging.info("Deleting all relationships of model %s matching expressions %s", cls.__name__, expressions)
        relationships = await cls.find_many(expressions=expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions, ref="r"
        )

        await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                DELETE r
            """,
            parameters={**expression_parameters},
        )

        logging.info("Deleted %s relationships", len(relationships))
        return len(relationships)

    @classmethod
    async def count(cls: Type[T], expressions: TypedExpressions | None = None) -> int:
        """
        Counts all relationships which match the provided `expressions` parameter.

        Args:
            expressions (TypedExpressions | None, optional): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of relationships matched by the query.
        """
        logging.info("Getting count of relationships of model %s matching expressions %s", cls.__name__, expressions)
        expression_query, expression_parameters = cls._query_builder.build_property_expression(
            expressions=expressions if expressions is not None else {}, ref="r"
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._build_relationship_match()}
                {expression_query}
                RETURN count(r)
            """,
            parameters=expression_parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    @classmethod
    def _build_relationship_match(cls, rel_ref: str = "r", start_ref: str = "start", end_ref: str = "end") -> str:
        """
        Builds a relationships `MATCH` clause based on the defined ref names and direction.

        Args:
            rel_ref (str, optional): Variable name to use for the relationship. Defaults to "r".
            start_ref (str, optional): Variable name to use for the start node. Defaults to "start".
            end_ref (str, optional): Variable name to use for the end node. Defaults to "end".

        Raises:
            UnknownRelationshipDirection: Raised if a invalid direction is provided.

        Returns:
            str: The generated `MATCH` clause.
        """
        start_node = f"({start_ref}:{':'.join(cls._start_node_model.__labels__)})"
        end_node = f"({end_ref}:{':'.join(cls._end_node_model.__labels__)})"
        relationship = f"[{rel_ref}:{cls.__type__}]"

        match cls._direction:
            case Direction.BOTH:
                return f"{start_node}-{relationship}-{end_node}"
            case Direction.INCOMING:
                return f"{start_node}<-{relationship}-{end_node}"
            case Direction.BOTH:
                return f"{start_node}-{relationship}->{end_node}"
            case _:
                raise UnknownRelationshipDirection(
                    expected_directions=[option.value for option in Direction], actual_direction=cls._direction
                )

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
