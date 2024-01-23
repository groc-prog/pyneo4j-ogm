# pylint: disable=unused-argument, unused-variable, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase, hooks
from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


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
