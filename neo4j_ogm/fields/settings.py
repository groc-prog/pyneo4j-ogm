"""
This module contains possible settings for NodeModels and RelationshipModels
"""
from typing import List, Optional, Set, Union


class BaseModelSettings:
    """
    Shared settings for NodeModel and RelationshipModel classes or subclasses.
    """

    exclude_from_export: Set[str] = set()


class NodeModelSettings(BaseModelSettings):
    """
    Settings for a NodeModel class or subclass.
    """

    labels: Optional[Union[List[str], str]]


class RelationshipModelSettings(BaseModelSettings):
    """
    Settings for a RelationshipModel class or subclass.
    """

    type: Optional[str]


class RelationshipPropertySettings:
    """
    Settings for a RelationshipProperty class or subclass.
    """

    allow_multiple: bool = False
