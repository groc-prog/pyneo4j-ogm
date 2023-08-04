"""
This module contains a modified version of Pydantic's BaseModel class adjusted to the needs of the
library. It adds additional methods for exporting the model to a dictionary and importing from a
dictionary.
"""
import json
import re
from asyncio import iscoroutinefunction
from typing import Any, Callable, ClassVar, Dict, List, ParamSpec, Set, Type, TypeVar, Union, cast

from pydantic import BaseModel, PrivateAttr, root_validator

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.exceptions import ModelImportFailure, ReservedPropertyName
from neo4j_ogm.fields.settings import BaseModelSettings
from neo4j_ogm.queries.query_builder import QueryBuilder

P = ParamSpec("P")
T = TypeVar("T", bound="ModelBase")
U = TypeVar("U")


def hooks(func: Callable[P, U]) -> Callable[P, U]:
    """
    Decorator which runs defined pre- and post hooks for the decorated method. The decorator expects the
    hooks to have the name of the decorated method.
    """

    async def decorator(self: T, *args, **kwargs) -> U:
        settings: BaseModelSettings = getattr(self, "_settings")

        # Run pre hooks if defined
        if func.__name__ in settings.pre_hooks:
            for hook_function in settings.pre_hooks[func.__name__]:
                if iscoroutinefunction(hook_function):
                    await hook_function(self, *args, **kwargs)
                else:
                    hook_function(self, *args, **kwargs)

        result = await func(self, *args, **kwargs)

        # Run post hooks if defined
        if func.__name__ in settings.post_hooks:
            for hook_function in settings.post_hooks[func.__name__]:
                if iscoroutinefunction(hook_function):
                    await hook_function(self, result, *args, **kwargs)
                else:
                    hook_function(self, result, *args, **kwargs)

        return result

    return decorator


