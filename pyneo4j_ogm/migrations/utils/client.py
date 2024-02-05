"""
Utility for Pyneo4jClient used in migrations.
"""

from typing import Any, Dict, Optional, cast

from neo4j import Auth, basic_auth, bearer_auth, custom_auth, kerberos_auth

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.migrations.utils.models import Migration, MigrationConfig
from pyneo4j_ogm.pydantic_utils import get_model_dump
from pyneo4j_ogm.queries.types import QueryOptionsOrder


class MigrationClient:
    """
    Utility for Pyneo4jClient used in migrations.
    """

    config: MigrationConfig
    client: Pyneo4jClient

    def __init__(self, config: MigrationConfig) -> None:
        self.client = Pyneo4jClient()
        self.config = config

    async def __aenter__(self):
        auth: Optional[Auth] = None
        Migration._settings.labels = set(self.config.neo4j.node_labels)

        if self.config.neo4j.options is not None and self.config.neo4j.options.scheme is not None:
            match self.config.neo4j.options.scheme:
                case "basic":
                    auth = basic_auth(
                        user=cast(Dict[str, Any], self.config.neo4j.options.auth)["username"],
                        password=cast(Dict[str, Any], self.config.neo4j.options.auth)["password"],
                    )
                case "kerberos":
                    auth = kerberos_auth(
                        base64_encoded_ticket=cast(Dict[str, Any], self.config.neo4j.options.auth)[
                            "base64_encoded_ticket"
                        ]
                    )
                case "bearer":
                    auth = bearer_auth(
                        base64_encoded_token=cast(Dict[str, Any], self.config.neo4j.options.auth)[
                            "base64_encoded_token"
                        ]
                    )
                case _:
                    auth = custom_auth(
                        principal=cast(Dict[str, Any], self.config.neo4j.options.auth)["principal"],
                        credentials=cast(Dict[str, Any], self.config.neo4j.options.auth)["credentials"],
                        realm=cast(Dict[str, Any], self.config.neo4j.options.auth)["realm"],
                        scheme=cast(Dict[str, Any], self.config.neo4j.options.auth)["scheme"],
                        **(
                            cast(Dict[str, Any], self.config.neo4j.options.auth)["parameters"]
                            if "parameters" in cast(Dict[str, Any], self.config.neo4j.options.auth)
                            else {}
                        ),
                    )

        await self.client.connect(
            uri=self.config.neo4j.uri,
            auth=auth,
            **(
                get_model_dump(self.config.neo4j.options, exclude={"scheme", "auth"})
                if self.config.neo4j.options is not None
                else {}
            ),
        )
        await self.client.register_models([Migration])

        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        await self.client.close()

    async def get_migration_node(self) -> Migration:
        """
        Get the migration node from the database.

        Returns:
            Migration: If a migration node exists, it will be returned. Otherwise, a
                new migration node will be created and returned.
        """
        migration = await Migration.find_many(
            options={"limit": 1, "sort": "updated_at", "order": QueryOptionsOrder.DESCENDING}
        )

        if len(migration) > 0 and isinstance(migration[0], Migration):
            return migration[0]

        migration = Migration()
        await migration.create()

        return migration
