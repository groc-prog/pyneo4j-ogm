# pylint: disable=unused-argument, unused-variable, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import json
from typing import Union, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import ListItemNotEncodable, UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.pydantic_utils import get_model_dump, get_model_dump_json
from tests.fixtures.db_setup import Developer


def hook_func():
    pass


def test_pre_hooks():
    Developer.register_pre_hooks("test_hook", lambda: None)
    assert len(Developer._settings.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.pre_hooks["test_hook"])
    Developer._settings.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", [lambda: None, lambda: None])
    assert len(Developer._settings.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer._settings.pre_hooks["test_hook"])
    Developer._settings.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(Developer._settings.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.pre_hooks["test_hook"])
    Developer._settings.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", lambda: None)
    Developer.register_pre_hooks("test_hook", lambda: None, overwrite=True)
    assert len(Developer._settings.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.pre_hooks["test_hook"])
    Developer._settings.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", lambda: None)
    Developer.register_pre_hooks("test_hook", lambda: None)
    assert len(Developer._settings.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer._settings.pre_hooks["test_hook"])
    Developer._settings.pre_hooks["test_hook"] = []


def test_post_hooks():
    Developer.register_post_hooks("test_hook", lambda: None)
    assert len(Developer._settings.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.post_hooks["test_hook"])
    Developer._settings.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", [lambda: None, lambda: None])
    assert len(Developer._settings.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer._settings.post_hooks["test_hook"])
    Developer._settings.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(Developer._settings.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.post_hooks["test_hook"])
    Developer._settings.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", lambda: None)
    Developer.register_post_hooks("test_hook", lambda: None, overwrite=True)
    assert len(Developer._settings.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer._settings.post_hooks["test_hook"])
    Developer._settings.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", lambda: None)
    Developer.register_post_hooks("test_hook", lambda: None)
    assert len(Developer._settings.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer._settings.post_hooks["test_hook"])
    Developer._settings.post_hooks["test_hook"] = []


def test_model_settings():
    class ModelSettingsTest(NodeModel):
        pass

        class Settings:
            pre_hooks = {"test_hook": [hook_func]}
            post_hooks = {"test_hook": [hook_func, hook_func]}

    assert ModelSettingsTest.model_settings().pre_hooks == {"test_hook": [hook_func]}
    assert ModelSettingsTest.model_settings().post_hooks == {"test_hook": [hook_func, hook_func]}


