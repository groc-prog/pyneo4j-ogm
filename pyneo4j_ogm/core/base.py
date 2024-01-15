"""
Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
model types like registering hooks and exporting/importing models to/from dictionaries.
"""

# pyright: reportUnboundVariable=false

import asyncio
import json
from asyncio import iscoroutinefunction
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

from pydantic import BaseModel, PrivateAttr

from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2, get_model_dump
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
    from pydantic.json_schema import GenerateJsonSchema
else:
    from pydantic.class_validators import root_validator

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
        async def wrapper(self, *args, **kwargs):  # type: ignore
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

            if iscoroutinefunction(func):
                result = await func(self, *args, **kwargs)
            else:
                result = func(self, *args, **kwargs)

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

    else:

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            settings: BaseModelSettings = getattr(self, "_settings")
            loop = asyncio.get_event_loop()

            if func.__name__ in settings.pre_hooks:
                logger.debug(
                    "Found %s pre-hook functions for method %s", len(settings.pre_hooks[func.__name__]), func.__name__
                )
                for hook_function in settings.pre_hooks[func.__name__]:
                    logger.debug("Running pre-hook function %s", hook_function.__name__)
                    if iscoroutinefunction(hook_function):
                        loop.run_until_complete(hook_function(self, *args, **kwargs))
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
                        loop.run_until_complete(hook_function(self, result, *args, **kwargs))
                    else:
                        hook_function(self, result, *args, **kwargs)

            return result

    return wrapper


if IS_PYDANTIC_V2:

    class CustomGenerateJsonSchema(GenerateJsonSchema):
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

        @model_validator(mode="after")
        def _model_validator_check_list_properties(cls, values: Any) -> Any:
            """
            Checks if all list properties are made of primitive types.
            """
            normalized_values: Dict[str, Any] = get_model_dump(values) if isinstance(values, BaseModel) else values

            for key, value in normalized_values.items():
                if isinstance(value, list):
                    for item in value:
                        if not isinstance(item, (int, float, str, bool)):
                            raise ValueError(f"List property {key} must be made of primitive types")

            return values

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

            if hasattr(self, "_relationship_properties"):
                for field_name in getattr(self, "_relationship_properties"):
                    if field_name in serialized:
                        serialized[field_name] = cast(RelationshipProperty, getattr(self, field_name)).nodes

            return serialized

        @classmethod
        def model_json_schema(cls, *args, **kwargs) -> Dict[str, Any]:
            kwargs.setdefault("schema_generator", CustomGenerateJsonSchema)
            return super().model_json_schema(*args, **kwargs)

    else:

        @root_validator
        def _root_validator_check_list_properties(cls, values: Any) -> Any:
            """
            Checks if all list properties are made of primitive types.
            """
            normalized_values: Dict[str, Any] = get_model_dump(values) if isinstance(values, BaseModel) else values

            for key, value in normalized_values.items():
                if isinstance(value, list):
                    for item in value:
                        if not isinstance(item, (int, float, str, bool)):
                            raise ValueError(f"List property {key} must be made of primitive types")

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

            if hasattr(self, "_relationship_properties"):
                for field_name in getattr(self, "_relationship_properties"):
                    field = cast(Union[RelationshipProperty, List], getattr(self, field_name))

                    if not isinstance(field, list) and not (exclude is not None and field_name in exclude):
                        modified_json[field_name] = [
                            cast(Union[RelationshipModel, NodeModel], node).json() for node in field.nodes
                        ]

            return json.dumps(modified_json)

    def __init__(self, *args, **kwargs) -> None:
        if not hasattr(self, "_client"):
            raise UnregisteredModel(model=self.__class__.__name__)

        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *args, **kwargs) -> None:
        setattr(cls, "_query_builder", QueryBuilder())

        logger.debug("Registering settings for model %s", cls.__name__)
        if hasattr(cls, "Settings"):
            for setting, value in cls.Settings.__dict__.items():
                if not setting.startswith("__"):
                    if isinstance(value, set) and getattr(cls._settings, setting, None) is not None:
                        setattr(
                            cls._settings,
                            setting,
                            value.union(getattr(cls._settings, setting)),
                        )
                    else:
                        setattr(cls._settings, setting, value)

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
        for name, value in self.__dict__.items():
            if not name.startswith("_"):
                yield name, value

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
