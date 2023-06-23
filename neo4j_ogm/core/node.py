"""
This module holds the base node class `Neo4jNode` which is used to define database models for nodes.
"""
import json
from typing import Any, TypeVar

from neo4j.graph import Node
from pydantic import BaseModel

from neo4j_ogm.core.exceptions import InflationFailure

T = TypeVar("T", bound="Neo4jNode")


class Neo4jNode(BaseModel):
    """
    Base model for all node models. Every node model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    __dict_fields = set()
    __model_fields = set()
    _element_id: str | None

    def __init_subclass__(cls) -> None:
        """
        Filters BaseModel and dict instances in the models fields for serialization
        """
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
    def inflate(cls, node: Node) -> T:
        """
        Inflates a node instance into a instance of the current model.

        Args:
            node (Node): Node to inflate

        Raises:
            InflationFailure: Raised if inflating the node fails

        Returns:
            T: A new instance of the current model with the properties from the node instance
        """
        inflated: dict[str, Any] = {}

        for relationship_property in node.items():
            property_name, property_value = relationship_property

            if property_name in cls.__dict_fields or property_name in cls.__model_fields:
                try:
                    inflated[property_name] = json.loads(property_value)
                except Exception as exc:
                    raise InflationFailure(cls.__name__) from exc
            else:
                inflated[property_name] = property_value

        return cls(_element_id=node.element_id, **inflated)
