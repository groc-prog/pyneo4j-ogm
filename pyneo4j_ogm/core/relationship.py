"""
RelationshipModel module for the Neo4j OGM.

This module holds the base relationship class `RelationshipModel` which is used to define database models for
relationships. It provides base functionality like de-/inflation and validation and methods for interacting with
the database for CRUD operations on relationships.
"""
import json
import re
from functools import wraps
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union, cast

from neo4j.graph import Node, Relationship
from pydantic import BaseModel, Field

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import (
    InstanceDestroyed,
    InstanceNotHydrated,
    MissingFilters,
    NoResultsFound,
)
from pyneo4j_ogm.fields.settings import RelationshipModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.queries.types import (
    QueryOptions,
    RelationshipFilters,
    RelationshipMatchDirection,
)

T = TypeVar("T", bound="RelationshipModel")


def ensure_alive(func):
    """
    Decorator to ensure that the decorated method is only called on a alive instance.

    Args:
        func (Callable): The method to decorate.

    Raises:
        InstanceDestroyed: Raised if the instance is destroyed.
        InstanceNotHydrated: Raised if the instance is not hydrated.

    Returns:
        Callable: The decorated method.
    """

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any):
        if getattr(self, "_destroyed", False):
            raise InstanceDestroyed()

        if any(
            [
                getattr(self, "element_id", None) is None,
                getattr(self, "start_node_element_id", None) is None,
                getattr(self, "end_node_element_id", None) is None,
            ]
        ):
            raise InstanceNotHydrated()

        return func(self, *args, **kwargs)

    return wrapper


