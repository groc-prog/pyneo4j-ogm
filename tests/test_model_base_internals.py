# pylint: disable=unused-argument, unused-variable, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

import pytest

from pyneo4j_ogm.core.base import ModelBase
from pyneo4j_ogm.exceptions import ListItemNotEncodable, UnregisteredModel


def test_unregistered_model_exc():
    with pytest.raises(UnregisteredModel):
        ModelBase()


def test_deflate_non_encodable_list():
    class NonEncodableModel(ModelBase):
        list_field: list = [object()]

    setattr(NonEncodableModel, "_client", None)

    with pytest.raises(ListItemNotEncodable):
        NonEncodableModel()._deflate({"list_field": [object()]})
