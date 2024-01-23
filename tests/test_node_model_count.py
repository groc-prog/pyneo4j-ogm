# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import patch

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import UnexpectedEmptyResult
from tests.fixtures.db_setup import Coffee, client, session, setup_test_data


async def test_count(setup_test_data):
    count = await Coffee.count({"milk": True})
    assert count == 3


async def test_count_no_match(setup_test_data):
    count = await Coffee.count({"flavor": "SomethingElse"})
    assert count == 0


async def test_count_no_query_result(client: Pyneo4jClient):
    await client.register_models([Coffee])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]
        with pytest.raises(UnexpectedEmptyResult):
            await Coffee.count({"milk": True})