class RelationshipModel(ModelBase[RelationshipModelSettings]):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __settings__: RelationshipModelSettings
    start_node_element_id: Optional[str] = Field(default=None)
    end_node_element_id: Optional[str] = Field(default=None)
    Settings: ClassVar[Type[RelationshipModelSettings]]

    def __init_subclass__(cls) -> None:
        setattr(cls, "__settings__", RelationshipModelSettings())

        super().__init_subclass__()

        # Check if node labels is set, if not fall back to model name
        type_ = getattr(cls.__settings__, "type", None)

        # Check if relationship type is set, else fall back to class name
        if type_ is None:
            logger.warning("No type has been defined for model %s, using model name as type", cls.__name__)
            # Convert class name to upper snake case
            relationship_type = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__)
            setattr(cls.__settings__, "type", relationship_type.upper())

    def deflate(self) -> Dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            Dict[str, Any]: The deflated model instance
        """
        logger.debug("Deflating model %s to storable dictionary", self)
        deflated: Dict[str, Any] = json.loads(self.json(exclude={"__settings__"}))

        # Serialize nested BaseModel or dict instances to JSON strings
        for key, value in deflated.items():
            if isinstance(value, (dict, BaseModel)):
                deflated[key] = json.dumps(value)
            if isinstance(value, list):
                deflated[key] = [json.dumps(item) if isinstance(item, (dict, BaseModel)) else item for item in value]

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

        def try_property_parsing(property_value: str) -> Union[str, Dict[str, Any], BaseModel]:
            try:
                return json.loads(property_value)
            except:
                return property_value

        logger.debug("Inflating relationship %s to model instance", relationship)
        for node_property in relationship.items():
            property_name, property_value = node_property

            if isinstance(property_value, str):
                inflated[property_name] = try_property_parsing(property_value)
            elif isinstance(property_value, list):
                inflated[property_name] = [try_property_parsing(item) for item in property_value]
            else:
                inflated[property_name] = property_value

        instance = cls(**inflated)
        setattr(instance, "element_id", relationship.element_id)
        setattr(instance, "start_node_element_id", cast(Node, relationship.start_node).element_id)
        setattr(instance, "end_node_element_id", cast(Node, relationship.end_node).element_id)
        return instance

    @hooks
    @ensure_alive
    async def update(self) -> None:
        """
        Updates the corresponding relationship in the database with the current instance values.

        Raises:
            NoResultsFound: Raised if the query did not return the updated relationship.
        """
        deflated = self.deflate()

        logger.info(
            "Updating relationship %s of model %s with current properties %s",
            self.element_id,
            self.__class__.__name__,
            deflated,
        )
        set_query = ", ".join(
            [
                f"r.{property_name} = ${property_name}"
                for property_name in deflated
                if property_name in self.modified_properties
            ]
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__settings__.type)}
                WHERE elementId(r) = $element_id
                {f"SET {set_query}" if set_query != "" else ""}
                RETURN r
            """,
            parameters={
                "element_id": self.element_id,
                **deflated,
            },
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logger.debug("Resetting modified properties")
        self._db_properties = self.dict()
        logger.info("Updated relationship %s", self)

    @hooks
    @ensure_alive
    async def delete(self) -> None:
        """
        Deletes the corresponding relationship in the database and marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised.

        Raises:
            NoResultsFound: Raised if the query did not return the updated relationship.
        """
        logger.info("Deleting relationship %s", self)
        await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__settings__.type)}
                WHERE elementId(r) = $element_id
                DELETE r
            """,
            parameters={
                "element_id": self.element_id,
            },
        )

        logger.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
        logger.info("Deleted relationship %s", self.element_id)

    @hooks
    @ensure_alive
    async def refresh(self) -> None:
        """
        Refreshes the current instance with the values from the database.

        Raises:
            NoResultsFound: Raised if the query did not return the current relationship.
        """
        logger.info("Refreshing relationship %s with values from database", self)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__settings__.type)}
                WHERE elementId(r) = $element_id
                RETURN r
            """,
            parameters={"element_id": self.element_id},
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logger.debug("Updating current instance")
        self.__dict__.update(results[0][0].__dict__)
        logger.info("Refreshed relationship %s", self)

    @hooks
    @ensure_alive
    async def start_node(self) -> Type[NodeModel]:
        """
        Returns the start node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the start node.

        Returns:
            Type[NodeModel]: A instance of the start node model.
        """
        logger.info("Getting start node %s for relationship %s", self.start_node_element_id, self)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__settings__.type, start_node_ref="start")}
                WHERE elementId(r) = $element_id
                RETURN start
            """,
            parameters={
                "element_id": self.element_id,
            },
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    @hooks
    @ensure_alive
    async def end_node(self) -> Type[NodeModel]:
        """
        Returns the end node the relationship belongs to.

        Raises:
            NoResultsFound: Raised if the query did not return the end node.

        Returns:
            Type[NodeModel]: A instance of the end node model.
        """
        logger.info("Getting end node %s for relationship %s", self.end_node_element_id, self)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.relationship_match(type_=self.__settings__.type, start_node_ref="start", end_node_ref="end")}
                WHERE elementId(r) = $element_id
                RETURN end
            """,
            parameters={
                "element_id": self.element_id,
            },
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]

    @classmethod
    @hooks
    async def find_one(
        cls: Type[T], filters: RelationshipFilters, projections: Optional[Dict[str, str]] = None
    ) -> Optional[Union[T, Dict[str, Any]]]:
        """
        Finds the first relationship that matches `filters` and returns it. If no matching relationship is found,
        `None` is returned instead.

        Args:
            filters (RelationshipFilters): Expressions applied to the query.
            projections (Dict[str, str], optional): The properties to project from the relationship. The keys define
                the new keys in the projection and the value defines the model property to be projected. A invalid
                or empty projection will result in the whole model instance being returned. Defaults to None.

        Raises:
            MissingFilters: Raised if no filters are provided.

        Returns:
            T | Dict[str, Any] | None: A instance of the model or None if no match is found or a dictionary if a
                projection is provided.
        """
        logger.info(
            "Getting first encountered relationship of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        cls._query_builder.relationship_filters(filters=filters)

        if projections is not None:
            cls._query_builder.build_projections(projections=projections, ref="r")

        projection_query = (
            "DISTINCT r" if cls._query_builder.query["projections"] == "" else cls._query_builder.query["projections"]
        )

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                WITH r
                LIMIT 1
                RETURN {projection_query}
            """,
            parameters=cls._query_builder.parameters,
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None

        logger.debug("Checking if relationship has to be parsed to instance")
        if isinstance(results[0][0], Relationship):
            return cls.inflate(relationship=results[0][0])
        elif isinstance(results[0][0], list):
            return results[0][0][0]

        return results[0][0]

    @classmethod
    @hooks
    async def find_many(
        cls: Type[T],
        filters: Optional[RelationshipFilters] = None,
        projections: Optional[Dict[str, str]] = None,
        options: Optional[QueryOptions] = None,
    ) -> List[Union[T, Dict[str, Any]]]:
        """
        Finds the all relationships that matches `filters` and returns them.

        Args:
            filters (RelationshipFilters | None, optional): Expressions applied to the query. Defaults to
                None.
            projections (Dict[str, str], optional): The properties to project from the relationship. The keys define
                the new keys in the projection and the value defines the model property to be projected. A invalid
                or empty projection will result in the whole model instance being returned. Defaults to None.
            options (QueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T | Dict[str, Any]]: A list of model instances or dictionaries if a projection is provided.
        """
        logger.info(
            "Getting relationships of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)
        if options is not None:
            cls._query_builder.query_options(options=options, ref="r")
        if projections is not None:
            cls._query_builder.build_projections(projections=projections, ref="r")

        instances: List[Union[T, Dict[str, Any]]] = []
        projection_query = (
            "DISTINCT r" if cls._query_builder.query["projections"] == "" else cls._query_builder.query["projections"]
        )
        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                WITH r
                RETURN {projection_query}
                {cls._query_builder.query['options']}
            """,
            parameters=cls._query_builder.parameters,
        )

        logger.debug("Building instances from query results")
        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(result, Relationship):
                    instances.append(cls.inflate(relationship=result))
                elif isinstance(result, list):
                    instances.extend(result)
                else:
                    instances.append(result)

        return instances

    @classmethod
    @hooks
    async def update_one(
        cls: Type[T],
        update: Dict[str, Any],
        filters: RelationshipFilters,
        new: bool = False,
    ) -> Optional[T]:
        """
        Finds the first relationship that matches `filters` and updates it with the values defined by `update`. If
        no match is found, `None` is returned instead.

        Args:
            update (Dict[str, Any]): Values to update the relationship properties with.
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationship. By default, the old relationship is
                returned. Defaults to False.

        Raises:
            MissingFilters: Raised if no filters are provided.

        Returns:
            T | None: By default, the old relationship instance is returned. If `new` is set to `True`, the result
                will be the `updated instance`. If no match is found, `None` is returned.
        """
        new_instance: T

        logger.info(
            "Updating first encountered relationship of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        logger.debug(
            "Getting first encountered relationship of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        cls._query_builder.relationship_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE {cls._query_builder.query['where']}
                RETURN DISTINCT r
                LIMIT 1
            """,
            parameters=cls._query_builder.parameters,
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None
        old_instance = cast(T, results[0][0])

        # Update existing instance with values and save
        logger.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instance.dict())

        for key, value in update.items():
            if key in cls.__fields__:
                setattr(new_instance, key, value)

        setattr(new_instance, "element_id", getattr(old_instance, "element_id", None))
        setattr(new_instance, "start_node_element_id", getattr(old_instance, "start_node_element_id", None))
        setattr(new_instance, "end_node_element_id", getattr(old_instance, "end_node_element_id", None))

        deflated = new_instance.deflate()
        set_query = ", ".join(
            [
                f"r.{property_name} = ${property_name}"
                for property_name in deflated
                if property_name in new_instance.modified_properties
            ]
        )

        await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.relationship_match(type_=new_instance.__settings__.type)}
                WHERE elementId(r) = $element_id
                {f"SET {set_query}" if set_query != "" else ""}
            """,
            parameters={
                "element_id": new_instance.element_id,
                **deflated,
            },
        )

        logger.info("Successfully updated relationship %s", getattr(new_instance, "element_id"))
        return new_instance if new else old_instance

    @classmethod
    @hooks
    async def update_many(
        cls: Type[T],
        update: Dict[str, Any],
        filters: Optional[RelationshipFilters] = None,
        new: bool = False,
    ) -> List[T]:
        """
        Finds all relationships that match `filters` and updates them with the values defined by `update`.

        Args:
            update (Dict[str, Any]): Values to update the relationship properties with.
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated relationships. By default, the old relationships is
                returned. Defaults to False.

        Returns:
            List[T]: By default, the old relationship instances are returned. If `new` is set to `True`, the
                result will be the `updated instance`.
        """
        new_instance: T

        logger.info(
            "Updating all relationships of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        logger.debug(
            "Getting all relationships of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN DISTINCT r
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

        logger.debug("Checking if query returned a result")
        if len(old_instances) == 0:
            logger.debug("No results found")
            return []

        # Try and parse update values into random instance to check validation
        logger.debug("Creating instance copy with new values %s", update)
        new_instance = cls(**old_instances[0].dict())

        for key, value in update.items():
            if key in cls.__fields__:
                setattr(new_instance, key, value)

        deflated_properties = new_instance.deflate()

        # Update instances
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                SET {", ".join([f"r.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
                RETURN DISTINCT r
            """,
            parameters={**deflated_properties, **cls._query_builder.parameters},
        )

        logger.info(
            "Successfully updated %s relationships %s",
            len(old_instances),
            [getattr(instance, "element_id") for instance in old_instances],
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
    @hooks
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
        logger.info(
            "Deleting first encountered relationship of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        cls._query_builder.relationship_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
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

        logger.info("Deleted %s relationships", results[0][0])
        return results[0][0]

    @classmethod
    @hooks
    async def delete_many(cls: Type[T], filters: Optional[RelationshipFilters] = None) -> int:
        """
        Finds all relationships that match `filters` and deletes them.

        Args:
            filters (RelationshipFilters): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of deleted relationships.
        """
        logger.info(
            "Deleting all relationships of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        logger.debug("Getting relationship count matching filters %s", filters)
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
            resolve_models=False,
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logger.debug("Deleting relationships")
        await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                DELETE r
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
        )

        logger.info("Deleted %s relationships", results[0][0])
        return results[0][0]

    @classmethod
    @hooks
    async def count(cls: Type[T], filters: Optional[RelationshipFilters] = None) -> int:
        """
        Counts all relationships which match the provided `filters` parameter.

        Args:
            filters (RelationshipFilters | None, optional): Expressions applied to the query. Defaults
                to None.

        Returns:
            int: The number of relationships matched by the query.
        """
        logger.info(
            "Getting count of relationships of model %s matching filters %s",
            cls.__name__,
            filters,
        )
        cls._query_builder.reset_query()
        if filters is not None:
            cls._query_builder.relationship_filters(filters=filters)

        match_query = cls._query_builder.relationship_match(
            type_=cls.__settings__.type, direction=RelationshipMatchDirection.OUTGOING
        )

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {match_query}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN count(r)
            """,
            parameters=cls._query_builder.parameters,
        )

        logger.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]
