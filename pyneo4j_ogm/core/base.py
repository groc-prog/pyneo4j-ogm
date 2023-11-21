"""
Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
model types like registering hooks and exporting/importing models to/from dictionaries.
"""
import asyncio
import json
import re
from asyncio import iscoroutinefunction
from copy import deepcopy
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    ParamSpec,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, PrivateAttr, root_validator

from pyneo4j_ogm.exceptions import ModelImportFailure, UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.queries.query_builder import QueryBuilder

if TYPE_CHECKING:
    from pyneo4j_ogm.core.client import Pyneo4jClient
else:
    Pyneo4jClient = object

P = ParamSpec("P")
T = TypeVar("T", bound="ModelBase")
U = TypeVar("U")
V = TypeVar("V")


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
            settings: BaseModelSettings = getattr(self, "__settings__")

            # Run pre hooks if defined
            logger.debug("Checking pre hooks for %s", func.__name__)
            if func.__name__ in settings.pre_hooks:
                for hook_function in settings.pre_hooks[func.__name__]:
                    if iscoroutinefunction(hook_function):
                        await hook_function(self, *args, **kwargs)
                    else:
                        hook_function(self, *args, **kwargs)

            if iscoroutinefunction(func):
                result = await func(self, *args, **kwargs)
            else:
                result = func(self, *args, **kwargs)

            # Run post hooks if defined
            logger.debug("Checking post hooks for %s", func.__name__)
            if func.__name__ in settings.post_hooks:
                for hook_function in settings.post_hooks[func.__name__]:
                    if iscoroutinefunction(hook_function):
                        await hook_function(self, result, *args, **kwargs)
                    else:
                        hook_function(self, result, *args, **kwargs)

            return result

    else:

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            settings: BaseModelSettings = getattr(self, "__settings__")
            loop = asyncio.get_event_loop()

            # Run pre hooks if defined
            logger.debug("Checking pre hooks for %s", func.__name__)
            if func.__name__ in settings.pre_hooks:
                for hook_function in settings.pre_hooks[func.__name__]:
                    if iscoroutinefunction(hook_function):
                        loop.run_until_complete(hook_function(self, *args, **kwargs))
                    else:
                        hook_function(self, *args, **kwargs)

            result = func(self, *args, **kwargs)

            # Run post hooks if defined
            logger.debug("Checking post hooks for %s", func.__name__)
            if func.__name__ in settings.post_hooks:
                for hook_function in settings.post_hooks[func.__name__]:
                    if iscoroutinefunction(hook_function):
                        loop.run_until_complete(hook_function(self, result, *args, **kwargs))
                    else:
                        hook_function(self, result, *args, **kwargs)

            return result

    return wrapper