def test_node_model_modified_properties():
    class ModifiedPropertiesTest(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(ModifiedPropertiesTest, "_client", None)

    model = ModifiedPropertiesTest()
    model.a = "modified"
    assert model.modified_properties == {"a"}

    model.b = 2
    assert model.modified_properties == {"a", "b"}


def test_relationship_model_modified_properties():
    class ModifiedPropertiesTest(RelationshipModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(ModifiedPropertiesTest, "_client", None)

    model = ModifiedPropertiesTest()
    model.a = "modified"
    assert model.modified_properties == {"a"}

    model.b = 2
    assert model.modified_properties == {"a", "b"}


async def test_hooks_decorator():
    class TestClass:
        def __init__(self):
            self._client = None  # type: ignore
            self._settings = BaseModelSettings()
            self._settings.pre_hooks["async_test_func"] = [MagicMock(__name__="MagicMock"), AsyncMock(), AsyncMock()]
            self._settings.post_hooks["async_test_func"] = [MagicMock(__name__="MagicMock"), AsyncMock(), AsyncMock()]
            self._settings.pre_hooks["sync_test_func"] = [
                MagicMock(__name__="MagicMock"),
                MagicMock(__name__="MagicMock"),
                AsyncMock(),
            ]
            self._settings.post_hooks["sync_test_func"] = [
                MagicMock(__name__="MagicMock"),
                MagicMock(__name__="MagicMock"),
                AsyncMock(),
            ]

        @hooks
        async def async_test_func(self):
            pass

        @hooks
        def sync_test_func(self):
            pass

    test_instance = TestClass()
    await test_instance.async_test_func()

    for hook_function in test_instance._settings.pre_hooks["async_test_func"]:
        cast(Union[MagicMock, AsyncMock], hook_function).assert_called_once_with(test_instance)

    for hook_function in test_instance._settings.post_hooks["async_test_func"]:
        cast(Union[MagicMock, AsyncMock], hook_function).assert_called_once_with(test_instance, None)

    test_instance.sync_test_func()

    for hook_function in test_instance._settings.pre_hooks["sync_test_func"]:
        cast(Union[MagicMock, AsyncMock], hook_function).assert_called_once_with(test_instance)

    for hook_function in test_instance._settings.post_hooks["sync_test_func"]:
        cast(Union[MagicMock, AsyncMock], hook_function).assert_called_once_with(test_instance, None)


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


def test_deflate_non_encodable_list():
    class NonEncodableModel(ModelBase):
        list_field: list = [object()]

    setattr(NonEncodableModel, "_client", None)

    with pytest.raises(ListItemNotEncodable):
        NonEncodableModel()._deflate({"list_field": [object()]})


def test_node_model_serialization():
    id_ = 1
    element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:1"
    expected = {"a": "a", "b": 1, "c": True, "id": id_, "element_id": element_id}

    class NodeModelClass(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(NodeModelClass, "_client", None)

    node_model = NodeModelClass()
    setattr(node_model, "_id", id_)
    setattr(node_model, "_element_id", element_id)

    node_model_dict = get_model_dump(node_model)
    node_model_json = get_model_dump_json(node_model)

    assert node_model_dict == expected
    assert json.loads(node_model_json) == expected


def test_relationship_model_serialization():
    id_ = 1
    element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:1"
    start_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:2"
    start_node_id = 2
    end_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:3"
    end_node_id = 3
    expected = {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }

    class RelationshipModelClass(RelationshipModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(RelationshipModelClass, "_client", None)

    relationship_model = RelationshipModelClass()
    setattr(relationship_model, "_id", id_)
    setattr(relationship_model, "_element_id", element_id)
    setattr(relationship_model, "_start_node_element_id", start_node_element_id)
    setattr(relationship_model, "_start_node_id", start_node_id)
    setattr(relationship_model, "_end_node_element_id", end_node_element_id)
    setattr(relationship_model, "_end_node_id", end_node_id)

    relationship_model_dict = get_model_dump(relationship_model)
    relationship_model_json = get_model_dump_json(relationship_model)

    assert relationship_model_dict == expected
    assert json.loads(relationship_model_json) == expected


def test_node_model_serialize_exclude():
    id_ = 1
    element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:1"
    expected_id_excluded = {"a": "a", "b": 1, "c": True, "element_id": element_id}
    expected_element_id_excluded = {"a": "a", "b": 1, "c": True, "id": id_}

    class NodeModelClass(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(NodeModelClass, "_client", None)

    node_model = NodeModelClass()
    setattr(node_model, "_id", id_)
    setattr(node_model, "_element_id", element_id)

    node_model_id_excluded_dict = get_model_dump(node_model, exclude={"id"})
    node_model_element_id_excluded_dict = get_model_dump(node_model, exclude={"element_id"})
    node_model_id_excluded_json = get_model_dump_json(node_model, exclude={"id"})
    node_model_element_id_excluded_json = get_model_dump_json(node_model, exclude={"element_id"})

    assert node_model_id_excluded_dict == expected_id_excluded
    assert node_model_element_id_excluded_dict == expected_element_id_excluded
    assert json.loads(node_model_id_excluded_json) == expected_id_excluded
    assert json.loads(node_model_element_id_excluded_json) == expected_element_id_excluded


def test_relationship_model_serialize_exclude():
    id_ = 1
    element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:1"
    start_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:2"
    start_node_id = 2
    end_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:3"
    end_node_id = 3

    class RelationshipModelClass(RelationshipModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    setattr(RelationshipModelClass, "_client", None)

    relationship_model = RelationshipModelClass()
    setattr(relationship_model, "_id", id_)
    setattr(relationship_model, "_element_id", element_id)
    setattr(relationship_model, "_start_node_element_id", start_node_element_id)
    setattr(relationship_model, "_start_node_id", start_node_id)
    setattr(relationship_model, "_end_node_element_id", end_node_element_id)
    setattr(relationship_model, "_end_node_id", end_node_id)

    assert get_model_dump(relationship_model, exclude={"id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert get_model_dump(relationship_model, exclude={"element_id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert get_model_dump(relationship_model, exclude={"start_node_element_id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert get_model_dump(relationship_model, exclude={"start_node_id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert get_model_dump(relationship_model, exclude={"end_node_element_id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
    }
    assert get_model_dump(relationship_model, exclude={"end_node_id"}) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
    }

    assert json.loads(get_model_dump_json(relationship_model, exclude={"id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert json.loads(get_model_dump_json(relationship_model, exclude={"element_id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert json.loads(get_model_dump_json(relationship_model, exclude={"start_node_element_id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert json.loads(get_model_dump_json(relationship_model, exclude={"start_node_id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "end_node_element_id": end_node_element_id,
        "end_node_id": end_node_id,
    }
    assert json.loads(get_model_dump_json(relationship_model, exclude={"end_node_element_id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_id": end_node_id,
    }
    assert json.loads(get_model_dump_json(relationship_model, exclude={"end_node_id"})) == {
        "a": "a",
        "b": 1,
        "c": True,
        "id": id_,
        "element_id": element_id,
        "start_node_element_id": start_node_element_id,
        "start_node_id": start_node_id,
        "end_node_element_id": end_node_element_id,
    }
