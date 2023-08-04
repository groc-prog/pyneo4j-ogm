from typing import Any, Dict

from pydantic import BaseModel

from neo4j_ogm.core.node import NodeModel


class C(BaseModel):
    c: Dict[str, str]


class A(NodeModel):
    a: Dict[str, Any]
    aa: C
    aaa: int

    class Settings:
        exclude_from_export = {"a"}


class B(NodeModel):
    class Settings:
        labels = ("B", "BB")


def log():
    pass


A.register_post_hooks("a", log)


print("DONE")
