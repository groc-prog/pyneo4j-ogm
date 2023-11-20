# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import ModelImportFailure, UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
from tests.fixtures.db_setup import Developer


def hook_func():
    pass


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


def test_pre_hooks():
    Developer.register_pre_hooks("test_hook", lambda: None)
    assert len(Developer.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.pre_hooks["test_hook"])
    Developer.__settings__.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", [lambda: None, lambda: None])
    assert len(Developer.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer.__settings__.pre_hooks["test_hook"])
    Developer.__settings__.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(Developer.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.pre_hooks["test_hook"])
    Developer.__settings__.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", lambda: None)
    Developer.register_pre_hooks("test_hook", lambda: None, overwrite=True)
    assert len(Developer.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.pre_hooks["test_hook"])
    Developer.__settings__.pre_hooks["test_hook"] = []

    Developer.register_pre_hooks("test_hook", lambda: None)
    Developer.register_pre_hooks("test_hook", lambda: None)
    assert len(Developer.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer.__settings__.pre_hooks["test_hook"])
    Developer.__settings__.pre_hooks["test_hook"] = []


def test_post_hooks():
    Developer.register_post_hooks("test_hook", lambda: None)
    assert len(Developer.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.post_hooks["test_hook"])
    Developer.__settings__.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", [lambda: None, lambda: None])
    assert len(Developer.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer.__settings__.post_hooks["test_hook"])
    Developer.__settings__.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(Developer.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.post_hooks["test_hook"])
    Developer.__settings__.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", lambda: None)
    Developer.register_post_hooks("test_hook", lambda: None, overwrite=True)
    assert len(Developer.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in Developer.__settings__.post_hooks["test_hook"])
    Developer.__settings__.post_hooks["test_hook"] = []

    Developer.register_post_hooks("test_hook", lambda: None)
    Developer.register_post_hooks("test_hook", lambda: None)
    assert len(Developer.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in Developer.__settings__.post_hooks["test_hook"])
    Developer.__settings__.post_hooks["test_hook"] = []


def test_import_model():
    class ModelImportTest(NodeModel):
        my_prop: Optional[int]
        my_list: Optional[List[int]]

    setattr(ModelImportTest, "_client", None)

    model_dict = {
        "element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "my_prop": 2,
        "my_list": [1, 2],
    }

    model = ModelImportTest.import_model(model_dict)

    assert model.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model.id == 13
    assert model.my_prop == 2
    assert model.my_list == [1, 2]

    model_dict_converted = {
        "elementId": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "myProp": 2,
        "myList": [1, 2],
    }

    model_converted = ModelImportTest.import_model(model_dict_converted, from_camel_case=True)

    assert model_converted.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model_converted.id == 13
    assert model_converted.my_prop == 2
    assert model_converted.my_list == [1, 2]

    with pytest.raises(ModelImportFailure):
        ModelImportTest.import_model({"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"})
        ModelImportTest.import_model({"id": 13})
        ModelImportTest.import_model(
            {"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18", "id": 13}, from_camel_case=True
        )


def test_model_settings():
    class ModelSettingsTest(NodeModel):
        pass

        class Settings:
            exclude_from_export = {"exclude_from_export"}
            pre_hooks = {"test_hook": [hook_func]}
            post_hooks = {"test_hook": [hook_func, hook_func]}

    assert ModelSettingsTest.model_settings().exclude_from_export == {"exclude_from_export"}
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
            self.__settings__ = BaseModelSettings()
            self.__settings__.pre_hooks["async_test_func"] = [AsyncMock(), AsyncMock()]
            self.__settings__.post_hooks["async_test_func"] = [AsyncMock(), AsyncMock()]
            self.__settings__.pre_hooks["sync_test_func"] = [MagicMock(), MagicMock()]
            self.__settings__.post_hooks["sync_test_func"] = [MagicMock(), MagicMock()]

        @hooks
        async def async_test_func(self):
            pass

        @hooks
        def sync_test_func(self):
            pass

    test_instance = TestClass()
    await test_instance.async_test_func()

    for hook_function in test_instance.__settings__.pre_hooks["async_test_func"]:
        hook_function.assert_called_once_with(test_instance)

    for hook_function in test_instance.__settings__.post_hooks["async_test_func"]:
        hook_function.assert_called_once_with(test_instance, None)

    test_instance.sync_test_func()

    for hook_function in test_instance.__settings__.pre_hooks["sync_test_func"]:
        hook_function.assert_called_once_with(test_instance)

    for hook_function in test_instance.__settings__.post_hooks["sync_test_func"]:
        hook_function.assert_called_once_with(test_instance, None)


async def test_list_primitive_types():
    class AllowedListModel(ModelBase):
        list_field: List[Any] = [1, "a", True, 2.3]

    class DisallowedListModel(ModelBase):
        list_field: List[Any] = [{"test": True}, [1, 2]]

    setattr(AllowedListModel, "_client", None)
    setattr(DisallowedListModel, "_client", None)

    AllowedListModel()

    with pytest.raises(ValueError):
        DisallowedListModel()
