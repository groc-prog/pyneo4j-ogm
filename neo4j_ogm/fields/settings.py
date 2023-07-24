"""
This module contains possible settings for NodeModels and RelationshipModels
"""
from typing import Optional


class NodeModelSettings:
    """
    Settings for a NodeModel class or subclass.
    """

    labels: Optional[list[str] | str]


class RelationshipModelSettings:
    """
    Settings for a RelationshipModel class or subclass.
    """

    type: Optional[str]
