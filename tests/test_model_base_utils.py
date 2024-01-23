# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import AsyncMock, MagicMock

from pyneo4j_ogm.core.base import hooks
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.fields.settings import BaseModelSettings
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
