"""
Constants for default values.
"""

from typing import List

DEFAULT_CONFIG_URI = "bolt://localhost:7687"
DEFAULT_MIGRATION_DIR = "migrations"
DEFAULT_CONFIG_FILENAME: str = "migration-config.json"
DEFAULT_CONFIG_LABELS: List[str] = ["migration"]
MIGRATION_TEMPLATE = '''"""
Auto-generated migration file {name}. Do not
rename this file or the `up` and `down` functions.
"""
from pyneo4j_ogm import Pyneo4jClient


async def up(client: Pyneo4jClient) -> None:
    """
    Write your `UP migration` here.
    """
    pass


async def down(client: Pyneo4jClient) -> None:
    """
    Write your `DOWN migration` here.
    """
    pass
'''
