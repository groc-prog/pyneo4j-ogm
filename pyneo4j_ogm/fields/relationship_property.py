"""
Relationship property class used to define relationships between the model this class is used on and a target model,
which defines the other end of the relationship.
"""

# pyright: reportUnboundVariable=false

import asyncio
from asyncio import iscoroutinefunction
from enum import Enum
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    ForwardRef,
    Generator,
    Generic,
    List,
    Optional,
    ParamSpec,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from neo4j.graph import Node, Relationship

from pyneo4j_ogm.exceptions import (
    CardinalityViolation,
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidTargetNode,
    NotConnectedToSourceNode,
    UnexpectedEmptyResult,
    UnregisteredModel,
)
from pyneo4j_ogm.fields.settings import NodeModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2, parse_model
from pyneo4j_ogm.queries.query_builder import QueryBuilder
from pyneo4j_ogm.queries.types import (
    Projection,
    QueryOptions,
    RelationshipFilters,
    RelationshipPropertyFilters,
)

if TYPE_CHECKING:
    from pyneo4j_ogm.core.client import Pyneo4jClient
    from pyneo4j_ogm.core.node import NodeModel
    from pyneo4j_ogm.core.relationship import RelationshipModel
else:
    Pyneo4jClient = object
    NodeModel = object
    RelationshipModel = object

if IS_PYDANTIC_V2:
    from pydantic import GetCoreSchemaHandler, ValidatorFunctionWrapHandler
    from pydantic_core import CoreSchema, core_schema
else:
    from pydantic.fields import ModelField  # type: ignore
    from pydantic.json import ENCODERS_BY_TYPE

P = ParamSpec("P")
T = TypeVar("T", bound=NodeModel)
U = TypeVar("U", bound=RelationshipModel)
V = TypeVar("V")


