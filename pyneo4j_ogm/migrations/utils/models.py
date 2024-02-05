"""
Pydantic validation models for configuration file and migration node.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import Literal

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.migrations.utils.defaults import DEFAULT_CONFIG_LABELS
from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2

if IS_PYDANTIC_V2:
    from pydantic import model_validator
else:
    from pydantic import root_validator

Scheme = Literal["basic", "kerberos", "bearer", "custom"]
AuthKeys = Literal[
    "username",
    "password",
    "base64_encoded_ticket",
    "base64_encoded_token",
    "principal",
    "credentials",
    "realm",
    "scheme",
    "parameters",
]


class Neo4jDatabaseConfigOptions(BaseModel):
    """
    Neo4j database options. All options accepted by the official Neo4j driver are allowed in addition to the
    defined ones.
    """

    scheme: Optional[Scheme] = Field(default=None)
    auth: Optional[
        Dict[
            AuthKeys,
            Any,
        ]
    ] = Field(default=None)

    if IS_PYDANTIC_V2:

        @model_validator(mode="after")  # type: ignore
        def _validate_scheme_params(cls, values: "Neo4jDatabaseConfigOptions") -> Any:  # type: ignore
            if values.scheme is not None:
                if values.auth is None:
                    raise ValueError("Missing parameters for defined auth scheme")

                match values.scheme:
                    case "basic":
                        if "username" not in values.auth or "password" not in values.auth:
                            raise ValueError("Basic scheme requires username and password")
                    case "kerberos":
                        if "base64_encoded_ticket" not in values.auth:
                            raise ValueError("Kerberos scheme requires base64_encoded_ticket")
                    case "bearer":
                        if "base64_encoded_token" not in values.auth:
                            raise ValueError("Bearer scheme requires base64_encoded_token")

            return values

        model_config = {"extra": "allow"}
    else:

        @root_validator  # type: ignore
        def _validate_scheme_params(cls, values: Dict[str, Any]) -> Dict[str, Any]:
            if values["scheme"] is not None:
                if values["auth"] is None:
                    raise ValueError("Missing parameters for defined auth scheme")

                match values["scheme"]:
                    case "basic":
                        if "username" not in values["auth"] or "password" not in values["auth"]:
                            raise ValueError("Basic scheme requires username")
                    case "kerberos":
                        if "base64_encoded_ticket" not in values["auth"]:
                            raise ValueError("Kerberos scheme requires base64_encoded_ticket")
                    case "bearer":
                        if "base64_encoded_token" not in values["auth"]:
                            raise ValueError("Bearer scheme requires base64_encoded_token")

            return values

        class Config:
            extra = "allow"


class Neo4jDatabaseConfig(BaseModel):
    """
    Neo4j database configuration.
    """

    uri: str
    options: Optional[Neo4jDatabaseConfigOptions] = Neo4jDatabaseConfigOptions()
    node_labels: List[str] = DEFAULT_CONFIG_LABELS


class MigrationConfig(BaseModel):
    """
    Migration configuration. Used to validate the migration config file.
    """

    neo4j: Neo4jDatabaseConfig
    migration_dir: str


class AppliedMigration(BaseModel):
    """
    Log of applied migrations.
    """

    name: str
    applied_at: float = Field(default_factory=lambda: datetime.timestamp(datetime.now()))


class Migration(NodeModel):
    """
    Migration node model.
    """

    applied_migrations: List[AppliedMigration] = []
    updated_at: Optional[float] = Field(default=None)

    @property
    def get_applied_migration_identifiers(self) -> List[str]:
        """
        Returns:
            List[str]: Names of applied migrations
        """
        applied_migrations: List[str] = []

        for applied_migration in self.applied_migrations:
            identifier = applied_migration.name.split("-")[0]
            applied_migrations.append(identifier)

        return applied_migrations
