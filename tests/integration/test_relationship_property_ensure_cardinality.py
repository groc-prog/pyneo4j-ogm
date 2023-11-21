# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import (
    CardinalityViolation,
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidTargetNode,
)
from tests.fixtures.db_setup import (
    Bestseller,
    Coffee,
    CoffeeShop,
    client,
    coffee_model_instances,
    coffee_shop_model_instances,
    dev_model_instances,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_ensure_cardinality(client: Pyneo4jClient, coffee_shop_model_instances, coffee_model_instances):
    await client.register_models([CoffeeShop, Coffee, Bestseller])

    espresso_model = coffee_model_instances[2]
    rating_five_model, *_ = coffee_shop_model_instances

    with pytest.raises(CardinalityViolation):
        await rating_five_model.bestseller.connect(espresso_model)
