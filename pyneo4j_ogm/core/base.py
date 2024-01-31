"""
Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
model types like registering hooks and exporting/importing models to/from dictionaries.
"""

# pyright: reportUnboundVariable=false

import asyncio
import json
from asyncio import iscoroutinefunction
from copy import deepcopy
from functools import wraps
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    ParamSpec,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from neo4j.graph import Node, Relationship
from pydantic import BaseModel, PrivateAttr

from pyneo4j_ogm.exceptions import ListItemNotEncodable, UnregisteredModel
from pyneo4j_ogm.fields.relationship_property import (
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
)
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import (
    IS_PYDANTIC_V2,
    get_field_type,
    get_model_dump,
    get_model_fields,
    parse_model,
)
from pyneo4j_ogm.queries.query_builder import QueryBuilder

if TYPE_CHECKING:
    from pyneo4j_ogm.core.client import Pyneo4jClient
    from pyneo4j_ogm.core.node import NodeModel
    from pyneo4j_ogm.core.relationship import RelationshipModel
else:
    Pyneo4jClient = object
    NodeModel = object
    RelationshipModel = object

if IS_PYDANTIC_V2:
    from pydantic import SerializationInfo, model_serializer, model_validator
    from pydantic.errors import PydanticSchemaGenerationError
    from pydantic.json_schema import GenerateJsonSchema
else:
    from pydantic import root_validator

P = ParamSpec("P")
T = TypeVar("T", bound="ModelBase")
U = TypeVar("U")
V = TypeVar("V")

MappingIntStrAny = Mapping[int | str, Any]
DictStrAny = Dict[str, Any]
AbstractSetIntStr = AbstractSet[int | str]
IncEx = Optional[Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]]


def hooks(func):
    """
    Decorator which runs defined pre- and post hooks for the decorated method. The decorator expects the
    hooks to have the name of the decorated method. Both synchronous and asynchronous hooks are supported.

    Args:
        func (Callable): The method to decorate.

    Returns:
        Callable: The decorated method.
    """

    if iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            settings: BaseModelSettings = getattr(self, "_settings")

            if func.__name__ in settings.pre_hooks:
                logger.debug(
                    "Found %s pre-hook functions for method %s", len(settings.pre_hooks[func.__name__]), func.__name__
                )
                for hook_function in settings.pre_hooks[func.__name__]:
                    logger.debug("Running pre-hook function %s", hook_function.__name__)
                    if iscoroutinefunction(hook_function):
                        await hook_function(self, *args, **kwargs)
                    else:
                        hook_function(self, *args, **kwargs)

            result = await func(self, *args, **kwargs)

            if func.__name__ in settings.post_hooks:
                logger.debug(
                    "Found %s post-hook functions for method %s", len(settings.post_hooks[func.__name__]), func.__name__
                )
                for hook_function in settings.post_hooks[func.__name__]:
                    logger.debug("Running post-hook function %s", hook_function.__name__)
                    if iscoroutinefunction(hook_function):
                        await hook_function(self, result, *args, **kwargs)
                    else:
                        hook_function(self, result, *args, **kwargs)

            return result

        return async_wrapper

    else:

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            settings: BaseModelSettings = getattr(self, "_settings")

            if func.__name__ in settings.pre_hooks:
                logger.debug(
                    "Found %s pre-hook functions for method %s", len(settings.pre_hooks[func.__name__]), func.__name__
                )
                for hook_function in settings.pre_hooks[func.__name__]:
                    logger.debug("Running pre-hook function %s", hook_function.__name__)
                    if iscoroutinefunction(hook_function):
                        asyncio.create_task(hook_function(self, *args, **kwargs))
                    else:
                        hook_function(self, *args, **kwargs)

            result = func(self, *args, **kwargs)

            if func.__name__ in settings.post_hooks:
                logger.debug(
                    "Found %s post-hook functions for method %s", len(settings.post_hooks[func.__name__]), func.__name__
                )
                for hook_function in settings.post_hooks[func.__name__]:
                    logger.debug("Running post-hook function %s", hook_function.__name__)
                    if iscoroutinefunction(hook_function):
                        asyncio.create_task(hook_function(self, result, *args, **kwargs))
                    else:
                        hook_function(self, result, *args, **kwargs)

            return result

        return sync_wrapper


