"""
Node- and RelationshipModels used for integration tests.
"""

# pyright: reportGeneralTypeIssues=false

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.fields.property_options import WithOptions


class TestNodeModel(NodeModel):
    a: WithOptions(str, unique=True)
    b: WithOptions(str, range_index=True)
    c: WithOptions(str, text_index=True)
    d: WithOptions(str, point_index=True)

    class Settings:
        labels = {"Test", "Node"}


class TestRelationshipModel(RelationshipModel):
    a: WithOptions(str, unique=True)
    b: WithOptions(str, range_index=True)
    c: WithOptions(str, text_index=True)
    d: WithOptions(str, point_index=True)

    class Settings:
        type = "TEST_RELATIONSHIP"
