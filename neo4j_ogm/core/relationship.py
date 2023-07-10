"""
This module holds the base relationship class `Neo4jRelationship` which is used to define database models for nodes.
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
                WHERE elementId(start) = $start_node AND elementId(end) = $end_node AND elementId(r) = $rel
                SET {", ".join([f"r.{property_name} = ${property_name}" for property_name in deflated])}
                RETURN n
            """,
            parameters={
                "start_node": self._start_node_id,
                "end_node": self._end_node_id,
                "rel": self._element_id,
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
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._build_relationship_match()}
                WHERE elementId(start) = $start_node AND elementId(end) = $end_node AND elementId(r) = $rel
                DELETE r
            """,
            parameters={
                "start_node": self._start_node_id,
                "end_node": self._end_node_id,
                "rel": self._element_id,
            },
        )

        logging.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
        logging.info("Deleted relationship %s", self._element_id)

    # @classmethod
    # async def find_one(cls: Type[T], expressions: TypedExpressions) -> T | None:
    #     """
    #     Finds the first relationship that matches `expressions` and returns it. If no matching relationship is found, `None`
    #     is returned instead.

    #     Args:
    #         expressions (TypedExpressions): Expressions applied to the query.

    #     Returns:
    #         T | None: A instance of the model or None if no match is found.
    #     """
    #     logging.info(
    #         "Getting first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
    #     )
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(expressions=expressions)

    #     if expression_query == "":
    #         raise InvalidExpressions(expressions=expressions)

    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             RETURN n
    #             LIMIT 1
    #         """,
    #         parameters=expression_parameters,
    #     )

    #     logging.debug("Checking if query returned a result")
    #     if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
    #         return None

    #     logging.debug("Checking if relationship has to be parsed to instance")
    #     if isinstance(results[0][0], Node):
    #         return cls.inflate(relationship=results[0][0])

    #     return results[0][0]

    # @classmethod
    # async def find_many(
    #     cls: Type[T], expressions: TypedExpressions | None = None, options: TypedQueryOptions | None = None
    # ) -> list[T]:
    #     """
    #     Finds the all nodes that matches `expressions` and returns them. If no matching nodes are found.

    #     Args:
    #         expressions (TypedExpressions | None, optional): Expressions applied to the query. Defaults to None.
    #         options (TypedQueryOptions | None, optional): Options for modifying the query result. Defaults to None.

    #     Returns:
    #         list[T]: A list of model instances.
    #     """
    #     logging.info("Getting nodes of model %s matching expressions %s", cls.__name__, expressions)
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(
    #         expressions=expressions if expressions is not None else {}
    #     )

    #     options_query = cls._query_builder.build_query_options(options=options if options else {})

    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             RETURN n
    #             {options_query}
    #         """,
    #         parameters=expression_parameters,
    #     )

    #     instances: list[T] = []

    #     for result_list in results:
    #         for result in result_list:
    #             if result is None:
    #                 continue

    #             if isinstance(results[0][0], Node):
    #                 instances.append(cls.inflate(relationship=results[0][0]))
    #             else:
    #                 instances.append(result)

    #     return instances

    # @classmethod
    # async def update_one(
    #     cls: Type[T], update: dict[str, Any], expressions: TypedExpressions, upsert: bool = False, new: bool = False
    # ) -> T | None:
    #     """
    #     Finds the first relationship that matches `expressions` and updates it with the values defined by `update`. If no match
    #     is found, a `NoResultsFound` is raised. Optionally, `upsert` can be set to `True` to create a new relationship if no
    #     match is found. When doing so, update must contain all properties required for model validation to succeed.

    #     Args:
    #         update (dict[str, Any]): Values to update the relationship properties with. If `upsert` is set to `True`, all
    #             required values defined on model must be present, else the model validation will fail.
    #         expressions (TypedExpressions): Expressions applied to the query. Defaults to None.
    #         upsert (bool, optional): Whether to create a new relationship if no relationship is found. Defaults to False.
    #         new (bool, optional): Whether to return the updated relationship. By default, the old relationship is returned. Defaults to
    #             False.

    #     Raises:
    #         NoResultsFound: Raised if the query did not return the relationship.

    #     Returns:
    #         T | None: By default, the old relationship instance is returned. If `upsert` is set to `True` and `not match is
    #             found`, `None` will be returned for the old relationship. If `new` is set to `True`, the result will be the
    #             `updated/created instance`.
    #     """
    #     is_upsert: bool = False
    #     new_instance: T

    #     logging.info(
    #         "Updating first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
    #     )
    #     old_instance = await cls.find_one(expressions=expressions)

    #     logging.debug("Checking if query returned a result")
    #     if old_instance is None:
    #         if upsert:
    #             # If upsert is True, try and parse new instance
    #             logging.debug("No results found, running upsert")
    #             new_instance = cls(**update)
    #             is_upsert = True
    #         else:
    #             raise NoResultsFound()
    #     else:
    #         # Update existing instance with values and save
    #         logging.debug("Creating instance copy with new values %s", update)
    #         new_instance = cls(**old_instance.dict())

    #         new_instance.__dict__.update(update)
    #         setattr(new_instance, "_element_id", getattr(old_instance, "_element_id", None))

    #     # Create query depending on whether upsert is active or not
    #     if upsert and is_upsert:
    #         await new_instance.create()
    #         logging.info("Successfully created relationship %s", getattr(new_instance, "_element_id"))
    #     else:
    #         await new_instance.update()
    #         logging.info("Successfully updated relationship %s", getattr(new_instance, "_element_id"))

    #     if new:
    #         return new_instance

    #     return old_instance

    # @classmethod
    # async def update_many(
    #     cls: Type[T],
    #     update: dict[str, Any],
    #     expressions: TypedExpressions | None = None,
    #     upsert: bool = False,
    #     new: bool = False,
    # ) -> list[T] | T | None:
    #     """
    #     Finds all nodes that match `expressions` and updates them with the values defined by `update`. Optionally,
    #     `upsert` can be set to `True` to create a new relationship if no matches are found. When doing so, update must contain
    #     all properties required for model validation to succeed.

    #     Args:
    #         update (dict[str, Any]): Values to update the relationship properties with. If `upsert` is set to `True`, all
    #             required values defined on model must be present, else the model validation will fail.
    #         expressions (TypedExpressions): Expressions applied to the query. Defaults to None.
    #         upsert (bool, optional): Whether to create a new relationship if no nodes are found. Defaults to False.
    #         new (bool, optional): Whether to return the updated nodes. By default, the old nodes is returned. Defaults
    #             to False.

    #     Returns:
    #         list[T] | T | None: By default, the old relationship instances are returned. If `upsert` is set to `True` and `not
    #             matches are found`, `None` will be returned for the old nodes. If `new` is set to `True`, the result
    #             will be the `updated/created instance`.
    #     """
    #     is_upsert: bool = False
    #     new_instance: T

    #     logging.info("Updating all nodes of model %s matching expressions %s", cls.__name__, expressions)
    #     old_instances = await cls.find_many(expressions=expressions)

    #     logging.debug("Checking if query returned a result")
    #     if len(old_instances) == 0:
    #         if upsert:
    #             # If upsert is True, try and parse new instance
    #             logging.debug("No results found, running upsert")
    #             new_instance = cls(**update)
    #             is_upsert = True
    #         else:
    #             logging.debug("No results found")
    #             return []
    #     else:
    #         # Try and parse update values into random instance to check validation
    #         logging.debug("Creating instance copy with new values %s", update)
    #         new_instance = cls(**old_instances[0].dict())
    #         new_instance.__dict__.update(update)

    #     deflated_properties = new_instance.deflate()
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(
    #         expressions=expressions if expressions is not None else {}
    #     )

    #     if is_upsert:
    #         results, _ = await cls._client.cypher(
    #             query=f"""
    #                 CREATE (n:{":".join(cls.__labels__)})
    #                 SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties])}
    #                 RETURN n
    #             """,
    #             parameters=deflated_properties,
    #         )

    #         logging.debug("Checking if query returned a result")
    #         if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
    #             raise NoResultsFound()

    #         logging.info("Successfully created relationship %s", getattr(results[0][0], "_element_id"))
    #         return results[0][0] if new else None

    #     # Update instances
    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
    #             RETURN n
    #         """,
    #         parameters={**deflated_properties, **expression_parameters},
    #     )

    #     if new:
    #         instances: list[T] = []

    #         for result_list in results:
    #             for result in result_list:
    #                 if result is not None:
    #                     instances.append(result)

    #         logging.info(
    #             "Successfully updated %s nodes %s",
    #             len(instances),
    #             [getattr(instance, "_element_id") for instance in instances],
    #         )
    #         return instances

    #     logging.info(
    #         "Successfully updated %s nodes %s",
    #         len(old_instances),
    #         [getattr(instance, "_element_id") for instance in old_instances],
    #     )
    #     return old_instances

    # @classmethod
    # async def delete_one(cls: Type[T], expressions: TypedExpressions) -> int:
    #     """
    #     Finds the first relationship that matches `expressions` and deletes it. If no match is found, a `NoResultsFound` is
    #     raised.

    #     Args:
    #         expressions (TypedExpressions): Expressions applied to the query. Defaults to None.

    #     Raises:
    #         NoResultsFound: Raised if the query did not return the relationship.

    #     Returns:
    #         int: The number of deleted nodes.
    #     """
    #     logging.info(
    #         "Deleting first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
    #     )
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(expressions=expressions)

    #     if expression_query == "":
    #         raise InvalidExpressions(expressions=expressions)

    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             DETACH DELETE n
    #             RETURN n
    #         """,
    #         parameters={**expression_parameters},
    #     )

    #     logging.debug("Checking if query returned a result")
    #     if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
    #         raise NoResultsFound()

    #     logging.info("Deleted relationship %s", cast(Node, results[0][0]).element_id)
    #     return len(results)

    # @classmethod
    # async def delete_many(cls: Type[T], expressions: dict[str, Any] | None = None) -> int:
    #     """
    #     Finds all nodes that match `expressions` and deletes them.

    #     Args:
    #         expressions (dict[str, Any]): Expressions applied to the query. Defaults to None.

    #     Returns:
    #         int: The number of deleted nodes.
    #     """
    #     logging.info(
    #         "Deleting first encountered relationship of model %s matching expressions %s", cls.__name__, expressions
    #     )
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(expressions=expressions)

    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             DETACH DELETE n
    #             RETURN n
    #         """,
    #         parameters={**expression_parameters},
    #     )

    #     logging.info("Deleted %s nodes", len(results))
    #     return len(results)

    # @classmethod
    # async def count(cls: Type[T], expressions: TypedExpressions | None = None) -> int:
    #     """
    #     Counts all nodes which match the provided `expressions` parameter.

    #     Args:
    #         expressions (TypedExpressions | None, optional): Expressions applied to the query. Defaults to None.

    #     Returns:
    #         int: The number of nodes matched by the query.
    #     """
    #     logging.info("Getting count of nodes of model %s matching expressions %s", cls.__name__, expressions)
    #     expression_query, expression_parameters = cls._query_builder.build_property_expression(
    #         expressions=expressions if expressions is not None else {}
    #     )

    #     results, _ = await cls._client.cypher(
    #         query=f"""
    #             MATCH (n:{":".join(cls.__labels__)})
    #             {expression_query}
    #             RETURN count(n)
    #         """,
    #         parameters=expression_parameters,
    #     )

    #     logging.debug("Checking if query returned a result")
    #     if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
    #         raise NoResultsFound()

    #     return results[0][0]

    def _build_relationship_match(self, rel_ref: str = "r", start_ref: str = "start", end_ref: str = "end") -> str:
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
        start_node = f"({start_ref}:{':'.join(self._start_node_model.__labels__)})"
        end_node = f"({end_ref}:{':'.join(self._end_node_model.__labels__)})"
        relationship = f"[{rel_ref}:{self.__type__}]"

        match self._direction:
            case Direction.BOTH:
                return f"{start_node}-{relationship}-{end_node}"
            case Direction.INCOMING:
                return f"{start_node}<-{relationship}-{end_node}"
            case Direction.BOTH:
                return f"{start_node}-{relationship}->{end_node}"
            case _:
                raise UnknownRelationshipDirection(
                    expected_directions=[option.value for option in Direction], actual_direction=self._direction
                )

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
