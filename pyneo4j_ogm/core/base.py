"""
Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
model types like registering hooks and exporting/importing models to/from dictionaries.
"""
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
from pydantic.class_validators import root_validator

from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2, get_model_dump
from pyneo4j_ogm.queries.query_builder import QueryBuilder

if TYPE_CHECKING:
    from pyneo4j_ogm.core.client import Pyneo4jClient
else:
    Pyneo4jClient = object

if IS_PYDANTIC_V2:
    from pydantic import model_validator

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

        @model_validator(mode="after")  # pyright: ignore[reportUnboundVariable]
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

        def dict(  # type: ignore
            self,
            *,
            include: IncEx = None,
            exclude: IncEx = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
        ) -> Dict[str, Any]:
            base_dict = super().dict(
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )

            element_id_field_name = self._get_alias("element_id") if by_alias else "element_id"
            id_field_name = self._get_alias("id") if by_alias else "id"

            if self._check_field_included(
                exclude=exclude,  # type: ignore
                include=include,  # type: ignore
                field_name=element_id_field_name,
            ):
                base_dict[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):  # type: ignore
                base_dict[id_field_name] = self._id

            return base_dict

        def model_dump(
            self,
            *,
            mode: str = "python",
            include: IncEx = None,
            exclude: IncEx = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool = True,
        ) -> Dict[str, Any]:
            base_dict = super().model_dump(
                mode=mode,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                round_trip=round_trip,
                warnings=warnings,
            )

            element_id_field_name = self._get_alias("element_id") if by_alias else "element_id"
            id_field_name = self._get_alias("id") if by_alias else "id"

            if self._check_field_included(
                exclude=exclude,  # type: ignore
                include=include,  # type: ignore
                field_name=element_id_field_name,
            ):
                base_dict[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):  # type: ignore
                base_dict[id_field_name] = self._id

            return base_dict

        def json(  # type: ignore
            self,
            *,
            include: IncEx = None,
            exclude: IncEx = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            encoder: Optional[Callable[[Any], Any]] = None,
            models_as_dict: bool = True,
            **dumps_kwargs: Any,
        ) -> str:
            base_json = super().json(
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                encoder=encoder,
                models_as_dict=models_as_dict,
                **dumps_kwargs,
            )

            element_id_field_name = self._get_alias("element_id") if by_alias else "element_id"
            id_field_name = self._get_alias("id") if by_alias else "id"

            modified_json = json.loads(base_json)

            if self._check_field_included(
                exclude=exclude,  # type: ignore
                include=include,  # type: ignore
                field_name=element_id_field_name,
            ):
                modified_json[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):  # type: ignore
                modified_json[id_field_name] = self._id

            return json.dumps(modified_json)

        def model_dump_json(
            self,
            *,
            indent: int | None = None,
            include: IncEx = None,
            exclude: IncEx = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool = True,
        ) -> str:
            base_json = super().model_dump_json(
                indent=indent,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                round_trip=round_trip,
                warnings=warnings,
            )

            element_id_field_name = (
                self._get_alias("element_id") if by_alias else "element_id" if by_alias else "element_id"
            )
            id_field_name = self._get_alias("id") if by_alias else "id" if by_alias else "id"

            modified_json = json.loads(base_json)

            if self._check_field_included(
                exclude=exclude,  # type: ignore
                include=include,  # type: ignore
                field_name=element_id_field_name,
            ):
                modified_json[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):  # type: ignore
                modified_json[id_field_name] = self._id

            return json.dumps(modified_json)

        def _get_alias(self, field_name: str) -> str:
            """
            Returns the field name to use for serialization.

            Args:
                field_name (str): The field name to search for aliases for.

            Returns:
                str: The field name to use for serialization.
            """
            serialization_name = field_name

            if "alias_generator" in self.model_config and self.model_config["alias_generator"] is not None:
                serialization_name = self.model_config["alias_generator"](field_name)

            return serialization_name

        def _check_field_included(self, exclude: IncEx, include: IncEx, field_name: str) -> bool:  # type: ignore
            """
            Checks if a field should be included in the serialization.

            Args:
                exclude (IncEx): The fields to exclude.
                include (IncEx): The fields to include.
                field_name (str): The field name to check.

            Returns:
                bool: Whether the field should be included in the serialization.
            """
            if exclude is not None and field_name in exclude:
                return False
            if include is not None and field_name not in include:
                return False
            if include is not None and field_name in include and exclude is not None and field_name in exclude:
                return True

            return True

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
            # pylint: disable=unexpected-keyword-arg
            base_dict = super().dict(
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                skip_defaults=skip_defaults,  # type: ignore
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )

            element_id_field_name = self._get_alias("element_id") if by_alias else "element_id"
            id_field_name = self._get_alias("id") if by_alias else "id"

            if self._check_field_included(exclude=exclude, include=include, field_name=element_id_field_name):
                base_dict[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):
                base_dict[id_field_name] = self._id

            return base_dict

        def json(  # type: ignore
            self,
            *,
            include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
            exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
            by_alias: bool = False,
            skip_defaults: Optional[bool] = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            encoder: Optional[Callable[[Any], Any]] = None,
            models_as_dict: bool = True,
            **dumps_kwargs: Any,
        ) -> str:
            base_json = super().json(
                include=include,  # type: ignore
                exclude=exclude,  # type: ignore
                by_alias=by_alias,
                skip_defaults=skip_defaults,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                encoder=encoder,
                models_as_dict=models_as_dict,
                **dumps_kwargs,
            )

            element_id_field_name = self._get_alias("element_id") if by_alias else "element_id"
            id_field_name = self._get_alias("id") if by_alias else "id"

            modified_json = json.loads(base_json)

            if self._check_field_included(exclude=exclude, include=include, field_name=element_id_field_name):
                modified_json[element_id_field_name] = self._element_id
            if self._check_field_included(exclude=exclude, include=include, field_name=id_field_name):
                modified_json[id_field_name] = self._id

            return json.dumps(modified_json)

        def _get_alias(self, field_name: str) -> str:
            """
            Returns the field name to use for serialization.

            Args:
                field_name (str): The field name to search for aliases for.

            Returns:
                str: The field name to use for serialization.
            """
            serialization_name = field_name

            if self.__config__.fields.get(field_name) is not None:  # type: ignore
                field = self.__config__.fields.get(field_name)  # type: ignore

                if isinstance(field, str):
                    serialization_name = field
                elif field is not None and "alias" in field:
                    serialization_name = field["alias"]
            elif self.__config__.alias_generator is not None:  # type: ignore
                serialization_name = self.__config__.alias_generator(field_name)  # type: ignore

            return serialization_name

        def _check_field_included(
            self,
            exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]],
            include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]],
            field_name: str,
        ) -> bool:
            """
            Checks if a field should be included in the serialization.

            Args:
                exclude (Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]]): The fields to exclude.
                include (Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]]): The fields to include.
                field_name (str): The field name to check.

            Returns:
                bool: Whether the field should be included in the serialization.
            """
            if exclude is not None and field_name in exclude:
                return False
            if include is not None and field_name not in include:
                return False
            if include is not None and field_name in include and exclude is not None and field_name in exclude:
                return True

            return True

    def __init__(self, *args, **kwargs) -> None:
        if not hasattr(self, "_client"):
            raise UnregisteredModel(model=self.__class__.__name__)

        super().__init__(*args, **kwargs)

    def __init_subclass__(cls) -> None:
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

        return super().__init_subclass__()

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
            "arbitrary_types_allowed": True,
        }
    else:

        class Config:
            """
            Pydantic configuration options.
            """

            validate_all = True
            validate_assignment = True
            revalidate_instances = "always"
            arbitrary_types_allowed = True
            underscore_attrs_are_private = True
