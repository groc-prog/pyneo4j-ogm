# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring

import pytest

from pyneo4j_ogm.core.base import ModelBase
from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.exceptions import UnregisteredModel


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()
