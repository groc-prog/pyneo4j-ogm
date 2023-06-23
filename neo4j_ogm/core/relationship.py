"""
This module holds the base relationship class `Neo4jRelationship` which is used to define database models for
relationships between nodes.
"""
import json
from typing import Any, TypeVar

from neo4j.graph import Node, Relationship
from pydantic import BaseModel

from neo4j_ogm.core.exceptions import InflationFailure

T = TypeVar("T", bound="Neo4jRelationship")


class Neo4jRelationship(BaseModel):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __type__: str
    __dict_fields = set()
    __model_fields = set()
    _element_id: str | None
    _start_node: Node | None
    _end_node: Node | None

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models fields for serialization
        """
        # Check if relationship type is set, if not fall back to model name
        if not hasattr(cls, "__type__"):
            cls.__type__ = cls.__name__

        for field, value in cls.__fields__.items():
            # Check if value is None here to prevent breaking logic if field is of type None
            if value.type_ is not None:
                if issubclass(value.type_, dict):
                    cls.__dict_fields.add(field)
                elif issubclass(value.type_, BaseModel):
                    cls.__model_fields.add(field)

        return super().__init_subclass__()

    def deflate(self) -> dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            dict[str, Any]: The deflated model instance
        """
        deflated: dict[str, Any] = json.loads(self.json())

        # Serialize nested BaseModel or dict instances to JSON strings
        for field in self.__dict_fields:
            deflated[field] = json.dumps(deflated[field])

        for field in self.__model_fields:
            deflated[field] = self.__dict__[field].json()

        return deflated

    @classmethod
    def inflate(cls, relationship: Relationship) -> T:
        """
        Inflates a relationship instance into a instance of the current model.

        Args:
            relationship (Relationship): Relationship to inflate

        Raises:
            InflationFailure: Raised if inflating the relationship fails

        Returns:
            T: A new instance of the current model with the properties from the relationship instance
        """
        inflated: dict[str, Any] = {}

        for relationship_property in relationship.items():
            property_name, property_value = relationship_property

            if property_name in cls.__dict_fields or property_name in cls.__model_fields:
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        return cls(
            _element_id=relationship.element_id,
            _start_node=relationship.start_node,
            _end_node=relationship.end_node,
            **inflated
        )
