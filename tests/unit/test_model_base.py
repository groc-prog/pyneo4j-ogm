# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring

from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import ModelImportFailure, UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings


def hook_func():
    pass


class TestNode(NodeModel):
    pass


class TestImportModel(NodeModel):
    my_prop: Optional[int]
    my_list: Optional[List[Dict]]


class TestModifiedProperties(NodeModel):
    a: str = "a"
    b: int = 1
    c: bool = True


class TestModelSettings(NodeModel):
    pass

    class Settings:
        exclude_from_export = {"exclude_from_export"}
        pre_hooks = {"test_hook": [hook_func]}
        post_hooks = {"test_hook": [hook_func, hook_func]}


setattr(TestNode, "_client", None)
setattr(TestImportModel, "_client", None)
setattr(TestModifiedProperties, "_client", None)


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


def test_pre_hooks():
    TestNode.register_pre_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", [lambda: None, lambda: None])
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", lambda: None)
    TestNode.register_pre_hooks("test_hook", lambda: None, overwrite=True)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []

    TestNode.register_pre_hooks("test_hook", lambda: None)
    TestNode.register_pre_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.pre_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.pre_hooks["test_hook"])
    TestNode.__settings__.pre_hooks["test_hook"] = []


def test_post_hooks():
    TestNode.register_post_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", [lambda: None, lambda: None])
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", [lambda: None, "invalid"])  # type: ignore
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", lambda: None)
    TestNode.register_post_hooks("test_hook", lambda: None, overwrite=True)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 1
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []

    TestNode.register_post_hooks("test_hook", lambda: None)
    TestNode.register_post_hooks("test_hook", lambda: None)
    assert len(TestNode.__settings__.post_hooks["test_hook"]) == 2
    assert all(callable(func) for func in TestNode.__settings__.post_hooks["test_hook"])
    TestNode.__settings__.post_hooks["test_hook"] = []


def test_import_model():
    model_dict = {
        "element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "my_prop": 2,
        "my_list": [{"list_dict_prop": "test"}],
    }

    model = TestImportModel.import_model(model_dict)

    assert model.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model.id == 13
    assert model.my_prop == 2
    assert model.my_list == [{"list_dict_prop": "test"}]

    model_dict_converted = {
        "elementId": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
        "id": 13,
        "myProp": 2,
        "myList": [{"listDictProp": "test"}],
    }

    model_converted = TestImportModel.import_model(model_dict_converted, from_camel_case=True)

    assert model_converted.element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"
    assert model_converted.id == 13
    assert model_converted.my_prop == 2
    assert model_converted.my_list == [{"list_dict_prop": "test"}]

    with pytest.raises(ModelImportFailure):
        TestImportModel.import_model({"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18"})
        TestImportModel.import_model({"id": 13})
        TestImportModel.import_model(
            {"element_id": "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18", "id": 13}, from_camel_case=True
        )


def test_model_settings():
    assert TestModelSettings.model_settings().exclude_from_export == {"exclude_from_export"}
    assert TestModelSettings.model_settings().pre_hooks == {"test_hook": [hook_func]}
    assert TestModelSettings.model_settings().post_hooks == {"test_hook": [hook_func, hook_func]}


def test_modified_properties():
    model = TestModifiedProperties()
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
