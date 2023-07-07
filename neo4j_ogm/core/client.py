"""
Database client for running queries against the connected database.
"""
import logging
from os import environ
from typing import Any, Callable, Type

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction
from neo4j.graph import Node, Relationship

from neo4j_ogm.exceptions import InvalidConstraintEntity, MissingDatabaseURI, NotConnectedToDatabase


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
    node_models: list[Type] = []
    uri: str
    auth: tuple[str, str] | None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, node_models: list | None = None):
        """
        Registers models to be used by the client.

        Args:
            node_models (list | None, optional): A list of node models to register. All models not registered
                with the client will only return dictionaries from query results. Defaults to None.
        """
        if node_models is None:
            return

        for model in node_models:
            self.node_models.append(model)

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
    async def set_constraint(
        self, name: str, entity_type: str, properties: list[str], labels_or_type: list[str]
    ) -> None:
        """
        Sets a constraint on nodes or relationships in the Neo4j database. Currently only `UNIQUENESS` constraints are
        supported.

        Args:
            name (str): The name of the constraint.
            entity_type (str): The type of entity the constraint is applied to. Must be either "NODE" or "RELATIONSHIP".
            properties (list[str]): A list of properties that should be unique for nodes/relationships satisfying
                the constraint.
            labels_or_type (list[str]): For nodes, a list of labels to which the constraint should be applied.
                For relationships, a list with a single element representing the relationship type.

        Raises:
            InvalidConstraintEntity: If an invalid entity_type is provided.
        """
        if entity_type == "NODE":
            logging.info("Creating constraint %s with labels %s", name, labels_or_type)
            await self.cypher(
                query=f"""
                    CREATE CONSTRAINT {name} IF NOT EXISTS
                    FOR (node:{":".join(labels_or_type)})
                    REQUIRE ({", ".join([f"node.{property}" for property in properties])}) IS UNIQUE
                """,
                resolve_models=False,
            )
        elif entity_type == "RELATIONSHIP":
            logging.info("Creating constraint %s", name)
            await self.cypher(
                query="""
                        CREATE CONSTRAINT $name IF NOT EXISTS
                        FOR ()-[relationship:$type]-()
                        REQUIRE ($properties) IS UNIQUE
                    """,
                parameters={
                    "name": name,
                    "type": labels_or_type[0],
                    "properties": ", ".join([f"relationship.{property}" for property in properties]),
                },
                resolve_models=False,
            )
        else:
            raise InvalidConstraintEntity()

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

        for model in self.node_models:
            model_labels: set[str] = {}

            if hasattr(model, "__labels__"):
                model_labels = set(model.__labels__)
            elif hasattr(model, "__type__"):
                model_labels = set(model.__type__)

            if labels == model_labels:
                return model

        return None
