"""
This module contains a modified version of Pydantic's BaseModel class adjusted to the needs of the library.
It adds additional methods for exporting the model to a dictionary and importing from a dictionary.
"""
import logging
from typing import Any, ClassVar, Dict, Set, TypeVar, Union, cast

from pydantic import BaseModel, PrivateAttr, root_validator

from neo4j_ogm.core.client import Neo4jClient
from neo4j_ogm.exceptions import ModelImportFailure, ReservedPropertyName
from neo4j_ogm.fields.settings import BaseModelSettings
from neo4j_ogm.queries.query_builder import QueryBuilder

T = TypeVar("T", bound="ModelBase")


class ModelBase(BaseModel):
    """
    This class is a modified version of Pydantic's BaseModel class adjusted to the needs of the library.
    It adds additional methods for exporting the model to a dictionary and importing from a dictionary.
    """

    __model_settings__: ClassVar[BaseModelSettings]
    _dict_properties = set()
    _model_properties = set()
    _client: Neo4jClient = PrivateAttr()
    _query_builder: QueryBuilder = PrivateAttr()
    _modified_properties: set[str] = PrivateAttr(default=set())
    _destroyed: bool = PrivateAttr(default=False)
    _element_id: Union[str, None] = PrivateAttr(default=None)

    @root_validator(pre=True)
    def _validate_reserved_fields(cls, _: Dict[str, Any]) -> Dict[str, Any]:
        if "element_id" in cls.__fields__.keys():
            raise ReservedPropertyName("element_id")

    def __init_subclass__(cls) -> None:
        cls._client = Neo4jClient()
        cls._query_builder = QueryBuilder()

        logging.debug("Collecting dict and model fields")
        for property_name, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if property_name is of type None
            if value.type_ is not None:
                if isinstance(value.default, dict):
                    cls._dict_properties.add(property_name)
                elif issubclass(value.type_, BaseModel):
                    cls._model_properties.add(property_name)

        return super().__init_subclass__()

    def export_model(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Export the model to a dictionary containing standard python types. This method accepts all
        arguments of `pydantic.BaseModel.dict()`.

        Returns:
            Dict[str, Any]: The exported model as a dictionary.
        """
        # Check if additional fields should be excluded
        if "exclude" in kwargs:
            kwargs["exclude"] = cast(Set, kwargs["exclude"]).union({"a"})

        model_dict = self.json(*args, **kwargs)
        model_dict["element_id"] = self._element_id
        return model_dict

    @classmethod
    def import_model(cls, model: Dict[str, Any]) -> T:
        """
        Import a model from a dictionary.

        Args:
            model (Dict[str, Any]): The model to import.

        Raises:
            ModelImportFailure: If the model does not contain an `element_id` key.

        Returns:
            T: An instance of the model.
        """
        if "element_id" not in model:
            raise ModelImportFailure()

        instance = cls(**model)
        instance._element_id = model["element_id"]
        return instance
