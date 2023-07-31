"""
This module holds the base node class `NodeModel` which is used to define database models for nodes.
It provides base functionality like de-/inflation and validation and methods for interacting with
the database for CRUD operations on nodes.
"""
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, List, Type, TypeVar, Union, cast

from neo4j.graph import Node
from pydantic import BaseModel

from neo4j_ogm.core.base import ModelBase, hooks
from neo4j_ogm.exceptions import (
    InflationFailure,
    InstanceDestroyed,
    InstanceNotHydrated,
    MissingFilters,
    NoResultsFound,
)
from neo4j_ogm.fields.settings import NodeModelSettings
from neo4j_ogm.queries.types import NodeFilters, QueryOptions

if TYPE_CHECKING:
    from neo4j_ogm.fields.relationship_property import RelationshipProperty
else:
    RelationshipProperty = object

T = TypeVar("T", bound="NodeModel")


def ensure_alive(func: Callable):
    """
    Decorator which ensures that a instance has not been destroyed and has been hydrated before
    running any queries.

    Raises:
        InstanceDestroyed: Raised if the method is called on a instance which has been destroyed.
        InstanceNotHydrated: Raised if the method is called on a instance which has been saved to
            the database.
    """

    async def decorator(self, *args, **kwargs):
        if getattr(self, "_destroyed", True):
            raise InstanceDestroyed()

        if getattr(self, "_element_id", None) is None:
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class NodeModel(ModelBase):
    """
    Base model for all node models. Every node model should inherit from this class to define a
    model.
    """

    __model_settings__: ClassVar[NodeModelSettings]
    _relationships_properties = set()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Build relationship properties
        for _, property_name in self.__dict__.items():
            if hasattr(property_name, "_build_property"):
                cast(RelationshipProperty, property_name)._build_property(self)

    def __init_subclass__(cls) -> None:
        if not hasattr(cls, "__model_settings__"):
            setattr(cls, "__model_settings__", NodeModelSettings())

        # Check if node labels is set, if not fall back to model name
        if not hasattr(cls.__model_settings__, "labels"):
            logging.warning("No labels have been defined for model %s, using model name as label", cls.__name__)
            cls.__model_settings__.labels = (cls.__name__.capitalize(),)
        elif hasattr(cls.__model_settings__, "labels") and isinstance(cls.__model_settings__.labels, str):
            logging.debug("str class %s provided as labels, converting to tuple", cls.__model_settings__.labels)
            setattr(cls.__model_settings__, "labels", tuple(cls.__model_settings__.labels))

        for property_name, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if property_name is of type None
            if value.type_ is not None and hasattr(value.type_, "_build_property"):
                cls._relationships_properties.add(property_name)
                cls.__model_settings__.exclude_from_export.add(property_name)

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
            Dict[str, Any]: The deflated model instance.
        """
        logging.debug("Deflating model to storable dictionary")
        deflated: Dict[str, Any] = json.loads(self.json(exclude=self._relationships_properties))

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
    def inflate(cls: Type[T], node: Node) -> T:
        """
        Inflates a node instance into a instance of the current model.

        Args:
            node (Node): Node to inflate.

        Raises:
            InflationFailure: Raised if inflating the node fails.

        Returns:
            T: A new instance of the current model with the properties from the node instance.
        """
        inflated: Dict[str, Any] = {}

        logging.debug("Inflating node %s to model instance", node.element_id)
        for node_property in node.items():
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
        setattr(instance, "_element_id", node.element_id)
        return instance

    async def create(self: T) -> T:
        """
        Creates a new node from the current instance. After the method is finished, a newly created
        instance is seen as `alive` and any methods can be called on it.

        Raises:
            NoResultsFound: Raised if the query did not return the created node.

        Returns:
            T: The current model instance.
        """
        logging.info("Creating new node from model instance %s", self.__class__.__name__)
        deflated_properties = self.deflate()

        results, _ = await self._client.cypher(
            query=f"""
                CREATE {self._query_builder.node_match(self.__model_settings__.labels)}
                SET {', '.join(f"n.{property_name} = ${property_name}" for property_name in deflated_properties.keys())}
                RETURN n
            """,
            parameters=deflated_properties,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.debug("Hydrating instance values")
        setattr(self, "_element_id", getattr(cast(T, results[0][0]), "_element_id"))

        logging.debug("Resetting modified properties")
        self._modified_properties.clear()
        logging.info("Created new node %s", self._element_id)

        return self

    @ensure_alive
    async def update(self) -> None:
        """
        Updates the corresponding node in the database with the current instance values.

        Raises:
            NoResultsFound: Raised if the query did not return the updated node.
        """
        deflated = self.deflate()

        logging.info(
            "Updating node %s of model %s with current properties %s",
            self._element_id,
            self.__class__.__name__,
            deflated,
        )
        set_query = ", ".join(
            [
                f"n.{property_name} = ${property_name}"
                for property_name in deflated
                if property_name in self._modified_properties
            ]
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.node_match(self.__model_settings__.labels)}
                WHERE elementId(n) = $element_id
                {f"SET {set_query}" if set_query != "" else ""}
                RETURN n
            """,
            parameters={"element_id": self._element_id, **deflated},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        # Reset _modified_properties
        logging.debug("Resetting modified properties")
        self._modified_properties.clear()
        logging.info("Updated node %s", self._element_id)

    @ensure_alive
    async def delete(self) -> None:
        """
        Deletes the corresponding node in the database and marks this instance as destroyed. If
        another method is called on this instance, an `InstanceDestroyed` will be raised.

        Raises:
            NoResultsFound: Raised if the query did not return the updated node.
        """
        logging.info("Deleting node %s of model %s", self._element_id, self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.node_match(self.__model_settings__.labels)}
                WHERE elementId(n) = $element_id
                DETACH DELETE n
                RETURN count(n)
            """,
            parameters={"element_id": self._element_id},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.debug("Marking instance as destroyed")
        setattr(self, "_destroyed", True)
        logging.info("Deleted node %s", self._element_id)

    @ensure_alive
    async def refresh(self) -> None:
        """
        Refreshes the current instance with the values from the database.

        Raises:
            NoResultsFound: Raised if the query did not return the current node.
        """
        logging.info("Refreshing node %s of model %s", self._element_id, self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {self._query_builder.node_match(self.__model_settings__.labels)}
                WHERE elementId(n) = $element_id
                RETURN n
            """,
            parameters={"element_id": self._element_id},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.debug("Updating current instance")
        self.__dict__.update(cast(T, results[0][0]).__dict__)
        logging.info("Refreshed node %s", self._element_id)

    @classmethod
    @hooks
    async def find_one(cls: Type[T], filters: NodeFilters) -> Union[T, None]:
        """
        Finds the first node that matches `filters` and returns it. If no matching node is found,
        `None` is returned instead.

        Args:
            filters (NodeFilters): The filters to apply to the query.

        Raises:
            MissingFilters: Raised if no filters or invalid filters are provided.

        Returns:
            T | None: A instance of the model or None if no match is found.
        """
        logging.info("Getting first encountered node of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.node_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                WHERE {cls._query_builder.query['where']}
                RETURN n
                LIMIT 1
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            return None

        logging.debug("Checking if node has to be parsed to instance")
        if isinstance(results[0][0], Node):
            return cls.inflate(node=results[0][0])

        return results[0][0]

    @classmethod
    async def find_many(
        cls: Type[T], filters: Union[NodeFilters, None] = None, options: Union[QueryOptions, None] = None
    ) -> List[T]:
        """
        Finds the all nodes that matches `filters` and returns them. If no matches are found, an
        empty list is returned instead.

        Args:
            filters (NodeFilters, optional): The filters to apply to the query. Defaults to None.
            options (QueryOptions, optional): The options to apply to the query. Defaults to None.

        Returns:
            List[T]: A list of model instances.
        """
        logging.info("Getting nodes of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.node_filters(filters=filters)
        if options is not None:
            cls._query_builder.query_options(options=options)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN n
                {cls._query_builder.query['options']}
            """,
            parameters=cls._query_builder.parameters,
        )

        instances: List[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(results[0][0], Node):
                    instances.append(cls.inflate(node=results[0][0]))
                else:
                    instances.append(result)

        return instances

    @classmethod
    async def update_one(cls: Type[T], update: Dict[str, Any], filters: NodeFilters, new: bool = False) -> T:
        """
        Finds the first node that matches `filters` and updates it with the values defined by
        `update`. If no match is found, a `NoResultsFound` is raised.

        Args:
            update (Dict[str, Any]): Values to update the node properties with.
            filters (NodeFilters): The filters to apply to the query.
            new (bool, optional): Whether to return the updated node. By default, the old node is
                returned. Defaults to False.

        Raises:
            NoResultsFound: Raised if the query did not return the node.
            MissingFilters: Raised if no filters or invalid filters are provided.

        Returns:
            T: By default, the old node instance is returned. If `new` is set to `True`, the result
                will be the `updated` instance.
        """
        new_instance: T

        logging.info("Updating first encountered node of model %s matching filters %s", cls.__name__, filters)
        logging.debug("Getting first encountered node of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.node_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                WHERE {cls._query_builder.query['where']}
                RETURN n
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
        new_instance = cls(**cast(T, old_instance).dict())

        for key, value in update.items():
            setattr(new_instance, key, value)
        setattr(new_instance, "_element_id", getattr(old_instance, "_element_id", None))

        await new_instance.update()
        logging.info("Successfully updated node %s", getattr(new_instance, "_element_id"))

        if new:
            return new_instance

        return old_instance

    @classmethod
    async def update_many(
        cls: Type[T], update: Dict[str, Any], filters: Union[NodeFilters, None] = None, new: bool = False
    ) -> [List[T], T]:
        """
        Finds all nodes that match `filters` and updates them with the values defined by `update`.

        Args:
            update (Dict[str, Any]): Values to update the node properties with.
            filters (NodeFilters, optional): The filters to apply to the query. Defaults to None.
            new (bool, optional): Whether to return the updated nodes. By default, the old nodes
                is returned. Defaults to False.

        Returns:
            List[T] | T: By default, the old node instances are returned. If `new` is set to `True`,
                the result will be the `updated/created instance`.
        """
        new_instance: T

        logging.info("Updating all nodes of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.node_filters(filters=filters)

        logging.debug("Getting all nodes of model %s matching filters %s", cls.__name__, filters)
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN n
            """,
            parameters=cls._query_builder.parameters,
        )

        old_instances: List[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(results[0][0], Node):
                    old_instances.append(cls.inflate(node=results[0][0]))
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
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
                RETURN n
            """,
            parameters={**deflated_properties, **cls._query_builder.parameters},
        )

        logging.info(
            "Successfully updated %s nodes %s",
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
    async def delete_one(cls: Type[T], filters: NodeFilters) -> int:
        """
        Finds the first node that matches `filters` and deletes it. If no match is found, a
        `NoResultsFound` is raised.

        Args:
            filters (NodeFilters): The filters to apply to the query.

        Raises:
            NoResultsFound: Raised if the query did not return the node.
            MissingFilters: Raised if no filters or invalid filters are provided.

        Returns:
            int: The number of deleted nodes.
        """
        logging.info("Deleting first encountered node of model %s matching filters %s", cls.__name__, filters)
        cls._query_builder.node_filters(filters=filters)

        if cls._query_builder.query["where"] == "":
            raise MissingFilters()

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                WHERE {cls._query_builder.query['where']}
                WITH n LIMIT 1
                DETACH DELETE n
                RETURN n
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.info("Deleted node %s", cast(Node, results[0][0]).element_id)
        return len(results)

    @classmethod
    async def delete_many(cls: Type[T], filters: Union[NodeFilters, None] = None) -> int:
        """
        Finds all nodes that match `filters` and deletes them.

        Args:
            filters (NodeFilters, optional): The filters to apply to the query. Defaults to None.

        Returns:
            int: The number of deleted nodes.
        """
        logging.info("Deleting all nodes of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.node_filters(filters=filters)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                DETACH DELETE n
                RETURN n
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.info("Deleted %s nodes", len(results))
        return len(results)

    @classmethod
    async def count(cls: Type[T], filters: Union[NodeFilters, None] = None) -> int:
        """
        Counts all nodes which match the provided `filters` parameter.

        Args:
            filters (NodeFilters, optional): The filters to apply to the query. Defaults to None.

        Returns:
            int: The number of nodes matched by the query.
        """
        logging.info("Getting count of nodes of model %s matching filters %s", cls.__name__, filters)
        if filters is not None:
            cls._query_builder.node_filters(filters=filters)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH {cls._query_builder.node_match(cls.__model_settings__.labels)}
                {f"WHERE {cls._query_builder.query['where']}" if cls._query_builder.query['where'] != "" else ""}
                RETURN count(n)
            """,
            parameters=cls._query_builder.parameters,
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        return results[0][0]