if IS_PYDANTIC_V2:

    class CustomGenerateJsonSchema(GenerateJsonSchema):
        """
        Custom JSON schema generator which adds support for generating JSON schemas for `RelationshipProperty` fields
        and adds index and uniqueness constraint information to the generated schema.
        """

        def generate(self, *args, **kwargs):
            model_cls: Optional[Type[BaseModel]] = None

            if "definitions" in args[0]:
                schema_ref = args[0]["schema"]["schema_ref"]

                for definition in args[0]["definitions"]:
                    if definition["ref"] == schema_ref and "cls" in definition:
                        model_cls = cast(Type[BaseModel], definition["cls"])
                        break
            elif "cls" in args[0]:
                model_cls = cast(Type[BaseModel], args[0]["cls"])

            if model_cls is None:
                raise PydanticSchemaGenerationError("Could not find model class in definitions")

            generated_schema = super().generate(*args, **kwargs)

            for field_name, field in get_model_fields(model_cls).items():
                point_index = getattr(get_field_type(field), "_point_index", False)
                range_index = getattr(get_field_type(field), "_range_index", False)
                text_index = getattr(get_field_type(field), "_text_index", False)
                unique = getattr(get_field_type(field), "_unique", False)

                if field_name not in generated_schema["properties"]:
                    continue

                if point_index:
                    generated_schema["properties"][field_name]["point_index"] = True
                if range_index:
                    generated_schema["properties"][field_name]["range_index"] = True
                if text_index:
                    generated_schema["properties"][field_name]["text_index"] = True
                if unique:
                    generated_schema["properties"][field_name]["uniqueness_constraint"] = True

            return generated_schema

        def encode_default(self, dft: Any) -> Any:
            if isinstance(dft, RelationshipProperty):
                dft = str(dft)
            return super().encode_default(dft)


