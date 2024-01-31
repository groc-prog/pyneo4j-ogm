"""
Fixture for setup/teardown of unit tests using temporary paths.
"""
import os

import pytest


@pytest.fixture
def tmp_cwd(tmp_path):
    """
    Fixture for changing the cwd to the temporary path.
    """
    original_cwd = os.getcwd()

    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(original_cwd)