class ModelBase(BaseModel):
    """
    This class is a modified version of Pydantic's BaseModel class adjusted to the needs of the library.
    It adds additional methods for exporting the model to a dictionary and importing from a dictionary.
    """

    _settings: BaseModelSettings
    _client: Neo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _db_properties: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: Union[str, None] = PrivateAttr(default=None)
    Settings: ClassVar[Type[BaseModelSettings]]

    @root_validator()
    def _validate_reserved_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        for value in ["element_id", "model_settings", "modified_properties"]:
            if value in values:
                raise ReservedPropertyName(value)

        return values

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._db_properties = self.dict()

    def __init_subclass__(cls) -> None:
        setattr(cls, "_client", Neo4jClient())
        setattr(cls, "_query_builder", QueryBuilder())

        if hasattr(cls, "Settings"):
            for setting, value in cls.Settings.__dict__.items():
                if not setting.startswith("__"):
                    if isinstance(value, set):
                        setattr(
                            cls._settings,
                            setting,
                            value.union(getattr(cls._settings, setting)),
                        )
                    else:
                        setattr(cls._settings, setting, value)

        return super().__init_subclass__()

    def __str__(self) -> str:
        hydration_msg = self._element_id if self._element_id is not None else "not hydrated"
        return f"{self.__class__.__name__}({hydration_msg})"

    def export_model(self: T, convert_to_camel_case: bool = False, *args, **kwargs) -> Dict[str, Any]:
        """
        Export the model to a dictionary containing standard python types. This method accepts all
        arguments of `pydantic.BaseModel.dict()`.

        Args:
            convert_to_camel_case (bool, optional): If set to True, the keys of the dictionary will be converted to
                camel case. Defaults to False.

        Returns:
            Dict[str, Any]: The exported model as a dictionary.
        """
        # Check if additional fields should be excluded
        if "exclude" in kwargs:
            kwargs["exclude"] = cast(Set, kwargs["exclude"]).union(self._settings.exclude_from_export)
        else:
            kwargs["exclude"] = self._settings.exclude_from_export

        model_dict = json.loads(self.json(*args, **kwargs))
        model_dict["element_id"] = self._element_id

        if convert_to_camel_case:
            model_dict = self._convert_to_camel_case(model_dict)

        return model_dict

    @classmethod
    def import_model(cls: Type[T], model: Dict[str, Any], from_camel_case: bool = False) -> T:
        """
        Import a model from a dictionary.

        Args:
            model (Dict[str, Any]): The model to import.
            from_camel_case (bool, optional): If set to True, the keys of the dictionary will be converted from
                camel case to snake case. Defaults to False.

        Raises:
            ModelImportFailure: If the model does not contain an `element_id` key.

        Returns:
            T: An instance of the model.
        """
        if from_camel_case and "elementId" not in model:
            raise ModelImportFailure()
        if not from_camel_case and "element_id" not in model:
            raise ModelImportFailure()

        if from_camel_case:
            model = cls._convert_keys_to_snake_case(model)

        instance = cls(**model)
        instance._element_id = model["element_id"]
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
                the same hook is registered. Defaults to False.
        """
        valid_hook_functions: List[Callable] = []

        if isinstance(hook_functions, list):
            for hook_function in hook_functions:
                if callable(hook_function):
                    valid_hook_functions.append(hook_function)
        elif callable(hook_functions):
            valid_hook_functions.append(hook_functions)

        # Create key if it does not exist
        if hook_name not in cls._settings.pre_hooks:
            cls._settings.pre_hooks[hook_name] = []

        if overwrite:
            cls._settings.pre_hooks[hook_name] = valid_hook_functions
        else:
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
                the same hook is registered. Defaults to False.
        """
        valid_hook_functions: List[Callable] = []

        if isinstance(hook_functions, list):
            for hook_function in hook_functions:
                if callable(hook_function):
                    valid_hook_functions.append(hook_function)
        elif callable(hook_functions):
            valid_hook_functions.append(hook_functions)

        # Create key if it does not exist
        if hook_name not in cls._settings.post_hooks:
            cls._settings.post_hooks[hook_name] = []

        if overwrite:
            cls._settings.post_hooks[hook_name] = valid_hook_functions
        else:
            for hook_function in valid_hook_functions:
                cls._settings.post_hooks[hook_name].append(hook_function)

    @classmethod
    def _convert_to_camel_case(cls, model_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively convert all keys in a dictionary to camelCase.

        Args:
            model_dict (dict): The dictionary to convert.

        Returns:
            dict: The dictionary with all keys converted to camelCase.
        """

        def to_camel_case(key: str) -> str:
            return key[0].lower() + re.sub(r"(?:_+)(\w)", lambda x: x.group(1).upper(), key[1:])

        if isinstance(model_dict, dict):
            return {to_camel_case(key): cls._convert_to_camel_case(value) for key, value in model_dict.items()}
        if isinstance(model_dict, list):
            return [cls._convert_to_camel_case(item) for item in model_dict]

        return model_dict

    @classmethod
    def _convert_keys_to_snake_case(cls, model_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively convert all keys in a dictionary from camelCase to snake_case.

        Args:
            model_dict (dict): The dictionary to convert.

        Returns:
            dict: The dictionary with all keys converted to snake_case.
        """

        def to_snake_case(key: str) -> str:
            return re.sub(r"(?<!^)(?=[A-Z])|(?<=\w)(?=[A-Z][a-z])", "_", key).lower()

        if isinstance(model_dict, dict):
            return {to_snake_case(key): cls._convert_keys_to_snake_case(value) for key, value in model_dict.items()}
        if isinstance(model_dict, list):
            return [cls._convert_keys_to_snake_case(item) for item in model_dict]

        return model_dict

    @property
    def modified_properties(self) -> List[str]:
        """
        Returns a list of properties which have been modified since the instance was hydrated.

        Returns:
            List[str]: A list of properties which have been modified.
        """
        modified_properties = []
        current_properties = self.dict()

        for property_name, property_value in self._db_properties.items():
            if current_properties[property_name] != property_value:
                modified_properties.append(property_name)

        return modified_properties

    @property
    def model_settings(self) -> List[str]:
        """
        Returns the settings defined for the model.
        """
        return self._settings

    class Config:
        """
        Pydantic configuration options.
        """

        validate_all = True
        validate_assignment = True
        revalidate_instances = "always"
        arbitrary_types_allowed = True
