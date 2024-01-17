"""
Pydantic validation models for configuration file and migration node.
"""
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import field_validator
else:
    from pydantic import validator

INVALID_NEO4J_OPTIONS = ["resolver", "trusted_certificates", "ssl_context", "bookmark_manager"]
CONFIG_FILENAME: str = "migration-config.json"
MIGRATION_TEMPLATE = '''"""
Auto-generated migration file 20240115234453_something_awesome.py. Do not
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


class StatusActionFormat(enum.Enum):
    """
    Status action format.
    """

    RAW = "RAW"
    PRETTIFY = "PRETTIFY"


class Neo4jDatabaseConfig(BaseModel):
    """
    Neo4j database configuration.
    """

    uri: str = "bolt://localhost:7687"
    options: Optional[Dict[str, Any]] = None
    node_labels: List[str] = ["migration"]

    if IS_PYDANTIC_V2:

        @field_validator("options")  # type: ignore
        def _serialize_options(cls, options: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:  # type: ignore
            if options is None:
                return options

            for invalid_option in INVALID_NEO4J_OPTIONS:
                options.pop(invalid_option, None)

            if "auth" in options and isinstance(options["auth"], list):
                options["auth"] = tuple(options["auth"])

            return options

    else:

        @validator("options", pre=True)  # type: ignore
        def _serialize_options(cls, options: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            if options is None:
                return options

            for invalid_option in INVALID_NEO4J_OPTIONS:
                options.pop(invalid_option, None)

            if "auth" in options and isinstance(options["auth"], list):
                options["auth"] = tuple(options["auth"])

            return options


class StatusActionConfig(BaseModel):
    """
    Status action configuration.
    """

    default_format: Optional[StatusActionFormat] = None


class MigrationConfig(BaseModel):
    """
    Migration configuration. Used to validate the migration config file.
    """

    neo4j: Neo4jDatabaseConfig = Neo4jDatabaseConfig()
    migration_dir: str
    models_dir: Optional[str] = None
    status_action: StatusActionConfig = StatusActionConfig()


class AppliedMigration(BaseModel):
    """
    Log of applied migrations.
    """

    name: str
    applied_at: datetime


class Migration(NodeModel):
    """
    Migration node model.
    """

    applied_migrations: List[AppliedMigration] = Field(default_factory=list)
    last_applied: datetime
