# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
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

    assert not settings.pre_hooks
    assert not settings.post_hooks


def test_node_model_settings():
    settings = NodeModelSettings()

    assert settings.labels == set()
    assert settings.auto_fetch_nodes is None
    assert not settings.pre_hooks
    assert not settings.post_hooks


def test_node_model_settings_inheritance():
    class A(NodeModel):
        class Settings:
            auto_fetch_nodes = True
            post_hooks = {
                "save": lambda x: print("post save hook"),
                "delete": [lambda x: print("post delete hook"), None],
            }
            pre_hooks = {
                "delete": [lambda x: print("pre delete hook"), lambda x: print("pre delete hook")],
            }
            labels = {"A"}

    class B(A):
        class Settings:
            labels = {"B"}
            pre_hooks = {"save": lambda x: print("pre save hook B"), "delete": lambda x: print("pre delete hook")}
            post_hooks = {"delete": lambda x: print("post delete hook B")}

    assert getattr(A, "_settings", None) is not None
    assert isinstance(getattr(A, "_settings", None), NodeModelSettings)
    assert A._settings.labels == {"A"}
    assert A._settings.auto_fetch_nodes is True
    assert "delete" in A._settings.pre_hooks
    assert len(A._settings.pre_hooks["delete"]) == 2
    assert "save" in A._settings.post_hooks
    assert len(A._settings.post_hooks["save"]) == 1
    assert "delete" in A._settings.post_hooks
    assert len(A._settings.post_hooks["delete"]) == 1

    assert getattr(B, "_settings", None) is not None
    assert isinstance(getattr(B, "_settings", None), NodeModelSettings)
    assert B._settings.labels == {"A", "B"}
    assert B._settings.auto_fetch_nodes is True
    assert "save" in B._settings.pre_hooks
    assert len(B._settings.pre_hooks["save"]) == 1
    assert "delete" in B._settings.pre_hooks
    assert len(B._settings.pre_hooks["delete"]) == 3
    assert "save" in B._settings.post_hooks
    assert len(B._settings.post_hooks["save"]) == 1
    assert "delete" in B._settings.post_hooks
    assert len(B._settings.post_hooks["delete"]) == 2


def test_relationship_model_settings():
    settings = RelationshipModelSettings()

    assert not settings.pre_hooks
    assert not settings.post_hooks
    assert settings.type is None


def test_relationship_model_settings_inheritance():
    class A(RelationshipModel):
        class Settings:
            post_hooks = {
                "save": lambda x: print("post save hook"),
                "delete": [lambda x: print("post delete hook"), None],
            }
            pre_hooks = {
                "delete": [lambda x: print("pre delete hook"), lambda x: print("pre delete hook")],
            }
            type = "A"

    class B(A):
        class Settings:
            type = "B"
            pre_hooks = {"save": lambda x: print("pre save hook B"), "delete": lambda x: print("pre delete hook")}
            post_hooks = {"delete": lambda x: print("post delete hook B")}

    assert getattr(A, "_settings", None) is not None
    assert isinstance(getattr(A, "_settings", None), RelationshipModelSettings)
    assert A._settings.type == "A"
    assert "delete" in A._settings.pre_hooks
    assert len(A._settings.pre_hooks["delete"]) == 2
    assert "save" in A._settings.post_hooks
    assert len(A._settings.post_hooks["save"]) == 1
    assert "delete" in A._settings.post_hooks
    assert len(A._settings.post_hooks["delete"]) == 1

    assert getattr(B, "_settings", None) is not None
    assert isinstance(getattr(B, "_settings", None), RelationshipModelSettings)
    assert B._settings.type == "B"
    assert "save" in B._settings.pre_hooks
    assert len(B._settings.pre_hooks["save"]) == 1
    assert "delete" in B._settings.pre_hooks
    assert len(B._settings.pre_hooks["delete"]) == 3
    assert "save" in B._settings.post_hooks
    assert len(B._settings.post_hooks["save"]) == 1
    assert "delete" in B._settings.post_hooks
    assert len(B._settings.post_hooks["delete"]) == 2
