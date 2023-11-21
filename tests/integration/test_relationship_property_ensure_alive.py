# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring

import pytest

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import (
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidTargetNode,
)
from tests.fixtures.db_setup import (
    Coffee,
    Developer,
    WorkedWith,
    client,
    coffee_model_instances,
    dev_model_instances,
    session,
    setup_test_data,
)

pytest_plugins = ("pytest_asyncio",)


async def test_ensure_alive_not_hydrated(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    dev = Developer(name="Sindhu", age=23, uid=12)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceNotHydrated):
        await john_model.colleagues.connect(dev)


async def test_ensure_alive_destroyed(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    dev = Developer(name="Sindhu", age=23, uid=12)
    setattr(dev, "_element_id", "element-id")
    setattr(dev, "_id", 1)
    setattr(dev, "_destroyed", True)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceDestroyed):
        await john_model.colleagues.connect(dev)


async def test_ensure_alive_invalid_node(client: Pyneo4jClient, dev_model_instances, coffee_model_instances):
    await client.register_models([Developer, WorkedWith, Coffee])

    john_model, *_ = dev_model_instances
    latte_model, *_ = coffee_model_instances

    with pytest.raises(InvalidTargetNode):
        await john_model.colleagues.connect(latte_model)


async def test_ensure_alive_source_not_hydrated(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    dev = Developer(name="Sindhu", age=23, uid=12)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceNotHydrated):
        await dev.colleagues.connect(john_model)


async def test_ensure_alive_source_destroyed(client: Pyneo4jClient, dev_model_instances):
    await client.register_models([Developer, WorkedWith])

    dev = Developer(name="Sindhu", age=23, uid=12)
    setattr(dev, "_element_id", "element-id")
    setattr(dev, "_id", 1)
    setattr(dev, "_destroyed", True)

    john_model, *_ = dev_model_instances

    with pytest.raises(InstanceDestroyed):
        await dev.colleagues.connect(john_model)
