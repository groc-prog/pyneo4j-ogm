# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

from typing import LiteralString, cast
from unittest.mock import patch

import pytest
from neo4j import AsyncSession

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import NoResultsFound
from tests.fixtures.db_setup import (
    Coffee,
    Consumed,
    Developer,
    WorkedWith,
    client,
    coffee_model_instances,
    dev_model_instances,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_connect_not_allow_multiple(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    await client.register_models([Developer, Coffee, Consumed])

    john_model, *_ = dev_model_instances
    latte_model, mocha_model, *_ = coffee_model_instances
    updated_relationship = await john_model.coffee.connect(latte_model, {"liked": True})

    assert isinstance(updated_relationship, Consumed)
    assert updated_relationship.liked

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{Consumed.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": updated_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert result[0][0]["liked"]

    new_relationship = await john_model.coffee.connect(mocha_model, {"liked": False})

    assert isinstance(new_relationship, Consumed)
    assert not new_relationship.liked

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{Consumed.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": new_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert len(result) == 1
    assert not result[0][0]["liked"]


async def test_connect_allow_multiple(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, *_ = dev_model_instances

    new_relationship = await john_model.colleagues.connect(sam_model, {"language": "PHP"})

    assert isinstance(new_relationship, WorkedWith)
    assert new_relationship.language == "PHP"

    query_result = await session.run(
        cast(
            LiteralString,
            f"MATCH ()-[r:{WorkedWith.model_settings().type}]->() WHERE elementId(r) = $element_id RETURN r",
        ),
        {
            "element_id": new_relationship.element_id,
        },
    )
    result = await query_result.values()
    await query_result.consume()

    assert len(result) == 1
    assert result[0][0]["language"] == "PHP"


async def test_connect_no_result(
    client: Pyneo4jClient, session: AsyncSession, dev_model_instances, coffee_model_instances
):
    await client.register_models([Developer, WorkedWith])

    john_model, sam_model, *_ = dev_model_instances

    with patch.object(john_model.colleagues._client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(NoResultsFound):
            await john_model.colleagues.connect(sam_model, {"language": "PHP"})
