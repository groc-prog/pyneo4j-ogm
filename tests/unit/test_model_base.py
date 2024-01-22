# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

import json
from typing import Any, List, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
from pyneo4j_ogm.pydantic_utils import (
    IS_PYDANTIC_V2,
    get_model_dump,
    get_model_dump_json,
)
from tests.fixtures.db_setup import Coffee, Consumed, Developer


def hook_func():
    pass


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


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


def test_modified_properties():
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


async def test_hooks_decorator():
    class TestClass:
        def __init__(self):
            self._client = None  # type: ignore
            self._settings = BaseModelSettings()
            self._settings.pre_hooks["async_test_func"] = [AsyncMock(), AsyncMock()]
            self._settings.post_hooks["async_test_func"] = [AsyncMock(), AsyncMock()]
            self._settings.pre_hooks["sync_test_func"] = [
                MagicMock(__name__="MagicMock"),
                MagicMock(__name__="MagicMock"),
            ]
            self._settings.post_hooks["sync_test_func"] = [
                MagicMock(__name__="MagicMock"),
                MagicMock(__name__="MagicMock"),
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
        cast(AsyncMock, hook_function).assert_called_once_with(test_instance)

    for hook_function in test_instance._settings.post_hooks["async_test_func"]:
        cast(AsyncMock, hook_function).assert_called_once_with(test_instance, None)

    test_instance.sync_test_func()

    for hook_function in test_instance._settings.pre_hooks["sync_test_func"]:
        cast(AsyncMock, hook_function).assert_called_once_with(test_instance)

    for hook_function in test_instance._settings.post_hooks["sync_test_func"]:
        cast(AsyncMock, hook_function).assert_called_once_with(test_instance, None)


def test_dict_dump():
    def alias_gen(val: str) -> str:
        return f"ogm_{val}"

    class TestModel(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    class TestModelWithAlias(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

        if IS_PYDANTIC_V2:
            model_config = {"alias_generator": alias_gen}
        else:

            class Config:
                alias_generator = alias_gen

    setattr(TestModel, "_client", None)
    setattr(TestModelWithAlias, "_client", None)

    model = TestModel()
    setattr(model, "_element_id", "test-element-id")
    setattr(model, "_id", "test-id")
    model_dict = get_model_dump(model)

    assert "a" in model_dict
    assert "b" in model_dict
    assert "c" in model_dict
    assert "element_id" in model_dict
    assert "id" in model_dict

    assert model_dict["a"] == "a"
    assert model_dict["b"] == 1
    assert model_dict["c"] is True
    assert model_dict["element_id"] == "test-element-id"
    assert model_dict["id"] == "test-id"

    model_dict = get_model_dump(model, exclude={"id"}, include={"id", "element_id"})

    assert "id" not in model_dict
    assert "element_id" in model_dict

    alias_model = TestModelWithAlias()
    setattr(alias_model, "_element_id", "test-element-id")
    setattr(alias_model, "_id", "test-id")
    alias_model_dict = get_model_dump(alias_model)

    assert "a" in alias_model_dict
    assert "b" in alias_model_dict
    assert "c" in alias_model_dict
    assert "element_id" in alias_model_dict
    assert "id" in alias_model_dict

    alias_model_dict = get_model_dump(alias_model, by_alias=True)

    assert "ogm_a" in alias_model_dict
    assert "ogm_b" in alias_model_dict
    assert "ogm_c" in alias_model_dict
    assert "element_id" in alias_model_dict
    assert "id" in alias_model_dict

    assert alias_model_dict["ogm_a"] == "a"
    assert alias_model_dict["ogm_b"] == 1
    assert alias_model_dict["ogm_c"] is True
    assert alias_model_dict["element_id"] == "test-element-id"
    assert alias_model_dict["id"] == "test-id"


def test_json_dump():
    def alias_gen(val: str) -> str:
        return f"ogm_{val}"

    class TestModel(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

    class TestModelWithAlias(NodeModel):
        a: str = "a"
        b: int = 1
        c: bool = True

        if IS_PYDANTIC_V2:
            model_config = {"alias_generator": alias_gen}
        else:

            class Config:
                alias_generator = alias_gen

    setattr(TestModel, "_client", None)
    setattr(TestModelWithAlias, "_client", None)

    model = TestModel()
    setattr(model, "_element_id", "test-element-id")
    setattr(model, "_id", "test-id")
    model_dict = json.loads(get_model_dump_json(model))

    assert "a" in model_dict
    assert "b" in model_dict
    assert "c" in model_dict
    assert "element_id" in model_dict
    assert "id" in model_dict

    assert model_dict["a"] == "a"
    assert model_dict["b"] == 1
    assert model_dict["c"] is True
    assert model_dict["element_id"] == "test-element-id"
    assert model_dict["id"] == "test-id"

    model_dict = json.loads(get_model_dump_json(model, exclude={"id"}, include={"id", "element_id"}))

    assert "id" not in model_dict
    assert "element_id" in model_dict

    alias_model = TestModelWithAlias()
    setattr(alias_model, "_element_id", "test-element-id")
    setattr(alias_model, "_id", "test-id")
    alias_model_dict = json.loads(get_model_dump_json(alias_model))

    assert "a" in alias_model_dict
    assert "b" in alias_model_dict
    assert "c" in alias_model_dict
    assert "element_id" in alias_model_dict
    assert "id" in alias_model_dict

    alias_model_dict = json.loads(get_model_dump_json(alias_model, by_alias=True))

    assert "ogm_a" in alias_model_dict
    assert "ogm_b" in alias_model_dict
    assert "ogm_c" in alias_model_dict
    assert "element_id" in alias_model_dict
    assert "id" in alias_model_dict

    assert alias_model_dict["ogm_a"] == "a"
    assert alias_model_dict["ogm_b"] == 1
    assert alias_model_dict["ogm_c"] is True
    assert alias_model_dict["element_id"] == "test-element-id"
    assert alias_model_dict["id"] == "test-id"


def test_schema():
    setattr(Developer, "_client", None)
    setattr(Coffee, "_client", None)
    setattr(Consumed, "_client", None)
