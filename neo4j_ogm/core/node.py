"""
This module holds the base node class `NodeModel` which is used to define database models for nodes.
"""
import json
import logging
from typing import Any, Callable, ClassVar, Dict, List, Set, Type, TypeVar, cast

from neo4j.graph import Node
from pydantic import BaseModel, PrivateAttr

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.exceptions import (
    InflationFailure,
    InstanceDestroyed,
    InstanceNotHydrated,
    NoResultsFound,
    UnregisteredModel,
)
from neo4j_ogm.fields.settings import NodeModelSettings
from neo4j_ogm.queries.query_builder import QueryBuilder
from neo4j_ogm.queries.types import TypedNodeExpression, TypedQueryOptions

T = TypeVar("T", bound="NodeModel")


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

        if getattr(self, "_element_id", None) is None:
            raise InstanceNotHydrated()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class NodeModel(BaseModel):
    """
    Base model for all node models. Every node model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __model_settings__: ClassVar[NodeModelSettings]
    __dict_properties = set()
    __model_properties = set()
    _client: Neo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _modified_properties: Set[str] = PrivateAttr(default=set())
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: str | None = PrivateAttr(default=None)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        for _, property_name in self.__dict__.items():
            if hasattr(property_name, "build_source"):
                property_name.build_source(self.__class__)

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models properties for serialization.
        """
        cls._client = Neo4jClient()
        cls._query_builder = QueryBuilder()

        if not hasattr(cls, "__model_settings__"):
            setattr(cls, "__model_settings__", NodeModelSettings())

        # Check if node labels is set, if not fall back to model name
        if not hasattr(cls.__model_settings__, "labels"):
            logging.warning("No labels have been defined for model %s, using model name as label", cls.__name__)
            cls.__model_settings__.labels = tuple(cls.__name__.capitalize())
        elif hasattr(cls.__model_settings__, "labels") and isinstance(cls.__model_settings__.labels, str):
            logging.debug("str class provided as labels, converting to tuple")
            setattr(cls.__model_settings__, "labels", tuple(cls.__model_settings__.labels))

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

    def deflate(self) -> Dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            Dict[str, Any]: The deflated model instance
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
        inflated: Dict[str, Any] = {}

        logging.debug("Inflating node %s to model instance", node.element_id)
        for node_property in node.items():
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
        setattr(instance, "_element_id", node.element_id)
        return instance

    async def create(self: T) -> T:
        """
        Creates a new node from the current instance. After the method is finished, a newly created
        instance is seen as `alive`.

        Raises:
            NoResultsFound: Raised if the query did not return the created node.

        Returns:
            T: The current model instance.
        """
        logging.info("Creating new node from model instance %s", self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                CREATE (n:{":".join(self.__model_settings__.labels)} $properties)
                RETURN n
            """,
            parameters={
                "properties": self.deflate(),
            },
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
        results, _ = await self._client.cypher(
            query=f"""
                MATCH (n:{":".join(self.__model_settings__.labels)})
                WHERE elementId(n) = $element_id
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated])}
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
        Deletes the corresponding node in the database and marks this instance as destroyed. If another
        method is called on this instance, an `InstanceDestroyed` will be raised.

        Raises:
            NoResultsFound: Raised if the query did not return the updated node.
        """
        logging.info("Deleting node %s of model %s", self._element_id, self.__class__.__name__)
        results, _ = await self._client.cypher(
            query=f"""
                MATCH (n:{":".join(self.__model_settings__.labels)})
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
                MATCH (n:{":".join(self.__model_settings__.labels)})
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

    @ensure_alive
    async def find_connected_nodes(
        self: T,
        target_model: Type[T] | str,
        min_hops: int = 1,
        max_hops: int = 1,
        expressions: TypedNodeExpression | None = None,
        options: TypedQueryOptions | None = None,
    ) -> List[T]:
        """
        Finds nodes connected to the current instance with the given expressions applied to the target node.

        Args:
            target_node (Type[T] | str): Model or model name of the target node.
            min_hops (int, optional): The lower hops limit when querying for nodes. Defaults to 1.
            max_hops (int, optional): The upper hops limit when querying for nodes. Defaults to 1.
            expressions (TypedNodeExpression | None, optional): Expressions applied to the target nodes. Defaults to None.
            options (TypedQueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T]: Nodes of the given model which are connected to the current instance.
        """
        target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

        logging.debug("Checking if target model %s has been registered with client", target_model_name)
        registered_target_model = [model for model in self._client.models if model.__name__ == target_model_name]
        if len(registered_target_model) == 0:
            raise UnregisteredModel(unregistered_model=target_model_name)

        logging.info(
            "Getting nodes of model %s connected to current instance %s with expressions %s",
            target_model_name,
            self._element_id,
            expressions,
        )
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = self._query_builder.build_node_expressions(expressions=expressions if expressions is not None else {})
        options_query = self._query_builder.build_query_options(options=options if options else {})

        results, _ = await self._client.cypher(
            query=f"""
                MATCH
                    (self:`{":".join(self.__model_settings__.labels)}`)-[rel*{min_hops}..{max_hops}]->(target:`{":".join(getattr(target_model.__model_settings__, "labels"))}`)
                    {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE
                    elementId(self) = $self_element_id
                    {expression_where_query if expression_where_query is not None else ""}
                RETURN target
                {options_query}
            """,
            parameters={"self_element_id": self._element_id, **expression_parameters},
        )

        instances: List[T] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                instances.append(result)

        return instances

    @classmethod
    async def find_one(cls: Type[T], expressions: TypedNodeExpression) -> T | None:
        """
        Finds the first node that matches `expressions` and returns it. If no matching node is found, `None`
        is returned instead.

        Args:
            expressions (TypedNodeExpression): Expressions applied to the query.

        Returns:
            T | None: A instance of the model or None if no match is found.
        """
        logging.info("Getting first encountered node of model %s matching expressions %s", cls.__name__, expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                RETURN n
                LIMIT 1
            """,
            parameters=expression_parameters,
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
        cls: Type[T], expressions: TypedNodeExpression | None = None, options: TypedQueryOptions | None = None
    ) -> List[T]:
        """
        Finds the all nodes that matches `expressions` and returns them.

        Args:
            expressions (TypedNodeExpression | None, optional): Expressions applied to the query. Defaults to None.
            options (TypedQueryOptions | None, optional): Options for modifying the query result. Defaults to None.

        Returns:
            List[T]: A list of model instances.
        """
        logging.info("Getting nodes of model %s matching expressions %s", cls.__name__, expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions if expressions is not None else {})
        options_query = cls._query_builder.build_query_options(options=options if options else {})

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                RETURN n
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
                    instances.append(cls.inflate(node=results[0][0]))
                else:
                    instances.append(result)

        return instances

    @classmethod
    async def update_one(
        cls: Type[T], update: Dict[str, Any], expressions: TypedNodeExpression, new: bool = False
    ) -> T:
        """
        Finds the first node that matches `expressions` and updates it with the values defined by `update`. If no match
        is found, a `NoResultsFound` is raised.

        Args:
            update (Dict[str, Any]): Values to update the node properties with. If `upsert` is set to `True`, all
                required values defined on model must be present, else the model validation will fail.
            expressions (TypedNodeExpression): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated node. By default, the old node is returned. Defaults to
                False.

        Raises:
            NoResultsFound: Raised if the query did not return the node.

        Returns:
            T: By default, the old node instance is returned. If `new` is set to `True`, the result will be the
                `updated/created instance`.
        """
        new_instance: T

        logging.info("Updating first encountered node of model %s matching expressions %s", cls.__name__, expressions)
        old_instance = await cls.find_one(expressions=expressions)

        logging.debug("Checking if query returned a result")
        if old_instance is None:
            raise NoResultsFound()
        else:
            # Update existing instance with values and save
            logging.debug("Creating instance copy with new values %s", update)
            new_instance = cls(**old_instance.dict())

            new_instance.__dict__.update(update)
            setattr(new_instance, "_element_id", getattr(old_instance, "_element_id", None))

        await new_instance.update()
        logging.info("Successfully updated node %s", getattr(new_instance, "_element_id"))

        if new:
            return new_instance

        return old_instance

    @classmethod
    async def update_many(
        cls: Type[T], update: Dict[str, Any], expressions: TypedNodeExpression | None = None, new: bool = False
    ) -> list[T] | T | None:
        """
        Finds all nodes that match `expressions` and updates them with the values defined by `update`.

        Args:
            update (Dict[str, Any]): Values to update the node properties with. If `upsert` is set to `True`, all
                required values defined on model must be present, else the model validation will fail.
            expressions (TypedNodeExpression): Expressions applied to the query. Defaults to None.
            new (bool, optional): Whether to return the updated nodes. By default, the old nodes is returned. Defaults
                to False.

        Returns:
            list[T] | T: By default, the old node instances are returned. If `new` is set to `True`, the result
                will be the `updated/created instance`.
        """
        new_instance: T

        logging.info("Updating all nodes of model %s matching expressions %s", cls.__name__, expressions)
        old_instances = await cls.find_many(expressions=expressions)

        logging.debug("Checking if query returned a result")
        if len(old_instances) == 0:
            logging.debug("No results found")
            return []
        else:
            # Try and parse update values into random instance to check validation
            logging.debug("Creating instance copy with new values %s", update)
            new_instance = cls(**old_instances[0].dict())
            new_instance.__dict__.update(update)

        deflated_properties = new_instance.deflate()
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions)

        # Update instances
        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                SET {", ".join([f"n.{property_name} = ${property_name}" for property_name in deflated_properties if property_name in update])}
                RETURN n
            """,
            parameters={**deflated_properties, **expression_parameters},
        )

        if new:
            instances: List[T] = []

            for result_list in results:
                for result in result_list:
                    if result is not None:
                        instances.append(result)

            logging.info(
                "Successfully updated %s nodes %s",
                len(instances),
                [getattr(instance, "_element_id") for instance in instances],
            )
            return instances

        logging.info(
            "Successfully updated %s nodes %s",
            len(old_instances),
            [getattr(instance, "_element_id") for instance in old_instances],
        )
        return old_instances

    @classmethod
    async def delete_one(cls: Type[T], expressions: TypedNodeExpression) -> int:
        """
        Finds the first node that matches `expressions` and deletes it. If no match is found, a `NoResultsFound` is
        raised.

        Args:
            expressions (TypedNodeExpression): Expressions applied to the query. Defaults to None.

        Raises:
            NoResultsFound: Raised if the query did not return the node.

        Returns:
            int: The number of deleted nodes.
        """
        logging.info("Deleting first encountered node of model %s matching expressions %s", cls.__name__, expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions)

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                DETACH DELETE n
                RETURN n
            """,
            parameters={**expression_parameters},
        )

        logging.debug("Checking if query returned a result")
        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NoResultsFound()

        logging.info("Deleted node %s", cast(Node, results[0][0]).element_id)
        return len(results)

    @classmethod
    async def delete_many(cls: Type[T], expressions: TypedNodeExpression | None = None) -> int:
        """
        Finds all nodes that match `expressions` and deletes them.

        Args:
            expressions (TypedNodeExpression): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of deleted nodes.
        """
        logging.info("Deleting all nodes of model %s matching expressions %s", cls.__name__, expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions if expressions is not None else {})

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                DETACH DELETE n
                RETURN n
            """,
            parameters={**expression_parameters},
        )

        logging.info("Deleted %s nodes", len(results))
        return len(results)

    @classmethod
    async def count(cls: Type[T], expressions: TypedNodeExpression | None = None) -> int:
        """
        Counts all nodes which match the provided `expressions` parameter.

        Args:
            expressions (TypedNodeExpression | None, optional): Expressions applied to the query. Defaults to None.

        Returns:
            int: The number of nodes matched by the query.
        """
        logging.info("Getting count of nodes of model %s matching expressions %s", cls.__name__, expressions)
        (
            expression_match_query,
            expression_where_query,
            expression_parameters,
        ) = cls._query_builder.build_node_expressions(expressions=expressions if expressions is not None else {})

        results, _ = await cls._client.cypher(
            query=f"""
                MATCH (n:`{":".join(cls.__model_settings__.labels)}`) {f', {expression_match_query}' if expression_match_query is not None else ""}
                WHERE {expression_where_query if expression_where_query is not None else ""}
                RETURN count(n)
            """,
            parameters=expression_parameters,
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
