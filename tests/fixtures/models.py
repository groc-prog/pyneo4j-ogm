from typing import Any, Dict

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.fields.relationship_property import RelationshipProperty
from pyneo4j_ogm.queries.enums import RelationshipPropertyDirection


class SinglePropModel(NodeModel):
    my_prop: str = "default"

    class Settings:
        labels = {"Test"}


class MultiPropModel(NodeModel):
    str_prop: str
    int_prop: int
    bool_prop: bool
    dict_prop: Dict[str, Any]

    class Settings:
        labels = {"Test"}


class NoPropModel(NodeModel):
    class Settings:
        labels = {"Test"}


class RelatedModelOne(NodeModel):
    name: str

    class Settings:
        labels = {"RelatedOne"}


class RelationshipOne(RelationshipModel):
    class Settings:
        type = "REL_ONE"


class RelatedModelTwo(NodeModel):
    name: str

    class Settings:
        labels = {"RelatedTwo"}


class RelationshipTwo(RelationshipModel):
    class Settings:
        type = "REL_TWO"


class RelPropModel(NodeModel):
    val: str = "val"

    relations_one: RelationshipProperty[RelatedModelOne, RelationshipOne] = RelationshipProperty(
        target_model=RelatedModelOne,
        relationship_model=RelationshipOne,
        direction=RelationshipPropertyDirection.OUTGOING,
    )
    relations_two: RelationshipProperty[RelatedModelTwo, RelationshipTwo] = RelationshipProperty(
        target_model=RelatedModelTwo,
        relationship_model=RelationshipTwo,
        direction=RelationshipPropertyDirection.INCOMING,
        allow_multiple=True,
    )
