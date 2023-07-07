"""
Database client for running queries against the connected database.
"""
import logging
from enum import Enum
from os import environ
from typing import Any, Callable, Type

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction
from neo4j.graph import Node, Relationship

from neo4j_ogm.exceptions import (
    InvalidEntityType,
    InvalidIndexType,
    InvalidLabelOrType,
    MissingDatabaseURI,
    NotConnectedToDatabase,
)


class IndexTypes(str, Enum):
    """
    Available indexing types.
    """

    RANGE = "RANGE"
    TEXT = "TEXT"
    POINT = "POINT"
    TOKEN = "TOKEN"


class EntityTypes(str, Enum):
    """
    Available entity types.
    """

    NODE = "NODE"
    RELATIONSHIP = "RELATIONSHIP"


def ensure_connection(func: Callable):
    """
    Decorator which ensures that a connection to a database has been established before running
    any operations on it.

    Raises:
        NotConnectedToDatabase: Raised if the client is not connected to a database.
    """

    async def decorator(self, *args, **kwargs):
        if getattr(self, "_driver", None) is None:
            raise NotConnectedToDatabase()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class Neo4jClient:
    """
    Singleton database client class used to run different operations on the database.
    """

    _instance: "Neo4jClient"
    _driver: AsyncDriver
    _session: AsyncSession
    _transaction: AsyncTransaction
    _batch_enabled: bool = False
    models: set[Type] = set()
    uri: str
    auth: tuple[str, str] | None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def connect(self, uri: str | None = None, auth: tuple[str, str] | None = None) -> None:
        """
        Establish a connection to a database.

        Args:
            uri (str | None, optional): Connection URI. If not provided, will try to fall back to
                NEO4J_URI environment variable. Defaults to None.
            auth (tuple[str, str] | None, optional): Username and password authentication to use.
                Defaults to None.

        Raises:
            MissingDatabaseURI: Raised if no uri is provided and the NEO4J_URI env variable is
                not set
        """
        db_uri = uri if uri is not None else environ.get("NEO4J_URI", None)
        db_auth = auth if auth is not None else environ.get("NEO4J_AUTH", None)

        if db_uri is None:
            raise MissingDatabaseURI()

        self.uri = db_uri
        self.auth = db_auth

        logging.info("Connecting to database %s", self.uri)
        self._driver = AsyncGraphDatabase.driver(uri=self.uri, auth=self.auth)
        logging.info("Connected to database")

    @ensure_connection
    async def register_models(self, models: list[Type]) -> None:
        """
        Registers models which are used with the client to resolve query results to their corresponding model
        instances.

        Args:
            models (list[Type]): A list of models to register.
        """
        for model in models:
            self.models.add(model)

            for property_name, property_definition in model.__fields__.items():
                if getattr(property_definition.type_, "_unique", False):
                    await self.create_constraint(
                        name=f"{model.__name__}_{property_name}_unique_constraint",
                        entity_type=EntityTypes.NODE,
                        properties=[property_name],
                        labels_or_type=model.__labels__,
                    )
                if getattr(property_definition.type_, "_range_index", False):
                    await self.create_index(
                        name=f"{model.__name__}_{property_name}_range_index",
                        entity_type=EntityTypes.NODE,
                        index_type=IndexTypes.RANGE,
                        properties=[property_name],
                        labels_or_type=model.__labels__,
                    )
                if getattr(property_definition.type_, "_point_index", False):
                    await self.create_index(
                        name=f"{model.__name__}_{property_name}_point_index",
                        entity_type=EntityTypes.NODE,
                        index_type=IndexTypes.POINT,
                        properties=[property_name],
                        labels_or_type=model.__labels__,
                    )
                if getattr(property_definition.type_, "_text_index", False):
                    await self.create_index(
                        name=f"{model.__name__}_{property_name}_text_index",
                        entity_type=EntityTypes.NODE,
                        index_type=IndexTypes.TEXT,
                        properties=[property_name],
                        labels_or_type=model.__labels__,
                    )

    @ensure_connection
    async def close(self) -> None:
        """
        Closes the current connection to the client.
        """
        logging.info("Closing connection to database")
        await self._driver.close()
        logging.info("Connection to database closed")

    @ensure_connection
    async def cypher(
        self, query: str, parameters: dict[str, Any] | None = None, resolve_models: bool = True
    ) -> tuple[list[list[Any]], list[str]]:
        """
        Runs the provided cypher query with given parameters against the database.

        Args:
            query (str): Query to run.
            parameters (dict[str, Any]): Parameters passed to the transaction.
            resolve_models (bool, optional): Whether to try and resolve query results to their corresponding database
                models or not. Defaults to True.

        Returns:
            tuple[list[list[Any]], list[str]]: A tuple containing the query result and the names
                of the returned variables.
        """
        if parameters is None:
            parameters = {}

        if getattr(self, "_session", None) is None or getattr(self, "_transaction", None) is None:
            await self.begin_transaction()

        try:
            parameters = parameters if parameters is not None else {}

            logging.info("Running query %s with parameters %s", query, parameters)
            result_data = await self._transaction.run(query=query, parameters=parameters)

            results = [list(r.values()) async for r in result_data]
            meta = list(result_data.keys())

            if resolve_models:
                for list_index, result_list in enumerate(results):
                    for result_index, result in enumerate(result_list):
                        model = self._resolve_database_model(result)

                        if model is not None:
                            results[list_index][result_index] = model.inflate(result)

            await self.commit_transaction()

            logging.info("Query completed")
            return results, meta
        except Exception as exc:
            logging.error("Encountered exception during transaction: %s", exc)
            await self.rollback_transaction()

            raise exc

    @ensure_connection
    async def create_constraint(
        self, name: str, entity_type: str, properties: list[str], labels_or_type: list[str] | str
    ) -> None:
        """
        Creates a constraint on nodes or relationships in the Neo4j database. Currently only `UNIQUENESS`
        constraints are supported.

        Args:
            name (str): The name of the constraint.
            entity_type (str): The type of entity the constraint is applied to. Must be either "NODE" or "RELATIONSHIP".
            properties (list[str]): A list of properties that should be unique for nodes/relationships satisfying
                the constraint.
            labels_or_type (list[str]): For nodes, a list of labels to which the constraint should be applied.
                For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
        """
        match entity_type:
            case EntityTypes.NODE:
                if not isinstance(labels_or_type, list):
                    raise InvalidLabelOrType()

                for label in labels_or_type:
                    logging.info("Creating constraint %s with labels %s", name, label)
                    await self.cypher(
                        query=f"""
                            CREATE CONSTRAINT {name} IF NOT EXISTS
                            FOR (n:{label})
                            REQUIRE ({", ".join([f"n.{property}" for property in properties])}) IS UNIQUE
                        """,
                        resolve_models=False,
                    )
            case EntityTypes.RELATIONSHIP:
                if not isinstance(labels_or_type, str):
                    raise InvalidLabelOrType()

                logging.info("Creating constraint %s with labels %s", name, labels_or_type)
                await self.cypher(
                    query=f"""
                        CREATE CONSTRAINT {name} IF NOT EXISTS
                        FOR ()-[r:{labels_or_type}]-()
                        REQUIRE ({", ".join([f"r.{property}" for property in properties])}) IS UNIQUE
                    """,
                    resolve_models=False,
                )
            case _:
                raise InvalidEntityType(
                    available_types=[option.value for option in EntityTypes], entity_type=entity_type
                )

    @ensure_connection
    async def create_index(
        self, name: str, entity_type: str, index_type: str, properties: list[str], labels_or_type: list[str]
    ) -> None:
        """
        Creates a index on nodes or relationships in the Neo4j database.

        Args:
            name (str): The name of the constraint.
            entity_type (str): The type of entity the constraint is applied to. Must be either "NODE" or "RELATIONSHIP".
            index_type (str): The type of index to apply.
            properties (list[str]): A list of properties that should be unique for nodes/relationships satisfying
                the constraint.
            labels_or_type (list[str]): For nodes, a list of labels to which the constraint should be applied.
                For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
        """
        if index_type not in [index.value for index in IndexTypes]:
            raise InvalidIndexType(available_types=[option.value for option in IndexTypes], index_type=index_type)

        match entity_type:
            case EntityTypes.NODE:
                if not isinstance(labels_or_type, list):
                    raise InvalidLabelOrType()

                for label in labels_or_type:
                    match index_type:
                        case IndexTypes.TOKEN:
                            logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                            await self.cypher(
                                query=f"""
                                    CREATE LOOKUP INDEX {name} IF NOT EXISTS
                                    FOR (n)
                                    ON EACH labels(node)
                                """,
                                resolve_models=False,
                            )
                        case IndexTypes.RANGE:
                            logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                            await self.cypher(
                                query=f"""
                                    CREATE {index_type} INDEX {name} IF NOT EXISTS
                                    FOR (n:{label})
                                    ON ({", ".join([f"n.{property_name}" for property_name in properties])})
                                """,
                                resolve_models=False,
                            )
                        case _:
                            logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                            await self.cypher(
                                query=f"""
                                    CREATE {index_type} INDEX {name} IF NOT EXISTS
                                    FOR (n:{label})
                                    ON (n.{properties[0]})
                                """,
                                resolve_models=False,
                            )
            case EntityTypes.RELATIONSHIP:
                if not isinstance(labels_or_type, str):
                    raise InvalidLabelOrType()

                match index_type:
                    case IndexTypes.TOKEN:
                        logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                        await self.cypher(
                            query=f"""
                                CREATE LOOKUP INDEX {name} IF NOT EXISTS
                                FOR ()-[r]-()
                                ON EACH type(r)
                            """,
                            resolve_models=False,
                        )
                    case IndexTypes.RANGE:
                        logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                        await self.cypher(
                            query=f"""
                                CREATE {index_type} INDEX {name} IF NOT EXISTS
                                FOR ()-[r:{labels_or_type}]-()
                                ON ({", ".join([f"r.{property}" for property in properties])})
                            """,
                            resolve_models=False,
                        )
                    case _:
                        logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                        await self.cypher(
                            query=f"""
                                CREATE {index_type} INDEX {name} IF NOT EXISTS
                                FOR ()-[r:{labels_or_type}]-()
                                ON (r.{properties[0]})
                            """,
                            resolve_models=False,
                        )
            case _:
                raise InvalidEntityType(
                    available_types=[option.value for option in EntityTypes], entity_type=entity_type
                )

    @ensure_connection
    async def drop_nodes(self) -> None:
        """
        Deletes all nodes in the database.
        """
        logging.warning("Deleting all nodes in database")
        await self.cypher(query="MATCH (node) DETACH DELETE node", resolve_models=False)

    @ensure_connection
    async def drop_constraints(self) -> None:
        """
        Drops all constraints.
        """
        logging.debug("Discovering constraints")
        results, _ = await self.cypher(query="SHOW CONSTRAINTS", resolve_models=False)

        logging.warning("Dropping %s constraints", len(results))
        for constraint in results:
            logging.debug("Dropping constraint %s", constraint[1])
            await self.cypher(f"DROP CONSTRAINT {constraint[1]}")

    @ensure_connection
    async def drop_indexes(self) -> None:
        """
        Drops all indexes.
        """
        logging.debug("Discovering indexes")
        results, _ = await self.cypher(query="SHOW INDEXES", resolve_models=False)

        logging.warning("Dropping %s indexes", len(results))
        for index in results:
            logging.debug("Dropping index %s", index[1])
            await self.cypher(f"DROP INDEX {index[1]}")

    @ensure_connection
    async def begin_transaction(self) -> None:
        """
        Begin a new transaction from a session. If no session exists, a new one will be cerated.
        """
        logging.debug("Beginning new session")
        self._session = self._driver.session()
        logging.debug("Session %s created", self._session)

        logging.debug("Beginning new transaction for session %s", self._session)
        self._transaction = await self._session.begin_transaction()
        logging.debug("Transaction %s created", self._transaction)

    @ensure_connection
    async def commit_transaction(self) -> None:
        """
        Commits the currently active transaction and closes it.
        """
        logging.debug("Committing transaction %s", self._transaction)
        try:
            await self._transaction.commit()
        finally:
            self._session = None
            self._transaction = None

    @ensure_connection
    async def rollback_transaction(self) -> None:
        """
        Rolls back the currently active transaction and closes it.
        """
        logging.debug("Rolling back transaction %s", self._transaction)
        try:
            await self._transaction.rollback()
        finally:
            self._session = None
            self._transaction = None

    def _resolve_database_model(self, query_result: Node | Relationship) -> Type:
        """
        Resolves a query result to the corresponding database model, if one is registered.

        Args:
            query_result (Node | Relationship): The query result to try to resolve.

        Returns:
            Type: The type of the resolved database model.
        """
        labels = set(query_result.labels) if isinstance(query_result, Node) else set(query_result.type)

        for model in list(self.models):
            model_labels: set[str] = set()

            if hasattr(model, "__labels__"):
                model_labels = set(model.__labels__)
            elif hasattr(model, "__type__"):
                model_labels = set(model.__type__)

            if labels == model_labels:
                return model

        return None
