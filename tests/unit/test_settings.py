# pylint: disable=missing-module-docstring

from pyneo4j_ogm.fields.settings import (
    BaseModelSettings,
    NodeModelSettings,
    RelationshipModelSettings,
    _normalize_hooks,
)


def hook_function():
    pass


def test_normalize_hooks_validator():
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
    settings = BaseModelSettings()

    assert settings.exclude_from_export == set()
    assert not settings.pre_hooks
    assert not settings.post_hooks


def test_node_model_settings():
    settings = NodeModelSettings()

    assert settings.labels == set()
    assert settings.auto_fetch_nodes is False
    assert settings.exclude_from_export == set()
    assert not settings.pre_hooks
    assert not settings.post_hooks


def test_relationship_model_settings():
    settings = RelationshipModelSettings()

    assert settings.exclude_from_export == set()
    assert not settings.pre_hooks
    assert not settings.post_hooks
    assert settings.type is None
