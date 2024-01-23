# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import MagicMock

import pytest

from pyneo4j_ogm.exceptions import UnregisteredModel
from pyneo4j_ogm.fields.relationship_property import check_models_registered


@pytest.fixture
def mock_relationship_property():
    mock_source_node = MagicMock()

    return MagicMock(
        _client=MagicMock(models={mock_source_node.__class__}),
        _source_node=mock_source_node,
        _target_model_name=MagicMock(),
        _relationship_model=MagicMock(),
    )


async def test_unregistered_source_model(mock_relationship_property):
    mock_relationship_property._client.models = {}

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)


async def test_unregistered_target_model(mock_relationship_property):
    mock_relationship_property._target_model = None

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)


async def test_unregistered_relationship_model(mock_relationship_property):
    mock_relationship_property._relationship_model = None

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)
