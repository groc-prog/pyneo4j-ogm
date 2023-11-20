# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from unittest.mock import patch

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data

pytest_plugins = ("pytest_asyncio",)


async def test_count(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.count({"language": "Python"})
    assert result == 2


async def test_count_no_match(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.count({"language": "non-existent"})
    assert result == 0


async def test_count_no_query_result(client: Pyneo4jClient, setup_test_data):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]
        with pytest.raises(NoResultsFound):
            await WorkedWith.count({})
