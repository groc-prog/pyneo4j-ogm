"""
Settings for NodeModel and RelationshipModel classes.
"""
from typing import Callable, Dict, List, Optional, Set, TypedDict, Union

from pydantic import BaseModel, validator


def _normalize_hooks(hooks: Dict[str, Union[List[Callable], Callable]]) -> Dict[str, List[Callable]]:
    """
    Normalize a list of hooks to a list of callables.
    """
    if isinstance(hooks, dict):
        for hook_name, hook_function in hooks.items():
            if not isinstance(hook_function, list) and callable(hook_function):
                hooks[hook_name] = [hook_function]
            elif not isinstance(hook_function, list) and not callable(hook_function):
                hooks[hook_name] = []
        return hooks

    return {}


class BaseModelSettings(BaseModel):
    """
    Shared settings for NodeModel and RelationshipModel classes or subclasses.
    """

    exclude_from_export: Set[str] = set()
    pre_hooks: Dict[str, Union[List[Callable], Callable]] = {}
    post_hooks: Dict[str, Union[List[Callable], Callable]] = {}

    normalize_pre_hooks = validator("pre_hooks", pre=True, allow_reuse=True)(_normalize_hooks)
    normalize_post_hooks = validator("post_hooks", pre=True, allow_reuse=True)(_normalize_hooks)

    class Config:
        validate_assignment = True


class NodeModelSettings(BaseModelSettings):
    """
    Settings for a NodeModel class.
    """

    labels: Optional[Union[Set[str], str]] = None
    auto_fetch_nodes: bool = False


class RelationshipModelSettings(BaseModelSettings):
    """
    Settings for a RelationshipModel class.
    """

    type: Optional[str] = None


class TypedNodeModelSettings(TypedDict):
    """
    Interface to describe the settings for a NodeModel class.
    """

    exclude_from_export: Set[str]
    pre_hooks: Dict[str, List[Callable]]
    post_hooks: Dict[str, List[Callable]]
    labels: Set[str]
    auto_fetch_nodes: bool


class TypedRelationshipModelSettings(TypedDict):
    """
    Interface to describe the settings for a RelationshipModel class.
    """

    exclude_from_export: Set[str]
    pre_hooks: Dict[str, List[Callable]]
    post_hooks: Dict[str, List[Callable]]
    type: str