class ModelBase(BaseModel, Generic[V]):
    """
    Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
    model types like registering hooks and exporting/importing models to/from dictionaries.

    Should not be used directly.
    """

    _settings: BaseModelSettings = PrivateAttr()
    _client: Pyneo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _db_properties: Dict[str, Any] = PrivateAttr(default={})
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: Optional[str] = PrivateAttr(default=None)
    _id: Optional[int] = PrivateAttr(default=None)
    Settings: ClassVar[Type[BaseModelSettings]]

    if IS_PYDANTIC_V2:

        @model_serializer(mode="wrap")
        def _model_serializer(self, serializer: Any, info: SerializationInfo) -> Any:
            if isinstance(self, RelationshipProperty):
                return self.nodes

            serialized = serializer(self)

            if not (self.id is None and info.exclude_none) and not (info.exclude is not None and "id" in info.exclude):
                serialized["id"] = self.id

            if not (self.element_id is None and info.exclude_none) and not (
                info.exclude is not None and "element_id" in info.exclude
            ):
                serialized["element_id"] = self.element_id

            if (
                hasattr(self, "_start_node_element_id")
                and not (cast(RelationshipModel, self).start_node_element_id is None and info.exclude_none)
                and not (info.exclude is not None and "start_node_element_id" in info.exclude)
            ):
                serialized["start_node_element_id"] = cast(RelationshipModel, self)._start_node_element_id

            if (
                hasattr(self, "_start_node_id")
                and not (cast(RelationshipModel, self).start_node_id is None and info.exclude_none)
                and not (info.exclude is not None and "start_node_id" in info.exclude)
            ):
                serialized["start_node_id"] = cast(RelationshipModel, self)._start_node_id

            if (
                hasattr(self, "_end_node_element_id")
                and not (cast(RelationshipModel, self).end_node_element_id is None and info.exclude_none)
                and not (info.exclude is not None and "end_node_element_id" in info.exclude)
            ):
                serialized["end_node_element_id"] = cast(RelationshipModel, self)._end_node_element_id

            if (
                hasattr(self, "_end_node_id")
                and not (cast(RelationshipModel, self).end_node_id is None and info.exclude_none)
                and not (info.exclude is not None and "end_node_id" in info.exclude)
            ):
                serialized["end_node_id"] = cast(RelationshipModel, self)._end_node_id

            if hasattr(self, "_relationship_properties"):
                for field_name in getattr(self, "_relationship_properties"):
                    if field_name in serialized:
                        serialized[field_name] = cast(RelationshipProperty, getattr(self, field_name)).nodes

            return serialized

        @model_validator(mode="before")  # type: ignore
        def _model_validator(cls, values: Any) -> Any:
            relationship_properties = getattr(cls, "_relationship_properties", set())

            for field_name, field in get_model_fields(cls).items():
                if (
                    field_name in relationship_properties
                    and field_name in values
                    and isinstance(values[field_name], list)
                ):
                    field_default = cast(RelationshipProperty, field.default)
                    instance_copy = RelationshipProperty(
                        target_model=getattr(field_default, "_target_model_name"),
                        relationship_model=getattr(field_default, "_relationship_model_name"),
                        direction=cast(RelationshipPropertyDirection, getattr(field_default, "_direction")),
                        cardinality=cast(RelationshipPropertyCardinality, getattr(field_default, "_cardinality")),
                        allow_multiple=cast(bool, getattr(field_default, "_allow_multiple")),
                    )

                    instance_copy._build_property(cls, field_name)
                    target_model = getattr(instance_copy, "_target_model", None)

                    if target_model is not None:
                        nodes: List[NodeModel] = []

                        for node in values[field_name]:
                            if isinstance(node, target_model):
                                nodes.append(node)
                                continue

                            instance = target_model(**node)
                            if "element_id" in node:
                                setattr(instance, "_element_id", node["element_id"])
                            if "id" in node:
                                setattr(instance, "_id", node["id"])

                            nodes.append(instance)

                        setattr(instance_copy, "_nodes", nodes)

                    values[field_name] = instance_copy

            return values

        @classmethod
        def model_json_schema(cls, *args, **kwargs) -> Dict[str, Any]:
            kwargs.setdefault("schema_generator", CustomGenerateJsonSchema)
            return super().model_json_schema(*args, **kwargs)

    else:

        @root_validator(pre=True)
        def _parse_dict_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            relationship_properties = getattr(cls, "_relationship_properties", set())

            for field_name, field in get_model_fields(cls).items():
                if (
                    field_name in relationship_properties
                    and field_name in values
                    and isinstance(values[field_name], list)
                ):
                    field_default = cast(RelationshipProperty, field.default)
                    instance_copy = RelationshipProperty(
                        target_model=getattr(field_default, "_target_model_name"),
                        relationship_model=getattr(field_default, "_relationship_model_name"),
                        direction=cast(RelationshipPropertyDirection, getattr(field_default, "_direction")),
                        cardinality=cast(RelationshipPropertyCardinality, getattr(field_default, "_cardinality")),
                        allow_multiple=cast(bool, getattr(field_default, "_allow_multiple")),
                    )

                    instance_copy._build_property(cls, field_name)
                    target_model = getattr(instance_copy, "_target_model", None)

                    if target_model is not None:
                        nodes: List[NodeModel] = []

                        for node in values[field_name]:
                            if isinstance(node, target_model):
                                nodes.append(node)
                                continue

                            instance = target_model(**node)
                            if "element_id" in node:
                                setattr(instance, "_element_id", node["element_id"])
                            if "id" in node:
                                setattr(instance, "_id", node["id"])

                            nodes.append(instance)

                        setattr(instance_copy, "_nodes", nodes)

                    values[field_name] = instance_copy

            return values

        def dict(  # type: ignore
            self,
            *,
            include: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
            exclude: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
            by_alias: bool = False,
            skip_defaults: Optional[bool] = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
        ) -> DictStrAny:
            excluded_fields = set()
            excluded_fields.update(exclude or set())

            if hasattr(self, "_relationship_properties"):
                excluded_fields.update(cast(Set[str], getattr(self, "_relationship_properties")))

            # pylint: disable=unexpected-keyword-arg
            base_dict = super().dict(
                include=include,
                exclude=excluded_fields,
                by_alias=by_alias,
                skip_defaults=skip_defaults,  # type: ignore
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )

            if not (self._id is None and exclude_none) and not (exclude is not None and "id" in exclude):
                base_dict["id"] = self._id

            if not (self._element_id is None and exclude_none) and not (
                exclude is not None and "element_id" in exclude
            ):
                base_dict["element_id"] = self._element_id
            if (
                hasattr(self, "_start_node_element_id")
                and not (cast(RelationshipModel, self).start_node_element_id is None and exclude_none)
                and not (exclude is not None and "start_node_element_id" in exclude)
            ):
                base_dict["start_node_element_id"] = cast(RelationshipModel, self)._start_node_element_id

            if (
                hasattr(self, "_start_node_id")
                and not (cast(RelationshipModel, self).start_node_id is None and exclude_none)
                and not (exclude is not None and "start_node_id" in exclude)
            ):
                base_dict["start_node_id"] = cast(RelationshipModel, self)._start_node_id

            if (
                hasattr(self, "_end_node_element_id")
                and not (cast(RelationshipModel, self).end_node_element_id is None and exclude_none)
                and not (exclude is not None and "end_node_element_id" in exclude)
            ):
                base_dict["end_node_element_id"] = cast(RelationshipModel, self)._end_node_element_id

            if (
                hasattr(self, "_end_node_id")
                and not (cast(RelationshipModel, self).end_node_id is None and exclude_none)
                and not (exclude is not None and "end_node_id" in exclude)
            ):
                base_dict["end_node_id"] = cast(RelationshipModel, self)._end_node_id

            if hasattr(self, "_relationship_properties"):
                for field_name in getattr(self, "_relationship_properties"):
                    field = cast(Union[RelationshipProperty, List], getattr(self, field_name))

                    if not isinstance(field, list) and not (exclude is not None and field_name in exclude):
                        base_dict[field_name] = [
                            cast(Union[RelationshipModel, NodeModel], node).dict() for node in field.nodes
                        ]

            return base_dict

        def json(  # type: ignore
            self,
            *,
            include: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
            exclude: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
            by_alias: bool = False,
            skip_defaults: Optional[bool] = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            encoder: Optional[Callable[[Any], Any]] = None,
            models_as_dict: bool = True,
            **dumps_kwargs: Any,
        ) -> str:
            excluded_fields = set()
            excluded_fields.update(exclude or set())

            if hasattr(self, "_relationship_properties"):
                excluded_fields.update(cast(Set[str], getattr(self, "_relationship_properties")))

            base_json = super().json(
                include=include,  # type: ignore
                exclude=excluded_fields,  # type: ignore
                by_alias=by_alias,
                skip_defaults=skip_defaults,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                encoder=encoder,
                models_as_dict=models_as_dict,
                **dumps_kwargs,
            )

            modified_json = json.loads(base_json)

            if not (self._id is None and exclude_none) and not (exclude is not None and "id" in exclude):
                modified_json["id"] = self._id

            if not (self._element_id is None and exclude_none) and not (
                exclude is not None and "element_id" in exclude
            ):
                modified_json["element_id"] = self._element_id
            if (
                hasattr(self, "_start_node_element_id")
                and not (cast(RelationshipModel, self).start_node_element_id is None and exclude_none)
                and not (exclude is not None and "start_node_element_id" in exclude)
            ):
                modified_json["start_node_element_id"] = cast(RelationshipModel, self)._start_node_element_id

            if (
                hasattr(self, "_start_node_id")
                and not (cast(RelationshipModel, self).start_node_id is None and exclude_none)
                and not (exclude is not None and "start_node_id" in exclude)
            ):
                modified_json["start_node_id"] = cast(RelationshipModel, self)._start_node_id

            if (
                hasattr(self, "_end_node_element_id")
                and not (cast(RelationshipModel, self).end_node_element_id is None and exclude_none)
                and not (exclude is not None and "end_node_element_id" in exclude)
            ):
                modified_json["end_node_element_id"] = cast(RelationshipModel, self)._end_node_element_id

            if (
                hasattr(self, "_end_node_id")
                and not (cast(RelationshipModel, self).end_node_id is None and exclude_none)
                and not (exclude is not None and "end_node_id" in exclude)
            ):
                modified_json["end_node_id"] = cast(RelationshipModel, self)._end_node_id

            if hasattr(self, "_relationship_properties"):
                for field_name in getattr(self, "_relationship_properties"):
                    field = cast(Union[RelationshipProperty, List], getattr(self, field_name))

                    if not isinstance(field, list) and not (exclude is not None and field_name in exclude):
                        modified_json[field_name] = [
                            json.loads(cast(Union[RelationshipModel, NodeModel], node).json()) for node in field.nodes
                        ]

            return json.dumps(modified_json)

    def __init__(self, *args, **kwargs) -> None:
        if not hasattr(self, "_client"):
            raise UnregisteredModel(model=self.__class__.__name__)

        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *args, **kwargs) -> None:
        setattr(cls, "_query_builder", QueryBuilder())

        logger.debug("Merging settings for model %s", cls.__name__)
        if hasattr(cls, "Settings") and hasattr(cls, "_settings") and issubclass(cls._settings.__class__, BaseModel):
            # Validate settings and merge them with the parent class settings
            parsed_settings = get_model_dump(
                parse_model(
                    cls._settings.__class__,
                    {key: value for key, value in cls.Settings.__dict__.items() if not key.startswith("__")},
                )
            )
            merged_settings = cls._merge_settings(parsed_settings)
            setattr(cls, "_settings", parse_model(cls._settings.__class__, merged_settings))

        if not IS_PYDANTIC_V2:
            for _, field in get_model_fields(cls).items():
                point_index = getattr(get_field_type(field), "_point_index", False)
                range_index = getattr(get_field_type(field), "_range_index", False)
                text_index = getattr(get_field_type(field), "_text_index", False)
                unique = getattr(get_field_type(field), "_unique", False)

                if point_index:
                    field.field_info.extra["point_index"] = True  # type: ignore
                if range_index:
                    field.field_info.extra["range_index"] = True  # type: ignore
                if text_index:
                    field.field_info.extra["text_index"] = True  # type: ignore
                if unique:
                    field.field_info.extra["uniqueness_constraint"] = True  # type: ignore

        super().__init_subclass__(*args, **kwargs)

    def __eq__(self, other: Any) -> bool:
        instance_type = type(self)
        if not isinstance(other, instance_type):
            return False

        return self._element_id == other._element_id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(element_id={self._element_id}, destroyed={self._destroyed})"

    def __str__(self) -> str:
        return self.__repr__()

    def __iter__(self):
        for attr_name, attr_value in super().__iter__():
            yield attr_name, attr_value

        yield "element_id", self._element_id
        yield "id", self._id

    @classmethod
    def register_pre_hooks(
        cls,
        hook_name: str,
        hook_functions: Union[List[Callable], Callable],
        overwrite: bool = False,
    ) -> None:
        """
        Register one or multiple pre-hooks for a method.

        Args:
            hook_name (str): Name of the hook to register the function for.
            hook_functions (Union[List[Callable], Callable]): References of the functions to call if the hook is
                triggered.
            overwrite (bool, optional): Whether to overwrite all defined hook functions if a new hooks function for
                the same hook is registered. Defaults to `False`.
        """
        valid_hook_functions: List[Callable] = []

        logger.info("Registering pre-hook for %s", hook_name)
        # Normalize hooks to a list of functions
        if isinstance(hook_functions, list):
            for hook_function in hook_functions:
                if callable(hook_function):
                    valid_hook_functions.append(hook_function)
        elif callable(hook_functions):
            valid_hook_functions.append(hook_functions)

        if hook_name not in cls._settings.pre_hooks:
            cls._settings.pre_hooks[hook_name] = []

        if overwrite:
            logger.debug("Overwriting %s existing pre-hook functions", len(cls._settings.pre_hooks[hook_name]))
            cls._settings.pre_hooks[hook_name] = valid_hook_functions
        else:
            logger.debug("Adding %s pre-hook functions", len(valid_hook_functions))
            for hook_function in valid_hook_functions:
                cls._settings.pre_hooks[hook_name].append(hook_function)

    @classmethod
    def register_post_hooks(
        cls,
        hook_name: str,
        hook_functions: Union[List[Callable], Callable],
        overwrite: bool = False,
    ) -> None:
        """
        Register one or multiple post-hooks for a method.

        Args:
            hook_name (str): Name of the hook to register the function for.
            hook_functions (Union[List[Callable], Callable]): References of the functions to call if the hook is
                triggered.
            overwrite (bool, optional): Whether to overwrite all defined hook functions if a new hooks function for
                the same hook is registered. Defaults to `False`.
        """
        valid_hook_functions: List[Callable] = []

        logger.info("Registering post-hook for %s", hook_name)
        # Normalize hooks to a list of functions
        if isinstance(hook_functions, list):
            for hook_function in hook_functions:
                if callable(hook_function):
                    valid_hook_functions.append(hook_function)
        elif callable(hook_functions):
            valid_hook_functions.append(hook_functions)

        if hook_name not in cls._settings.post_hooks:
            cls._settings.post_hooks[hook_name] = []

        if overwrite:
            logger.debug("Overwriting %s existing post-hook functions", len(cls._settings.post_hooks[hook_name]))
            cls._settings.post_hooks[hook_name] = valid_hook_functions
        else:
            logger.debug("Adding %s post-hook functions", len(valid_hook_functions))
            for hook_function in valid_hook_functions:
                cls._settings.post_hooks[hook_name].append(hook_function)

    @classmethod
    def model_settings(cls) -> V:
        """
        Returns the model settings.

        Returns:
            V: The model settings.
        """
        return cast(V, cls._settings)

    @classmethod
    def _merge_settings(
        cls, settings: Dict[str, Any], current_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recursively merges the provided settings with the current model settings. Inherited settings are merged
        if they are of type `set` or `list`, other values are overwritten.

        Args:
            settings (Dict[str, Any]): The settings to merge.
            current_settings (Optional[Dict[str, Any]], optional): The current settings. Defaults to `None`.

        Returns:
            Dict[str, Any]: The merged settings.
        """
        if current_settings is None:
            if hasattr(cls, "_settings") and issubclass(cls._settings.__class__, BaseModel):
                current_settings = get_model_dump(cls._settings)
            else:
                current_settings = {}

        for setting, value in settings.items():
            if setting not in current_settings:
                if isinstance(value, set):
                    current_settings[setting] = set()
                elif isinstance(value, list):
                    current_settings[setting] = []
                elif isinstance(value, dict):
                    current_settings[setting] = {}

            if isinstance(value, set):
                current_settings[setting] = cast(Set, current_settings[setting]).union(value)
            elif isinstance(value, list):
                cast(List, current_settings[setting]).extend(value)
            elif isinstance(value, dict):
                new_setting = cls._merge_settings(value, current_settings[setting])
                current_settings[setting] = new_setting
            elif value is not None:
                current_settings[setting] = value

        return current_settings

    def _deflate(self, deflated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Args:
            deflated (Dict[str, Any]): The model to deflate.

        Returns:
            Dict[str, Any]: The model model.
        """
        logger.debug("Deflating model %s to storable dictionary", self)

        # Serialize nested BaseModel or dict instances to JSON strings
        for field_name, field in deepcopy(deflated).items():
            if isinstance(field, (dict, BaseModel)):
                deflated[field_name] = json.dumps(field)
            elif isinstance(field, list):
                for index, item in enumerate(field):
                    if not isinstance(item, (int, float, str, bool)):
                        try:
                            deflated[field_name][index] = json.dumps(item)
                        except TypeError as exc:
                            raise ListItemNotEncodable from exc

        return deflated

    @classmethod
    def _inflate(cls: Type[T], graph_entity: Union[Node, Relationship]) -> Dict[str, Any]:
        """
        Inflates a graph entity into a instance of the current model.

        Args:
            graph_entity (Union[Node, Relationship]): Graph entity to inflate.

        Raises:
            InflationFailure: If inflating the node fails.

        Returns:
            Dict[str, Any]: The inflated model.
        """
        inflated: Dict[str, Any] = {}

        def try_property_parsing(property_value: str) -> Union[str, Dict[str, Any], BaseModel]:
            try:
                return json.loads(property_value)
            except:
                return property_value

        logger.debug("Inflating node %s to model instance", graph_entity)
        for node_property in graph_entity.items():
            property_name, property_value = node_property

            if isinstance(property_value, str):
                inflated[property_name] = try_property_parsing(property_value)
            elif isinstance(property_value, list):
                inflated[property_name] = [
                    try_property_parsing(item) if isinstance(item, str) else item for item in property_value
                ]
            else:
                inflated[property_name] = property_value

        return inflated

    @property
    def modified_properties(self) -> Set[str]:
        """
        Returns a set of properties which have been modified since the instance was hydrated.

        Returns:
            Set[str]: A set of properties which have been modified.
        """
        modified_properties = set()
        current_properties = get_model_dump(self)

        logger.debug("Collecting modified properties for model %s", self.__class__.__name__)
        for property_name, property_value in self._db_properties.items():
            if current_properties[property_name] != property_value:
                modified_properties.add(property_name)

        return modified_properties

    @property
    def element_id(self) -> Optional[str]:
        """
        Returns the element ID of the instance or `None` if the instance has not been hydrated.

        Returns:
            str | None: The element ID of the instance or `None` if the instance has not been hydrated.
        """
        return self._element_id

    @property
    def id(self) -> Optional[int]:
        """
        Returns the ID of the instance or `None` if the instance has not been hydrated.

        Returns:
            int: The ID of the instance or `None` if the instance has not been hydrated.
        """
        return self._id

    if IS_PYDANTIC_V2:
        model_config = {
            "validate_default": True,
            "validate_assignment": True,
            "revalidate_instances": "always",
        }
    else:

        class Config:
            """
            Pydantic configuration options.
            """

            validate_all = True
            validate_assignment = True
            revalidate_instances = "always"
            underscore_attrs_are_private = True
