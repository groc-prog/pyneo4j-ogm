"""
Fixture for setup/teardown of unit tests using Operators instance.
"""
import pytest

from pyneo4j_ogm.queries.operators import Operators


@pytest.fixture
def operators():
    """
    Fixture for providing a Operators instance.
    """
    return Operators()
