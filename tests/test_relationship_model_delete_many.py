# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from unittest.mock import patch

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import UnexpectedEmptyResult
from tests.fixtures.db_setup import WorkedWith, client, session, setup_test_data


async def test_delete_many(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.delete_many({"language": "Javascript"})
    assert result == 2

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_delete_many_no_match(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    result = await WorkedWith.delete_many({"language": "non-existent"})
    assert result == 0

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_delete_many_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await WorkedWith.delete_many({"language": "non-existent"})