class ModelBase(Generic[V], BaseModel):
    """
    Base class for both `NodeModel` and `RelationshipModel`. This class handles shared logic for both
    model types like registering hooks and exporting/importing models to/from dictionaries.

    Should not be used directly.
    """

    __settings__: BaseModelSettings = PrivateAttr()
    _client: Pyneo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _db_properties: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: Optional[str] = PrivateAttr(default=None)
    _id: Optional[int] = PrivateAttr(default=None)
    Settings: ClassVar[Type[BaseModelSettings]]

    @root_validator
    def _check_list_properties(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks if all list properties are made of primitive types.
        """
        for key, value in values.items():
            if isinstance(value, list):
                for item in value:
                    if not isinstance(item, (int, float, str, bool)):
                        raise ValueError(f"List property {key} must be made of primitive types")

        return values

    def __init__(self, *args, **kwargs) -> None:
        if not hasattr(self, "_client"):
            raise UnregisteredModel(model=self.__class__.__name__)

        super().__init__(*args, **kwargs)

    def __init_subclass__(cls) -> None:
        setattr(cls, "_query_builder", QueryBuilder())

        logger.debug("Setting up defined settings for model %s", cls.__name__)
        if hasattr(cls, "Settings"):
            for setting, value in cls.Settings.__dict__.items():
                if not setting.startswith("__"):
                    if isinstance(value, set) and getattr(cls.__settings__, setting, None) is not None:
                        setattr(
                            cls.__settings__,
                            setting,
                            value.union(getattr(cls.__settings__, setting)),
                        )
                    else:
                        setattr(cls.__settings__, setting, value)

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

    def export_model(self, convert_to_camel_case: bool = False, *args, **kwargs) -> Dict[str, Any]:
        """
        Export the model to a dictionary containing standard python types. This method accepts all
        arguments of `pydantic.BaseModel.json()`.

        Args:
            convert_to_camel_case (bool, optional): If set to `True`, the keys of the dictionary will be converted to
                camel-case. Defaults to `False`.

        Returns:
            Dict[str, Any]: The exported model as a dictionary.
        """
        logger.debug("Checking if additional fields should be excluded")
        if "exclude" in kwargs:
            kwargs["exclude"] = cast(Set, kwargs["exclude"]).union(self.__settings__.exclude_from_export)
        else:
            kwargs["exclude"] = self.__settings__.exclude_from_export

        logger.info("Exporting model %s", self.__class__.__name__)
        model_dict = json.loads(self.json(*args, **kwargs))
        model_dict["element_id"] = self._element_id
        model_dict["id"] = self._id

        if convert_to_camel_case:
            logger.debug("Converting keys to camel-case")
            model_dict = cast(Dict[str, Any], self._convert_to_camel_case(model_dict))

        return model_dict

    @classmethod
    def import_model(cls: Type[T], model: Dict[str, Any], from_camel_case: bool = False) -> T:
        """
        Import a model from a dictionary. The imported model will be seen as hydrated.

        Args:
            model (Dict[str, Any]): The model to import.
            from_camel_case (bool, optional): If set to `True`, the keys of the dictionary will be converted from
                camel-case to snake-case. Defaults to `False`.

        Raises:
            ModelImportFailure: The model is missing the `element_id` or `id` key or their respective camel-case
                variants.

        Returns:
            T: An instance of the model.
        """
        import_model = deepcopy(model)

        logger.info("Importing model %s", cls.__name__)
        if any(
            [
                "elementId" not in model and from_camel_case,
                "element_id" not in model and not from_camel_case,
                "id" not in model,
            ]
        ):
            raise ModelImportFailure()

        if from_camel_case:
            logger.debug("Converting keys from camel case")
            import_model = cast(Dict[str, Any], cls._convert_keys_to_snake_case(model))

        logger.debug("Hydrating model %s", import_model["element_id"])
        instance = cls(**import_model)
        instance._element_id = import_model["element_id"]
        instance._id = import_model["id"]

        return instance

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

        if hook_name not in cls.__settings__.pre_hooks:
            cls.__settings__.pre_hooks[hook_name] = []

        if overwrite:
            logger.debug("Overwriting existing pre-hook functions")
            cls.__settings__.pre_hooks[hook_name] = valid_hook_functions
        else:
            logger.debug("Adding %s pre-hook functions", len(valid_hook_functions))
            for hook_function in valid_hook_functions:
                cls.__settings__.pre_hooks[hook_name].append(hook_function)

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

        if hook_name not in cls.__settings__.post_hooks:
            cls.__settings__.post_hooks[hook_name] = []

        if overwrite:
            logger.debug("Overwriting existing post-hook functions")
            cls.__settings__.post_hooks[hook_name] = valid_hook_functions
        else:
            logger.debug("Adding %s post-hook functions", len(valid_hook_functions))
            for hook_function in valid_hook_functions:
                cls.__settings__.post_hooks[hook_name].append(hook_function)

    @classmethod
    def model_settings(cls) -> V:
        """
        Returns the model settings.

        Returns:
            V: The model settings.
        """
        return cast(V, cls.__settings__)

    @classmethod
    def _convert_to_camel_case(cls, model_dict: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any]]:
        """
        Recursively convert all keys in a dictionary to camel-case.

        Args:
            model_dict (Union[Dict[str, Any], List[Any]]): The dictionary to convert.

        Returns:
            Union[Dict[str, Any], List[Any]]: The dictionary with all keys converted to camelCase.
        """

        def to_camel_case(key: str) -> str:
            return key[0].lower() + re.sub(r"(?:_+)(\w)", lambda x: x.group(1).upper(), key[1:])

        if isinstance(model_dict, dict):
            return {to_camel_case(key): cls._convert_to_camel_case(value) for key, value in model_dict.items()}
        if isinstance(model_dict, list):
            return [cls._convert_to_camel_case(item) for item in model_dict]

        return model_dict

    @classmethod
    def _convert_keys_to_snake_case(
        cls, model_dict: Union[Dict[str, Any], List[Any]]
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Recursively convert all keys in a dictionary from camel-case to snake-case.

        Args:
            model_dict (Union[Dict[str, Any], List[Any]]): The dictionary to convert.

        Returns:
            Union[Dict[str, Any], List[Any]]: The dictionary with all keys converted to snake-case.
        """

        def to_snake_case(key: str) -> str:
            return re.sub(r"(?<!^)(?=[A-Z])|(?<=\w)(?=[A-Z][a-z])", "_", key).lower()

        if isinstance(model_dict, dict):
            return {to_snake_case(key): cls._convert_keys_to_snake_case(value) for key, value in model_dict.items()}
        if isinstance(model_dict, list):
            return [cls._convert_keys_to_snake_case(item) for item in model_dict]

        return model_dict

    @property
    def modified_properties(self) -> Set[str]:
        """
        Returns a set of properties which have been modified since the instance was hydrated.

        Returns:
            Set[str]: A set of properties which have been modified.
        """
        modified_properties = set()
        current_properties = self.dict()

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

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True