class RelationshipPropertyDirection(str, Enum):
    """
    Available relationship directions for relationship properties.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class RelationshipPropertyCardinality(str, Enum):
    """
    Available cardinality types.
    """

    ZERO_OR_ONE = "ZERO_OR_ONE"
    ZERO_OR_MORE = "ZERO_OR_MORE"


def hooks(func):
    """
    Decorator which runs defined pre- and post hooks for the decorated method. The decorator expects the
    hooks to have the name of the decorated method.

    Args:
        func (Callable): The method to decorate.

    Returns:
        Callable: The decorated method.
    """

    if iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(self: "RelationshipProperty", *args, **kwargs):
            source_node = getattr(self, "_source_node")
            settings: NodeModelSettings = getattr(source_node, "_settings")
            hook_name = f"{getattr(self, '_registered_name')}.{func.__name__}"

            # Run pre hooks if defined
            logger.debug("Checking pre hooks for %s", hook_name)
            if hook_name in settings.pre_hooks:
                for hook_function in settings.pre_hooks[hook_name]:
                    if iscoroutinefunction(hook_function):
                        await hook_function(source_node, *args, **kwargs)
                    else:
                        hook_function(source_node, *args, **kwargs)

            result = await func(self, *args, **kwargs)

            # Run post hooks if defined
            logger.debug("Checking post hooks for %s", hook_name)
            if hook_name in settings.post_hooks:
                for hook_function in settings.post_hooks[hook_name]:
                    if iscoroutinefunction(hook_function):
                        await hook_function(source_node, result, *args, **kwargs)
                    else:
                        hook_function(source_node, result, *args, **kwargs)

            return result

        return async_wrapper

    else:

        @wraps(func)
        def sync_wrapper(self: "RelationshipProperty", *args, **kwargs):
            source_node = getattr(self, "_source_node")
            settings: NodeModelSettings = getattr(source_node, "_settings")
            hook_name = f"{getattr(self, '_registered_name')}.{func.__name__}"
            loop = asyncio.get_event_loop()

            # Run pre hooks if defined
            logger.debug("Checking pre hooks for %s", hook_name)
            if hook_name in settings.pre_hooks:
                for hook_function in settings.pre_hooks[hook_name]:
                    if iscoroutinefunction(hook_function):
                        loop.run_until_complete(hook_function(source_node, *args, **kwargs))
                    else:
                        hook_function(source_node, *args, **kwargs)

            result = func(self, *args, **kwargs)

            # Run post hooks if defined
            logger.debug("Checking post hooks for %s", hook_name)
            if hook_name in settings.post_hooks:
                for hook_function in settings.post_hooks[hook_name]:
                    if iscoroutinefunction(hook_function):
                        loop.run_until_complete(hook_function(source_node, result, *args, **kwargs))
                    else:
                        hook_function(source_node, result, *args, **kwargs)

            return result

        return sync_wrapper


def check_models_registered(func):
    """
    Decorator which checks if the relationship- and target model have been registered with the client.

    Args:
        func (Callable): The method to decorate.

    Returns:
        Callable: The decorated method.
    """

    @wraps(func)
    async def decorator(self: "RelationshipProperty", *args, **kwargs):
        source_node = getattr(self, "_source_node")
        client: Optional[Pyneo4jClient] = getattr(self, "_client", None)
        target_model_name: str = getattr(self, "_target_model_name")
        relationship_model_name: str = getattr(self, "_relationship_model_name")

        logger.debug(
            "Checking if source model %s has been registered with client",
            source_node.__class__.__name__,
        )
        if client is None or source_node.__class__ not in client.models:
            raise UnregisteredModel(model=source_node.__class__.__name__)

        logger.debug(
            "Checking if target model %s has been registered with client",
            target_model_name,
        )
        if getattr(self, "_target_model", None) is None:
            raise UnregisteredModel(model=target_model_name)

        logger.debug(
            "Checking if relationship model %s has been registered with client",
            relationship_model_name,
        )
        if getattr(self, "_relationship_model", None) is None:
            raise UnregisteredModel(model=relationship_model_name)

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class RelationshipProperty(Generic[T, U]):
    """
    Class used to define relationships between the model this class is used on and a target model, which defines the
    other end of the relationship.

    Accepts two generic types, the first being the target node and the second being the relationship model. For type
    support when using a relationship-property, these generics have to be provided since they can not be inferred
    automatically.
    """

    _client: Pyneo4jClient
    _query_builder: QueryBuilder
    _target_model: Optional[Type[T]]
    _target_model_name: str
    _source_node: T
    _direction: RelationshipPropertyDirection
    _cardinality: RelationshipPropertyCardinality
    _relationship_model: Optional[Type[U]]
    _relationship_model_name: str
    _allow_multiple: bool
    _nodes: List[T]
    _registered_name: Optional[str]

    if IS_PYDANTIC_V2:

        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            origin = get_origin(source_type)

            if origin is None:
                origin = source_type
                target_model_type = Any
                relationship_model_type = Any
            else:
                target_model_type, relationship_model_type = get_args(source_type)

            target_model_schema = handler.generate_schema(target_model_type)
            relationship_model_schema = handler.generate_schema(relationship_model_type)

            target_model_name = (
                target_model_type.__forward_arg__
                if isinstance(target_model_type, ForwardRef)
                else target_model_type.__name__
            )
            relationship_model_name = (
                relationship_model_type.__forward_arg__
                if isinstance(relationship_model_type, ForwardRef)
                else relationship_model_type.__name__
            )

            def validate_target_model(
                v: RelationshipProperty[T, U], _: ValidatorFunctionWrapHandler
            ) -> RelationshipProperty[T, U]:
                if isinstance(v, cls) and target_model_name != v._target_model_name:
                    raise TypeError("Mismatch between generic types and target/relationship models")
                return v

            def validate_relationship_model(
                v: RelationshipProperty[T, U], _: ValidatorFunctionWrapHandler
            ) -> RelationshipProperty[T, U]:
                if isinstance(v, cls) and relationship_model_name != v._relationship_model_name:
                    raise TypeError("Mismatch between generic types and target/relationship models")
                return v

            python_schema = core_schema.chain_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.no_info_wrap_validator_function(validate_target_model, target_model_schema),
                    core_schema.no_info_wrap_validator_function(validate_relationship_model, relationship_model_schema),
                ],
            )

            return core_schema.json_or_python_schema(
                json_schema=core_schema.typed_dict_schema(
                    {
                        "target_model_name": core_schema.typed_dict_field(core_schema.str_schema()),
                        "relationship_model_name": core_schema.typed_dict_field(core_schema.str_schema()),
                        "direction": core_schema.typed_dict_field(core_schema.str_schema()),
                        "cardinality": core_schema.typed_dict_field(core_schema.str_schema(), required=False),
                        "allow_multiple": core_schema.typed_dict_field(core_schema.bool_schema(), required=False),
                    },
                ),
                python_schema=python_schema,
            )

    else:

        @classmethod
        def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
            field_schema.update(
                type="object",
                properties={
                    "target_model_name": {"type": "string", "title": "Target Model Name"},
                    "relationship_model_name": {"type": "string", "title": "Relationship Model Name"},
                    "direction": {"type": "string", "title": "Direction"},
                    "cardinality": {
                        "type": "string",
                        "default": "ZERO_OR_MORE",
                        "title": "Cardinality",
                    },
                    "allow_multiple": {"type": "boolean", "default": False, "title": "Allow Multiple"},
                },
                required=["target_model_name", "relationship_model_name", "direction"],
            )

        @classmethod
        def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]:
            yield cls.validate

        @classmethod
        def validate(cls, v: Any, field: ModelField) -> Any:
            if not isinstance(v, cls):
                raise TypeError("Must be instance of RelationshipProperty")

            # If generics are omitted, return the instance as-is since it
            # can not be validated
            if not field.sub_fields:
                return v

            target_model_type = field.sub_fields[0].type_
            relationship_model_type = field.sub_fields[1].type_

            if isinstance(v, cls):
                # If the types are forward refs, get the actual class name
                target_model_name = (
                    target_model_type.__forward_arg__
                    if isinstance(target_model_type, ForwardRef)
                    else target_model_type.__name__
                )
                relationship_model_name = (
                    relationship_model_type.__forward_arg__
                    if isinstance(relationship_model_type, ForwardRef)
                    else relationship_model_type.__name__
                )

                # Check whether the class names match the ones defined on the instance
                if any(
                    [
                        target_model_name != v._target_model_name,
                        relationship_model_name != v._relationship_model_name,
                    ]
                ):
                    raise TypeError("Mismatch between generic types and target/relationship models")

            return v

    def __init__(
        self,
        target_model: Union[Type[T], str],
        relationship_model: Union[Type[U], str],
        direction: RelationshipPropertyDirection,
        cardinality: RelationshipPropertyCardinality = RelationshipPropertyCardinality.ZERO_OR_MORE,
        allow_multiple: bool = False,
    ) -> None:
        """
        Class used to define relationships between the model this class is used on and a target model, which defines the
        other end of the relationship.

        Accepts two generic types, the first being the target node and the second being the relationship model. For type
        support when using a relationship-property, these generics have to be provided since they can not be inferred
        automatically.

        Args:
            target_model (Type[T] | str): The model which is the target of the relationship. Can be a
                model class or a string which matches the name of the model class.
            direction (RelationshipPropertyDirection): The relationship direction.
            relationship_model (Type[U] | str): The relationship model or the relationship type as a string.
            direction (RelationshipPropertyDirection): The direction of the relationship.
            cardinality (RelationshipPropertyCardinality, optional): The cardinality of the relationship. Defaults
                to `RelationshipPropertyCardinality.ZERO_OR_MORE`.
            allow_multiple (bool): Whether to use `MERGE` when creating new relationships. Defaults to `False`.
        """
        self._nodes = []
        self._registered_name = None
        self._target_model = None
        self._relationship_model = None
        self._allow_multiple = allow_multiple
        self._direction = direction
        self._cardinality = cardinality
        self._relationship_model_name = (
            relationship_model if isinstance(relationship_model, str) else relationship_model.__name__
        )
        self._target_model_name = target_model if isinstance(target_model, str) else target_model.__name__

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RelationshipProperty):
            return False

        return (
            self._target_model_name == other._target_model_name
            and self._relationship_model_name == other._relationship_model_name
            and self._direction == other._direction
            and self._cardinality == other._cardinality
            and self._allow_multiple == other._allow_multiple
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(target_model_name={self._target_model_name}, "
            f"relationship_model={self._relationship_model_name}, direction={self._direction.value}, "
            f"cardinality={self._cardinality.value}, allow_multiple={self._allow_multiple})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @hooks
    @check_models_registered
    async def relationships(
        self,
        node: T,
        filters: Optional[RelationshipFilters] = None,
        projections: Optional[Projection] = None,
        options: Optional[QueryOptions] = None,
    ) -> List[U]:
        """
        Gets the relationships between the current node instance and the provided node. If the nodes are not connected,
        `an empty list` will be returned.

        Args:
            node (T): The node to which to get the relationship.
            filters (RelationshipFilters | None, optional): Expressions applied to the query. Defaults to
                `None`.
            projections (Projection, optional): The properties to project from the node. The keys define
                the new keys in the projection and the value defines the model property to be projected. A invalid
                or empty projection will result in the whole model instance being returned. Defaults to `None`.
            options (QueryOptions, optional): The options to apply to the query. Defaults to `None`.

        Returns:
            (List[U]): Returns a list of `relationship model instances` describing relationships between
                the nodes or `an empty list` if no relationships exist between the two.
        """
        self._ensure_alive(node)
        self._query_builder.reset_query()

        logger.info("Getting relationship between target node %s and source node %s", node, self._source_node)
        if filters is not None:
            self._query_builder.relationship_filters(filters=filters)
        if options is not None:
            self._query_builder.query_options(options=options, ref="r")
        if projections is not None:
            self._query_builder.build_projections(projections=projections, ref="r")

        projection_query = (
            "RETURN r" if self._query_builder.query["projections"] == "" else self._query_builder.query["projections"]
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            start_node_labels=list(self._source_node._settings.labels),
            end_node_ref="end",
            end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                {f"AND {self._query_builder.query['where']}" if self._query_builder.query['where'] != "" else ""}
                {"WITH DISTINCT r" if self._query_builder.query['options'] != "" else ""}
                {self._query_builder.query['options']}
                {projection_query}
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
                **self._query_builder.parameters,
            },
        )

        relationships: List[U] = []

        for result_list in results:
            for result in result_list:
                if result is None:
                    continue

                if isinstance(result, cast(Type[U], self._relationship_model)):
                    relationships.append(result)
                elif isinstance(result, Relationship):
                    relationships.append(cast(Type[U], self._relationship_model)._inflate(graph_entity=result))
                elif projection_query != "":
                    relationships.extend(result)

        return relationships

    @hooks
    @check_models_registered
    async def connect(self, node: T, properties: Optional[Dict[str, Any]] = None) -> U:
        """
        Connects the given node to the source node. By default only one relationship will be created between nodes.
        If `allow_multiple` has been set to `True` and a relationship already exists between the nodes, a duplicate
        relationship will be created.

        Args:
            node (T): Node instance to create a relationship to.
            properties (Dict[str, Any] | None): Properties defined on the relationship model. Defaults to `None`.

        Raises:
            UnexpectedEmptyResult: If the query should return a result but does not.

        Returns:
            U: The created relationship.
        """
        self._ensure_alive(node)
        await self._ensure_cardinality()

        logger.info(
            "Creating relationship between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )

        # Build properties if relationship is defined as model
        relationship_instance = parse_model(
            cast(U, self._relationship_model), properties if properties is not None else {}
        )
        deflated_properties: Dict[str, Any] = relationship_instance._deflate()

        relationship_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            end_node_ref="end",
        )

        # Build MERGE/CREATE part of query depending on if duplicate relationships are allowed or not
        logger.debug("Building queries")
        if self._allow_multiple:
            build_query = f"CREATE {relationship_query}"
        else:
            build_query = f"MERGE {relationship_query}"

        set_query = (
            f"SET {', '.join([f'r.{property_name} = ${property_name}' for property_name in deflated_properties])}"
            if len(deflated_properties.keys()) != 0
            else ""
        )

        results, _ = await self._client.cypher(
            query=f"""
                MATCH
                    {self._query_builder.node_match(ref="start")},
                    {self._query_builder.node_match(ref="end")}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                {build_query}
                {set_query}
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
                **deflated_properties,
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise UnexpectedEmptyResult()
        return results[0][0]

    @hooks
    @check_models_registered
    async def disconnect(self, node: T, raise_on_empty: bool = False) -> int:
        """
        Disconnects the provided node from the source node. If the nodes are `not connected`, the query will not modify
        any of the nodes and `return 0`. If multiple relationships exists, all will be deleted.

        Args:
            node (T): The node to disconnect.
            raise_on_empty (bool, optional): Whether to raise an exception if no relationships were deleted. Defaults
                to `False`.

        Raises:
            NotConnectedToSourceNode: If the node is not connected to the source node.

        Returns:
            int: The number of disconnected nodes.
        """
        self._ensure_alive(node)

        logger.info(
            "Deleting relationships between target node %s and source node %s",
            getattr(node, "_element_id", None),
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            start_node_labels=list(cast(T, self._source_node)._settings.labels),
            end_node_ref="end",
            end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
        )

        logger.debug("Getting relationship count between source and target node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN count(r)
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
            },
            resolve_models=False,
        )

        if (
            len(count_results) == 0
            or len(count_results[0]) == 0
            or count_results[0][0] is None
            or count_results[0][0] == 0
        ):
            logger.debug(
                "No relationships found between source node %s and target node %s",
                getattr(self._source_node, "_element_id", None),
                getattr(node, "_element_id", None),
            )
            if raise_on_empty:
                raise NotConnectedToSourceNode()
            return 0

        logger.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(node, "_element_id", None),
            },
        )

        return count_results[0][0]

    @hooks
    @check_models_registered
    async def disconnect_all(self) -> int:
        """
        Disconnects all nodes.

        Returns:
            int: The number of disconnected nodes.
        """
        logger.info(
            "Deleting all relationships associated with source node %s",
            getattr(self._source_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            start_node_labels=list(cast(T, self._source_node)._settings.labels),
            end_node_ref="end",
            end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
        )

        logger.debug("Getting relationship count for source node")
        count_results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id
                RETURN count(r)
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
            },
            resolve_models=False,
        )

        if (
            len(count_results) == 0
            or len(count_results[0]) == 0
            or count_results[0][0] is None
            or count_results[0][0] == 0
        ):
            logger.debug(
                "No relationships found for source node %s",
                getattr(self._source_node, "_element_id", None),
            )
            return 0

        logger.debug("Found %s, deleting relationships", count_results[0][0])
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
            },
        )

        return count_results[0][0]

    @hooks
    @check_models_registered
    async def replace(self, old_node: T, new_node: T) -> List[U]:
        """
        Disconnects a old node and replaces it with a new node. All relationship properties will be carried over to
        the new relationship. If multiple relationships exists, all will be replaced.

        Args:
            old_node (T): The currently connected node.
            new_node (T): The node which replaces the currently connected node.

        Raises:
            NotConnectedToSourceNode: If the old node is not connected to the source node.

        Returns:
            List[U]: The new relationships between the source node and the newly connected node.
        """
        self._ensure_alive([old_node, new_node])

        logger.info(
            "Replacing old node %s with new node %s",
            getattr(old_node, "_element_id", None),
            getattr(new_node, "_element_id", None),
        )
        match_query = self._query_builder.relationship_match(
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            start_node_labels=list(cast(T, self._source_node)._settings.labels),
            end_node_ref="end",
            end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
        )

        logger.debug("Checking if new node is already connected and needs to be disconnected")
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(new_node, "_element_id", None),
            },
        )

        if len(results) != 0 and len(results[0]) != 0 and results[0][0] is not None and self._allow_multiple is False:
            logger.debug(
                "New node is already connected and 'allow_multiple' is set to 'False', deleting old relationship"
            )
            await self._client.cypher(
                query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                DELETE r
            """,
                parameters={
                    "start_element_id": getattr(self._source_node, "_element_id", None),
                    "end_element_id": getattr(new_node, "_element_id", None),
                },
            )

        logger.debug("Getting relationship between source node and old node")
        results, _ = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                RETURN r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(old_node, "_element_id", None),
            },
        )

        if len(results) == 0 or len(results[0]) == 0 or results[0][0] is None:
            raise NotConnectedToSourceNode()

        logger.debug("Deleting relationship between source node and old node")
        await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                DELETE r
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(old_node, "_element_id", None),
            },
        )

        logger.debug("Creating relationship between source node and new node")
        create_queries: List[str] = []
        set_queries: List[str] = []
        return_queries: List[str] = []
        query_parameters: Dict[str, Any] = {}

        for result in results:
            ref = f"r{cast(U, result[0]).id}"
            deflated_properties = cast(U, result[0])._deflate()

            return_queries.append(ref)
            create_queries.append(
                self._query_builder.relationship_match(
                    ref=ref,
                    direction=self._direction,
                    type_=cast(U, self._relationship_model)._settings.type,
                    start_node_ref="start",
                    end_node_ref="end",
                )
            )

            for property_name in deflated_properties:
                property_name_ref = f"_{ref}_{property_name}"

                query_parameters[property_name_ref] = deflated_properties[property_name]
                set_queries.append(f"{ref}.{property_name} = ${property_name_ref}")

                query_parameters[f"_{ref}_{property_name}"] = deflated_properties[property_name]

        results, _ = await self._client.cypher(
            query=f"""
                MATCH
                    {self._query_builder.node_match(labels=list(cast(T, self._source_node)._settings.labels), ref="start")},
                    {self._query_builder.node_match(labels=list(cast(Type[T], self._target_model)._settings.labels), ref="end")}
                WHERE elementId(start) = $start_element_id AND elementId(end) = $end_element_id
                CREATE {', '.join(create_queries)}
                {f"SET {', '.join(set_queries)}" if len(set_queries) != 0 else ""}
                RETURN {', '.join(return_queries)}
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                "end_element_id": getattr(new_node, "_element_id", None),
                **query_parameters,
            },
        )

        return cast(List[U], results[0])

    @hooks
    @check_models_registered
    async def find_connected_nodes(
        self,
        filters: Optional[RelationshipPropertyFilters] = None,
        projections: Optional[Projection] = None,
        options: Optional[QueryOptions] = None,
        auto_fetch_nodes: bool = False,
        auto_fetch_models: Optional[List[Union[str, Type["NodeModel"]]]] = None,
    ) -> List[Union[T, Dict[str, Any]]]:
        """
        Finds all nodes that matches `filters` and are connected to the source node.

        Args:
            filters (RelationshipPropertyFilters | None, optional): Expressions applied to the query. Defaults to
                `None`.
            projections (Projection, optional): The properties to project from the node. A invalid or empty
                projection will result in the whole model instances being returned. Defaults to `None`.
            options (QueryOptions | None, optional): Options for modifying the query result. Defaults to `None`.
            auto_fetch_nodes (bool, optional): Whether to automatically fetch connected nodes. Takes priority over the
                identical option defined in `Settings`. Defaults to `False`.
            auto_fetch_models (List[Union[str, T]], optional): A list of models to auto-fetch. `auto_fetch_nodes` has
                to be set to `True` for this to have any effect. Defaults to `[]`.

        Returns:
            List[T | Dict[str, Any]]: A list of model instances or dictionaries of the projected properties.
        """
        instances: List[Union[T, Dict[str, Any]]] = []
        do_auto_fetch: bool = False
        match_queries, return_queries = [], []

        logger.info("Getting connected nodes matching filters %s", filters)
        self._query_builder.reset_query()
        if filters is not None:
            self._query_builder.relationship_property_filters(filters=filters, ref="r", node_ref="end")
        if options is not None:
            self._query_builder.query_options(options=options, ref="end")
        if projections is not None:
            self._query_builder.build_projections(projections=projections, ref="end")

        projection_query = (
            "RETURN end" if self._query_builder.query["projections"] == "" else self._query_builder.query["projections"]
        )

        if auto_fetch_nodes:
            logger.debug("Auto-fetching nodes is enabled")

            match_queries, return_queries = cast(
                Type[T], self._target_model
            )._build_auto_fetch(  # pylint: disable=protected-access
                ref="end", nodes_to_fetch=auto_fetch_models
            )

            do_auto_fetch = all(
                [
                    auto_fetch_nodes,
                    projections is None,
                    len(match_queries) != 0,
                    len(return_queries) != 0,
                ]
            )

        match_query = self._query_builder.relationship_match(
            ref="r",
            direction=self._direction,
            type_=cast(U, self._relationship_model)._settings.type,
            start_node_ref="start",
            start_node_labels=list(cast(T, self._source_node)._settings.labels),
            end_node_ref="end",
            end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
        )

        results, meta = await self._client.cypher(
            query=f"""
                MATCH {match_query}
                WHERE
                    elementId(start) = $start_element_id
                    {f"AND {self._query_builder.query['where']}" if self._query_builder.query['where'] != "" else ""}
                WITH DISTINCT end
                {self._query_builder.query['options']}
                {" ".join(f"OPTIONAL MATCH {match_query}" for match_query in match_queries) if do_auto_fetch else ""}
                {projection_query}{f', {", ".join(return_queries)}' if do_auto_fetch else ''}
            """,
            parameters={
                "start_element_id": getattr(self._source_node, "_element_id", None),
                **self._query_builder.parameters,
            },
        )

        logger.debug("Building instances from results")
        if do_auto_fetch:
            # Add auto-fetched nodes to relationship properties
            added_nodes: Set[str] = set()

            logger.debug("Adding auto-fetched nodes to relationship properties")
            for result_list in results:
                for index, result in enumerate(result_list):
                    if result is None or result_list[0] is None:
                        continue

                    instance_element_id = getattr(result, "_element_id")
                    if instance_element_id in added_nodes:
                        continue

                    if index == 0:
                        instances.append(
                            cast(Type[T], self._target_model)._inflate(graph_entity=result)
                            if isinstance(result, Node)
                            else result
                        )
                    else:
                        target_instance = [
                            instance
                            for instance in instances
                            if getattr(result_list[0], "_element_id") == getattr(instance, "_element_id")
                        ][0]
                        relationship_property = getattr(target_instance, meta[index])
                        nodes = cast(List[str], getattr(relationship_property, "_nodes"))
                        nodes.append(result)

                    added_nodes.add(instance_element_id)
        else:
            for result_list in results:
                for result in result_list:
                    if result is None:
                        continue

                    if isinstance(result, Node):
                        instances.append(cast(Type[T], self._target_model)._inflate(graph_entity=result))
                    elif isinstance(result, list):
                        instances.extend(result)
                    else:
                        instances.append(cast(T, result))

        return instances

    def _build_property(self, source_model: T, property_name: str) -> None:
        """
        Sets the source node and returns self.

        Args:
            source_model (T): The source model instance.
            property_name (str): The name under which the relationship property is defined on the source model.

        Raises:
            UnregisteredModel: Raised if the source model has not been registered with the client.
        """
        if getattr(source_model, "_client", None) is None:
            raise UnregisteredModel(model=source_model.__class__.__name__)

        self._registered_name = property_name
        self._client = cast(Pyneo4jClient, getattr(source_model, "_client"))
        self._query_builder = QueryBuilder()
        self._source_node = source_model

        registered_node_model = [model for model in self._client.models if model.__name__ == self._target_model_name]
        if len(registered_node_model) > 0:
            self._target_model = cast(Type[T], registered_node_model[0])

        registered_relationship_model = [
            model for model in self._client.models if model.__name__ == self._relationship_model_name
        ]
        if len(registered_relationship_model) > 0:
            self._relationship_model = cast(Type[U], registered_relationship_model[0])

    def _ensure_alive(self, nodes: Union[T, List[T]]) -> None:
        """
        Ensures that the provided nodes are alive.

        Args:
            nodes (T | List[T]): Nodes to check for hydration and alive.

        Raises:
            InstanceNotHydrated: Raised if a node is not hydrated yet.
            InstanceDestroyed: Raised if a node has been marked as destroyed.
        """
        nodes_to_check = nodes if isinstance(nodes, list) else [nodes]
        target_model_labels = list(cast(Type[T], self._target_model)._settings.labels)

        for node in nodes_to_check:
            node_labels = list(node._settings.labels)
            logger.debug(
                "Checking if node %s is alive and of correct type",
                getattr(node, "_element_id", None),
            )
            if getattr(node, "_element_id", None) is None or getattr(node, "_id", None) is None:
                raise InstanceNotHydrated()

            if getattr(node, "_destroyed", True):
                raise InstanceDestroyed()

            if not all([label in node_labels for label in target_model_labels]):
                raise InvalidTargetNode(
                    expected_type=cast(Type[T], self._target_model).__name__,
                    actual_type=node.__class__.__name__,
                )

        if getattr(self._source_node, "_element_id", None) is None or getattr(self._source_node, "_id", None) is None:
            raise InstanceNotHydrated()

        if getattr(self._source_node, "_destroyed", True):
            raise InstanceDestroyed()

    async def _ensure_cardinality(self) -> None:
        """
        Checks for any cardinality violations before creating a new relationship.

        Args:
            node (T): The node to check the cardinality for.
        """
        logger.debug("Checking cardinality %s", self._cardinality)
        match self._cardinality:
            case RelationshipPropertyCardinality.ZERO_OR_ONE:
                match_query = self._query_builder.relationship_match(
                    direction=self._direction,
                    type_=cast(Type[U], self._relationship_model)._settings.type,
                    start_node_ref="start",
                    start_node_labels=list(cast(T, self._source_node)._settings.labels),
                    end_node_ref="end",
                    end_node_labels=list(cast(Type[T], self._target_model)._settings.labels),
                )

                results, _ = await self._client.cypher(
                    query=f"""
                        MATCH {match_query}
                        WHERE elementId(start) = $start_element_id
                        RETURN count(r)
                    """,
                    parameters={"start_element_id": getattr(self._source_node, "_element_id", None)},
                )

                if results[0][0] > 0:
                    raise CardinalityViolation(
                        cardinality_type=self._cardinality,
                        relationship_type=cast(str, cast(Type[U], self._relationship_model)._settings.type),
                        start_model=self._source_node.__class__.__name__,
                        end_model=cast(Type[T], self._target_model).__name__,
                    )
            case _:
                logger.debug("RelationshipPropertyCardinality is %s, no checks required", self._cardinality)

    @property
    def nodes(self) -> List[T]:
        """
        Auto-fetched nodes. Must set `auto_fetch_nodes` in settings or `find_one, find_many or
        find_connected_nodes` to `True` fot this to work.

        Returns:
            List[T]: The auto-fetched nodes.
        """
        return self._nodes


if not IS_PYDANTIC_V2:
    ENCODERS_BY_TYPE[RelationshipProperty] = str
