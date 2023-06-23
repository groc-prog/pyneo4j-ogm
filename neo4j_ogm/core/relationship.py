"""
This module holds the base relationship class `Neo4jRelationship` which is used to define database models for
relationships between nodes.
"""
import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Neo4jRelationship(BaseModel):
    """
    Base model for all relationship models. Every relationship model should inherit from this class to have needed base
    functionality like de-/inflation and validation.
    """

    _element_id: str | None
    _start_node_element_id: str | None
    _end_node_element_id: str | None

    def deflate(self) -> dict[str, Any]:
        """
        Deflates the current model instance into a python dictionary which can be stored in Neo4j.

        Returns:
            dict[str, Any]: The deflated model instance
        """
        dicts: set[str] = set()
        models: set[str] = set()

        # Filter out other BaseModel or dict instances for serializing to JSON strings later
        for field, value in self.__fields__.items():
            # Check if value is None here to prevent breaking logic if field is of type None
            if value.type_ is not None:
                if issubclass(value.type_, dict):
                    dicts.add(field)
                elif issubclass(value.type_, BaseModel):
                    models.add(field)

        serialized_properties: dict[str, Any] = json.loads(self.json())

        # Serialize nested BaseModel or dict instances to JSON strings
        for field in dicts:
            serialized_properties[field] = json.dumps(serialized_properties[field])

        for field in models:
            serialized_properties[field] = self.__dict__[field].json()

        return serialized_properties

    @classmethod
    def inflate(cls, node):
        # Inflate from node to model
        pass


class Nested(BaseModel):
    a: str = "a"
    b: int = 1
    c: UUID = Field(default_factory=uuid4)
    h: list[str] = ["1", "2", "3"]
    j: datetime = Field(default_factory=datetime.now)


class Foo(Neo4jRelationship):
    d: dict = ({"foo": "foo", "bar": uuid4(), "foz": 1},)
    e: Nested = Nested()
    f: UUID = Field(default_factory=uuid4)
    g: list[str] = ["1", "2", "3"]
    i: datetime = Field(default_factory=datetime.now)
    k: None = None


foo = Foo()
a = foo.deflate()
print(a)
print("DONE")
