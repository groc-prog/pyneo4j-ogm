"""
Settings for model classes.
"""

# pyright: reportUnboundVariable=false

from typing import Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel
from pydantic.class_validators import validator

from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import field_validator


def _normalize_hooks(hooks: Dict[str, Union[List[Callable], Callable]]) -> Dict[str, List[Callable]]:
    """
    Normalize a list of hooks to a list of callables.
    """
    normalized_hooks: Dict[str, List[Callable]] = {}

    if isinstance(hooks, dict):
        for hook_name, hook_function in hooks.items():
            if callable(hook_function):
                normalized_hooks[hook_name] = [hook_function]
            elif isinstance(hook_function, list):
                normalized_hooks[hook_name] = [func for func in hook_function if callable(func)]

    return normalized_hooks


class BaseModelSettings(BaseModel):
    """
    Shared settings for NodeModel and RelationshipModel classes or subclasses.
    """

    pre_hooks: Dict[str, List[Callable]] = {}
    post_hooks: Dict[str, List[Callable]] = {}

    if IS_PYDANTIC_V2:
        normalize_pre_hooks = field_validator("pre_hooks", mode="before")(_normalize_hooks)
        normalize_post_hooks = field_validator("post_hooks", mode="before")(_normalize_hooks)
    else:
        normalize_pre_hooks = validator("pre_hooks", pre=True, allow_reuse=True)(_normalize_hooks)
        normalize_post_hooks = validator("post_hooks", pre=True, allow_reuse=True)(_normalize_hooks)

    if IS_PYDANTIC_V2:
        model_config = {
            "validate_assignment": True,
        }
    else:

        class Config:
            validate_assignment = True


class NodeModelSettings(BaseModelSettings):
    """
    Settings for a NodeModel class.
    """

    labels: Set[str] = set()
    auto_fetch_nodes: Optional[bool] = None


class RelationshipModelSettings(BaseModelSettings):
    """
    Settings for a RelationshipModel class.
    """

    type: Optional[str] = None
