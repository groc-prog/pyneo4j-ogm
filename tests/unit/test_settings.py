"""
Unit tests for neo4j_ogm.fields.settings.
"""
from neo4j_ogm.fields.settings import (
    BaseModelSettings,
    NodeModelSettings,
    RelationshipModelSettings,
    _normalize_hooks,
)


def hook_function():
    pass


def test_normalize_hooks():
    """
    Test that _normalize_hooks() returns a dict with only callable values and converts single functions to lists.
    """
    hooks = {
        "hook_list": [hook_function, "not a function"],
        "hook_function": hook_function,
        "hook_not_callable": "not a function",
    }

    normalized_hooks = _normalize_hooks(hooks)

    assert normalized_hooks == {
        "hook_list": [hook_function],
        "hook_function": [hook_function],
    }


def test_base_model_settings():
    """
    Test that BaseModelSettings is initialized correctly.
    """
    settings = BaseModelSettings()

    assert settings.exclude_from_export == set()
    assert settings.pre_hooks == {}
    assert settings.post_hooks == {}


def test_node_model_settings():
    """
    Test that NodeModelSettings is initialized correctly.
    """
    settings = NodeModelSettings()

    assert settings.labels == set()
    assert settings.auto_fetch_nodes is False
    assert settings.exclude_from_export == set()
    assert settings.pre_hooks == {}
    assert settings.post_hooks == {}


def test_relationship_model_settings():
    """
    Test that RelationshipModelSettings is initialized correctly.
    """
    settings = RelationshipModelSettings()

    assert settings.exclude_from_export == set()
    assert settings.pre_hooks == {}
    assert settings.post_hooks == {}
    assert settings.type is None
