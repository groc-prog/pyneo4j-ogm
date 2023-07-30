"""
This module holds the base relationship class `RelationshipModel` which is used to define database models for relationships.
It provides base functionality like de-/inflation and validation and methods for interacting with
the database for CRUD operations on relationships.
"""
import json
import logging
import re
from typing import Any, Callable, ClassVar, Dict, List, Type, TypeVar, Union, cast

from neo4j.graph import Node, Relationship
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.core.base import ModelBase
from neo4j_ogm.core.node import NodeModel
from neo4j_ogm.exceptions import (
    InflationFailure,
    InstanceDestroyed,
    InstanceNotHydrated,
    MissingFilters,
    NoResultsFound,
)
from neo4j_ogm.fields.settings import RelationshipModelSettings
from neo4j_ogm.queries.types import QueryOptions, RelationshipFilters, RelationshipMatchDirection

T = TypeVar("T", bound="RelationshipModel")


def ensure_alive(func: Callable):
    """
    Decorator which ensures that a instance has not been destroyed and has been hydrated before running any queries.

    Raises:
        InstanceDestroyed: Raised if the method is called on a instance which has been destroyed
        InstanceNotHydrated: Raised if the method is called on a instance which has been saved to the database
    """

    async def decorator(self, *args, **kwargs):
        if getattr(self, "_destroyed", True):
            raise InstanceDestroyed()

        if any(
            attribute is None
            for attribute in [
                getattr(self, "_element_id", None),
                getattr(self, "_end_node_id", None),
                getattr(self, "_start_node_id", None),
            ]
        ):
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class RelationshipModel(ModelBase):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __model_settings__: ClassVar[RelationshipModelSettings]
    _start_node_id: Union[str, None] = PrivateAttr(default=None)
    _end_node_id: Union[str, None] = PrivateAttr(default=None)

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "__model_settings__"):
            setattr(cls, "__model_settings__", RelationshipModelSettings())

        # Check if relationship type is set, else fall back to class name
        if not hasattr(cls.__model_settings__, "type"):
            logging.warning("No type has been defined for model %s, using model name as type", cls.__name__)
            # Convert class name to upper snake case
            relationship_type = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__)
            setattr(cls.__model_settings__, "type", relationship_type.upper())

        return super().__init_subclass__()

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__fields__ and not name.startswith("_"):
            logging.debug("Adding %s to modified properties", name)
            self._modified_properties.add(name)

        return super().__setattr__(name, value)

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.__fields__ and not key.startswith("_"):
            logging.debug("Adding %s to modified properties", key)
            self._modified_properties.add(key)

        return super().__setattr__(key, value)

    def __str__(self) -> str:
        hydration_msg = self._element_id if self._element_id is not None else "not hydrated"
        return f"{self.__class__.__name__}({hydration_msg})"

    def deflate(self) -> Dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            Dict[str, Any]: The deflated model instance
        """
        logging.debug("Deflating model to storable dictionary")
        deflated: Dict[str, Any] = json.loads(self.json())

        # Serialize nested BaseModel or dict instances to JSON strings
        logging.debug("Serializing nested dictionaries to JSON strings")
        for property_name in self._dict_properties:
            deflated[property_name] = json.dumps(deflated[property_name])

        logging.debug("Serializing nested models to JSON strings")
        for property_name in self._model_properties:
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
        inflated: Dict[str, Any] = {}

        logging.debug("Inflating relationship %s to model instance", relationship.element_id)
        for node_property in relationship.items():
            property_name, property_value = node_property

            if property_name in cls._dict_properties or property_name in cls._model_properties:
                try:
                    logging.debug("Inflating property %s of model %s", property_name, cls.__name__)
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
                MATCH {self._query_builder.relationship_match(type_=self.__model_settings__.type)}
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
                MATCH {self._query_builder.relationship_match(type_=self.__model_settings__.type)}
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
    async def refresh(self) -> None:
        """
        Refreshes the current instance with the values from the database.

        Raises:
            NoResultsFound: Raised if the query did not return the current relationship.
        """
        logging.info("Refreshing relationship %s of model %s", self._element_id, self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__model_settings__.type)}
                WHERE elementId(r) = $element_id
                RETURN r
            """,
            parameters={"element_id": self._element_id},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.debug("Updating current instance")
        self.__dict__.update(cast(T, results[0][0]).__dict__)
        logging.info("Refreshed relationship %s", self._element_id)

    @ensure_alive
    async def start_node(self) -> Type[NodeModel]:
        """
        Returns the start node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the start node.

        Returns:
            Type[NodeModel]: A instance of the start node model.
        """
        logging.info(
            "Getting start node %s relationship %s of model %s",
            self._start_node_id,
            self._element_id,
            self.__class__.__name__,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__model_settings__.type, start_node_ref="start")}
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
    async def end_node(self) -> Type[NodeModel]:
        """
        Returns the end node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the end node.

        Returns:
            Type[NodeModel]: A instance of the end node model.
        """
        logging.info(
            "Getting end node %s relationship %s of model %s",
            self._end_node_id,
            self._element_id,
            self.__class__.__name__,
        )
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__model_settings__.type, start_node_ref="start")}
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
    async def find_one(cls: Type[T], filters: RelationshipFilters) -> Union[T, None]:
        """
        Finds the first relationship that matches `filters` and returns it. If no matching relationship is found,
        `None` is returned instead.

        Args:
            filters (RelationshipFilters): Expressions applied to the query.

        Raises:
            MissingFilters: Raised if no filters are provided.

        Returns:
            T | None: A instance of the model or None if no match is found.
        """
        logging.info("Getting first encountered relationship of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.relationship_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                RETURN r
                LIMIT 1
            """,
            parameters=cls._query_builder.parameters,
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
        cls: Type[T], filters: Union[RelationshipFilters, None] = None, options: Union[QueryOptions, None] = None
    ) -> List[T]:
        """
        Finds the all relationships that matches `filters` and returns them.

        Args:
            filters (RelationshipFilters | None, optional): Expressions applied to the query. Defaults to
                None.
            options (QueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T]: A list of model instances.
        """
        logging.info("Getting relationships of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)
        if options is not None:
            cls._query_builder.query_options(options=options, ref="r")

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN r
                {cls._query_builder.query['options']}
            """,
            parameters=cls._query_builder.parameters,
        )

        instances: List[T] = []

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
    async def update_one(cls: Type[T], update: Dict[str, Any], filters: RelationshipFilters, new: bool = False) -> T:
        """
        Finds the first relationship that matches `filters` and updates it with the values defined by `update`. If
        no match is found, a `NoResultsFound` is raised.

        Args:
            update (Dict[str, Any]): Values to update the relationship properties with.
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationship. By default, the old relationship is
                returned. Defaults to False.

        Raises:
            NoResultsFound: Raised if the query did not return the relationship.

        Returns:
            T: By default, the old relationship instance is returned. If `new` is set to `True`, the result
                will be the `updated instance`.
        """
        new_instance: T

        logging.info("Updating first encountered relationship of model %s matching filters %s", cls.__name__, filters)
        logging.debug("Getting first encountered relationship of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.relationship_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                RETURN r
                LIMIT 1
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()
        old_instance = results[0][0]

        # Update existing instance with values and save
        logging.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instance.dict())

        for key, value in update.items():
            setattr(new_instance, key, value)
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
        update: Dict[str, Any],
        filters: Union[RelationshipFilters, None] = None,
        new: bool = False,
    ) -> Union[List[T], T]:
        """
        Finds all relationships that match `filters` and updates them with the values defined by `update`.

        Args:
            update (Dict[str, Any]): Values to update the relationship properties with.
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationships. By default, the old relationships is
                returned. Defaults to False.

        Returns:
            List[T] | T: By default, the old relationship instances are returned. If `new` is set to `True`, the
                result will be the `updated instance`.
        """
        new_instance: T

        logging.info("Updating all relationships of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        logging.debug("Getting all relationships of model %s matching filters %s", cls.__name__, filters)
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN r
            """,
            parameters=cls._query_builder.parameters,
        )

        old_instances: List[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(results[0][0], Relationship):
                    old_instances.append(cls.inflate(relationship=results[0][0]))
                else:
                    old_instances.append(result)

        logging.debug("Checking if query returned a result")
        if len(old_instances) == 0:
            logging.debug("No results found")
            return []

        # Try and parse update values into random instance to check validation
        logging.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instances[0].dict())
        new_instance.__dict__.update(update)

        deflated_properties = new_instance.deflate()

        # Update instances
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                SET {", ".join([f"r.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
                RETURN r
            """,
            parameters={**deflated_properties, **cls._query_builder.parameters},
        )

        logging.info(
            "Successfully updated %s relationships %s",
            len(old_instances),
            [getattr(instance, "_element_id") for instance in old_instances],
        )
        if new:
            instances: List[T] = []

            for result_list in results:
                for result in result_list:
                    if result is not None:
                        instances.append(result)

            return instances
        return old_instances

    @classmethod
    async def delete_one(cls: Type[T], filters: RelationshipFilters) -> int:
        """
        Finds the first relationship that matches `filters` and deletes it. If no match is found, a
        `NoResultsFound` is raised.

        Args:
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.

        Raises:
            NoResultsFound: Raised if the query did not return the relationship.

        Returns:
            int: The number of deleted relationships.
        """
        logging.info("Deleting first encountered relationship of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.relationship_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                WITH r LIMIT 1
                DELETE r
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.info("Deleted %s relationships", results[0][0])
        return results[0][0]

    @classmethod
    async def delete_many(cls: Type[T], filters: Union[RelationshipFilters, None] = None) -> int:
        """
        Finds all relationships that match `filters` and deletes them.

        Args:
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of deleted relationships.
        """
        logging.info("Deleting all relationships of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        logging.debug("Getting relationship count matching filters %s", filters)
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
            resolve_models=False,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.debug("Deleting relationships")
        await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                DELETE r
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.info("Deleted %s relationships", results[0][0])
        return results[0][0]

    @classmethod
    async def count(cls: Type[T], filters: Union[RelationshipFilters, None] = None) -> int:
        """
        Counts all relationships which match the provided `filters` parameter.

        Args:
            filters (RelationshipFilters | None, optional): Expressions applied to the query. Defaults
                to None.

        Returns:
            int: The number of relationships matched by the query.
        """
        logging.info("Getting count of relationships of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__model_settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN DISTINCT count(r)
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
        arbitrary_types_allowed = True
