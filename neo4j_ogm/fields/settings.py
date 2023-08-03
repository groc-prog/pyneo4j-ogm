"""
This module contains possible settings for NodeModels and RelationshipModels
"""
from typing import Callable, Dict, List, Optional, Set, Union


class BaseModelSettings:
    """
    Shared settings for NodeModel and RelationshipModel classes or subclasses.
    """

    exclude_from_export: Set[str] = set()
    pre_hooks: Dict[str, Union[List[Callable], Callable]] = {}
    post_hooks: Dict[str, Union[List[Callable], Callable]] = {}


class NodeModelSettings(BaseModelSettings):
    """
    Settings for a NodeModel class or subclass.
    """

    labels: Optional[Union[List[str], str]] = None


class RelationshipModelSettings(BaseModelSettings):
    """
    Settings for a RelationshipModel class or subclass.
    """

    type: Optional[str] = None
