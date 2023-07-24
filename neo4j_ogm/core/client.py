"""
Database client for running queries against the connected database.
"""
import importlib
import inspect
import logging
import os
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Set, Tuple, Type

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction
from neo4j.graph import Node, Relationship

from neo4j_ogm.exceptions import (
    InvalidEntityType,
    InvalidIndexType,
    InvalidLabelOrType,
    MissingDatabaseURI,
    NotConnectedToDatabase,
    TransactionInProgress,
)

if TYPE_CHECKING:
    from neo4j_ogm.core.node import NodeModel
    from neo4j_ogm.core.relationship import RelationshipModel
else:
    NodeModel = object
    RelationshipModel = object


class IndexType(str, Enum):
    """
    Available indexing types.
    """

    RANGE = "RANGE"
    TEXT = "TEXT"
    POINT = "POINT"
    TOKEN = "TOKEN"


class EntityType(str, Enum):
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
    models: Set[Type[NodeModel | RelationshipModel]] = set()
    uri: str
    auth: Tuple[str, str] | None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def connect(self, uri: str | None = None, auth: Tuple[str, str] | None = None) -> None:
        """
        Establish a connection to a database.

        Args:
            uri (str | None, optional): Connection URI. If not provided, will try to fall back to
                NEO4J_URI environment variable. Defaults to None.
            auth (Tuple[str, str] | None, optional): Username and password authentication to use.
                Defaults to None.

        Raises:
            MissingDatabaseURI: Raised if no uri is provided and the NEO4J_URI env variable is
                not set
        """
        db_uri = uri if uri is not None else os.environ.get("NEO4J_URI", None)
        db_auth = auth if auth is not None else os.environ.get("NEO4J_AUTH", None)

        if db_uri is None:
            raise MissingDatabaseURI()

        self.uri = db_uri
        self.auth = db_auth

        logging.info("Connecting to database %s", self.uri)
        self._driver = AsyncGraphDatabase.driver(uri=self.uri, auth=self.auth)
        logging.info("Connected to database")

    @ensure_connection
    async def register_models(self, models: List[Type[NodeModel | RelationshipModel]]) -> None:
        """
        Registers models which are used with the client to resolve query results to their corresponding model
        instances.

        Args:
            models (List[Type[NodeModel | RelationshipModel]]): A list of models to register.
        """
        from neo4j_ogm.core.node import NodeModel
        from neo4j_ogm.core.relationship import RelationshipModel

        for model in models:
            if issubclass(model, (NodeModel, RelationshipModel)):
                self.models.add(model)

                for property_name, property_definition in model.__fields__.items():
                    entity_type = EntityType.NODE if issubclass(model, NodeModel) else EntityType.RELATIONSHIP
                    labels_or_type = (
                        getattr(model.__model_settings__, "labels")
                        if issubclass(model, NodeModel)
                        else getattr(model.__model_settings__, "type")
                    )

                    if getattr(property_definition.type_, "_unique", False):
                        await self.create_constraint(
                            name=f"{model.__name__}_{property_name}_unique_constraint",
                            entity_type=entity_type,
                            properties=[property_name],
                            labels_or_type=labels_or_type,
                        )
                    if getattr(property_definition.type_, "_range_index", False):
                        await self.create_index(
                            name=f"{model.__name__}_{property_name}_range_index",
                            entity_type=entity_type,
                            index_type=IndexType.RANGE,
                            properties=[property_name],
                            labels_or_type=labels_or_type,
                        )
                    if getattr(property_definition.type_, "_point_index", False):
                        await self.create_index(
                            name=f"{model.__name__}_{property_name}_point_index",
                            entity_type=entity_type,
                            index_type=IndexType.POINT,
                            properties=[property_name],
                            labels_or_type=labels_or_type,
                        )
                    if getattr(property_definition.type_, "_text_index", False):
                        await self.create_index(
                            name=f"{model.__name__}_{property_name}_text_index",
                            entity_type=entity_type,
                            index_type=IndexType.TEXT,
                            properties=[property_name],
                            labels_or_type=labels_or_type,
                        )

    @ensure_connection
    async def register_model_directory(self, directory: str) -> None:
        """
        Loads all NodeModel and RelationshipModel subclasses found in the directory.

        Args:
            directory (str): The directory to search in.
        """
        modules: List[str] = []

        logging.debug("Getting modules from directory %s", directory)
        for filename in os.listdir(directory):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = os.path.splitext(filename)[0]
                module = importlib.import_module(f"{directory}.{module_name}")
                modules.append(module)

        logging.debug("Checking module classes for models")
        for module in modules:
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, (NodeModel, RelationshipModel))
                    and not obj.__name__ in [NodeModel.__name__, RelationshipModel.__name__]
                ):
                    self.models.add(obj)

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
        self, query: str, parameters: Dict[str, Any] | None = None, resolve_models: bool = True
    ) -> Tuple[List[List[Any]], List[str]]:
        """
        Runs the provided cypher query with given parameters against the database.

        Args:
            query (str): Query to run.
            parameters (Dict[str, Any]): Parameters passed to the transaction.
            resolve_models (bool, optional): Whether to try and resolve query results to their corresponding database
                models or not. Defaults to True.

        Returns:
            Tuple[List[List[Any]], List[str]]: A tuple containing the query result and the names
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

            if self._batch_enabled is False:
                await self.commit_transaction()

            logging.info("Query completed")
            return results, meta
        except Exception as exc:
            logging.error("Encountered exception during transaction: %s", exc)
            if self._batch_enabled is False:
                await self.rollback_transaction()

            raise exc

    @ensure_connection
    async def create_constraint(
        self, name: str, entity_type: str, properties: List[str], labels_or_type: List[str] | str
    ) -> None:
        """
        Creates a constraint on nodes or relationships in the Neo4j database. Currently only `UNIQUENESS`
        constraints are supported.

        Args:
            name (str): The name of the constraint.
            entity_type (str): The type of entity the constraint is applied to. Must be either "NODE" or "RELATIONSHIP".
            properties (List[str]): A list of properties that should be unique for nodes/relationships satisfying
                the constraint.
            labels_or_type (List[str]): For nodes, a list of labels to which the constraint should be applied.
                For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
        """
        match entity_type:
            case EntityType.NODE:
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
            case EntityType.RELATIONSHIP:
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
                    available_types=[option.value for option in EntityType], entity_type=entity_type
                )

    @ensure_connection
    async def create_index(
        self, name: str, entity_type: str, index_type: str, properties: List[str], labels_or_type: List[str]
    ) -> None:
        """
        Creates a index on nodes or relationships in the Neo4j database.

        Args:
            name (str): The name of the constraint.
            entity_type (str): The type of entity the constraint is applied to. Must be either "NODE" or "RELATIONSHIP".
            index_type (str): The type of index to apply.
            properties (List[str]): A list of properties that should be unique for nodes/relationships satisfying
                the constraint.
            labels_or_type (List[str]): For nodes, a list of labels to which the constraint should be applied.
                For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
        """
        if index_type not in [index.value for index in IndexType]:
            raise InvalidIndexType(available_types=[option.value for option in IndexType], index_type=index_type)

        match entity_type:
            case EntityType.NODE:
                if not isinstance(labels_or_type, list):
                    raise InvalidLabelOrType()

                for label in labels_or_type:
                    match index_type:
                        case IndexType.TOKEN:
                            logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                            await self.cypher(
                                query=f"""
                                    CREATE LOOKUP INDEX {name} IF NOT EXISTS
                                    FOR (n)
                                    ON EACH labels(node)
                                """,
                                resolve_models=False,
                            )
                        case IndexType.RANGE:
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
            case EntityType.RELATIONSHIP:
                if not isinstance(labels_or_type, str):
                    raise InvalidLabelOrType()

                match index_type:
                    case IndexType.TOKEN:
                        logging.info("Creating %s index %s with labels %s", index_type, name, labels_or_type)
                        await self.cypher(
                            query=f"""
                                CREATE LOOKUP INDEX {name} IF NOT EXISTS
                                FOR ()-[r]-()
                                ON EACH type(r)
                            """,
                            resolve_models=False,
                        )
                    case IndexType.RANGE:
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
                    available_types=[option.value for option in EntityType], entity_type=entity_type
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
        if getattr(self, "_session", None):
            raise TransactionInProgress()

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

    def batch(self) -> "BatchManager":
        """
        Combine multiple transactions into a batch transaction.

        Returns:
            BatchManager: A class for managing batch transaction which can be used with a `with` statement.
        """
        return BatchManager(self)

    def _resolve_database_model(self, query_result: Node | Relationship) -> Type[NodeModel | RelationshipModel]:
        """
        Resolves a query result to the corresponding database model, if one is registered.

        Args:
            query_result (Node | Relationship): The query result to try to resolve.

        Returns:
            Type: The type of the resolved database model.
        """
        from neo4j_ogm.core.node import NodeModel
        from neo4j_ogm.core.relationship import RelationshipModel

        if not isinstance(query_result, (Node, Relationship)):
            return None

        labels = set(query_result.labels) if isinstance(query_result, Node) else set(query_result.type)

        for model in list(self.models):
            model_labels: set[str] = set()

            if issubclass(model, NodeModel):
                model_labels = set(getattr(model.__model_settings__, "labels"))
            elif issubclass(model, RelationshipModel):
                model_labels = set(model.__model_settings__)

            if labels == model_labels:
                return model

        return None


class BatchManager:
    """
    Class for handling batch transactions.
    """

    def __init__(self, client: "Neo4jClient") -> None:
        self._client = client

    async def __aenter__(self) -> None:
        self._client._batch_enabled = True
        await self._client.begin_transaction()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            await self._client.rollback_transaction()
        else:
            await self._client.commit_transaction()

        self._client._batch_enabled = False
