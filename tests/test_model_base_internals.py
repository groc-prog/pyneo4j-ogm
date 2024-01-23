# pylint: disable=unused-argument, unused-variable, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyneo4j_ogm.core.base import ModelBase
from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.settings import BaseModelSettings


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()
