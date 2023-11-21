"""
Pyneo4j database client class for running operations on the database.
"""
import os
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, cast

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction
from neo4j.exceptions import DatabaseError
from neo4j.graph import Node, Path, Relationship
from typing_extensions import LiteralString

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import (
    InvalidEntityType,
    InvalidIndexType,
    InvalidLabelOrType,
    MissingDatabaseURI,
    NotConnectedToDatabase,
    TransactionInProgress,
    UnsupportedNeo4jVersion,
)
from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.queries.query_builder import QueryBuilder


class IndexType(str, Enum):
    """
    Available indexing types.
    """

    RANGE = "RANGE"
    TEXT = "TEXT"
    POINT = "POINT"
    LOOKUP = "LOOKUP"


class EntityType(str, Enum):
    """
    Available graph entity types.
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
        logger.debug("Ensuring connection to database for %s", func.__name__)
        if getattr(self, "_driver", None) is None:
            raise NotConnectedToDatabase()

        result = await func(self, *args, **kwargs)

        return result

    return decorator


class Pyneo4jClient:
    """
    Database client class for running operations on the database.

    All models use a instance of this class to run operations on the database. Can also be used
    directly to run queries and other operations against the database. Provides methods for
    handling transactions/constraints/indexes and utility methods.
    """

    _builder: QueryBuilder
    _driver: Optional[AsyncDriver]
    _session: Optional[AsyncSession]
    _transaction: Optional[AsyncTransaction]
    _skip_constraints: bool
    _skip_indexes: bool
    _batch_enabled: bool = False
    models: Set[Type[NodeModel | RelationshipModel]]
    uri: str

    def __init__(self) -> None:
        self._builder = QueryBuilder()
        self.models = set()

    async def connect(
        self,
        uri: Optional[str] = None,
        *args,
        skip_constraints: bool = False,
        skip_indexes: bool = False,
        **kwargs,
    ) -> "Pyneo4jClient":
        """
        Establish a connection to a database.

        Args:
            uri (str | None, optional): Connection URI. If not provided, will try to fall back to
                NEO4J_URI environment variable. Defaults to `None`.
            skip_constraints (bool, optional): Whether to skip creating constraints on models or
                not. Defaults to `False`.
            skip_indexes (bool, optional): Whether to skip creating indexes on models or not.
                Defaults to `False`.

        Raises:
            MissingDatabaseURI: If no uri is provided and the NEO4J_URI env variable is not set.

        Returns:
            Pyneo4jClient: The client instance.
        """
        db_uri = uri if uri is not None else os.environ.get("NEO4J_OGM_URI", None)

        if db_uri is None:
            raise MissingDatabaseURI()

        self.uri = db_uri
        self._skip_constraints = skip_constraints
        self._skip_indexes = skip_indexes

        logger.info("Connecting to database %s", self.uri)
        self._driver = AsyncGraphDatabase.driver(uri=self.uri, *args, **kwargs)

        logger.debug("Checking Neo4j version")
        server_info = await self._driver.get_server_info()

        version = server_info.agent.split("/")[1]

        if int(version.split(".")[0]) < 5:
            raise UnsupportedNeo4jVersion()

        logger.info("Connected to database")
        return self

    @ensure_connection
    async def register_models(self, models: List[Type[Union[NodeModel, RelationshipModel]]]) -> None:
        """
        Registers models which are used with the client to resolve query results to their
        corresponding model instances.

        If a model is not registered with the client, it can not be used with model methods and other
        models can not use it with relationship-properties.

        Args:
            models (List[Type[NodeModel | RelationshipModel]]): A list of models to register.
        """
        logger.info("Registering models %s", models)

        for model in models:
            if issubclass(model, (NodeModel, RelationshipModel)):
                self.models.add(model)
                setattr(model, "_client", self)

                for property_name, property_definition in model.__fields__.items():
                    entity_type = EntityType.NODE if issubclass(model, NodeModel) else EntityType.RELATIONSHIP
                    labels_or_type = (
                        list(getattr(model.__settings__, "labels"))
                        if issubclass(model, NodeModel)
                        else getattr(model.__settings__, "type")
                    )

                    if not self._skip_constraints:
                        if getattr(property_definition.type_, "_unique", False):
                            await self.create_constraint(
                                name=model.__name__,
                                entity_type=entity_type,
                                properties=[property_name],
                                labels_or_type=labels_or_type,
                            )

                    if not self._skip_indexes:
                        if getattr(property_definition.type_, "_range_index", False):
                            await self.create_index(
                                name=model.__name__,
                                entity_type=entity_type,
                                index_type=IndexType.RANGE,
                                properties=[property_name],
                                labels_or_type=labels_or_type,
                            )
                        if getattr(property_definition.type_, "_point_index", False):
                            await self.create_index(
                                name=model.__name__,
                                entity_type=entity_type,
                                index_type=IndexType.POINT,
                                properties=[property_name],
                                labels_or_type=labels_or_type,
                            )
                        if getattr(property_definition.type_, "_text_index", False):
                            await self.create_index(
                                name=model.__name__,
                                entity_type=entity_type,
                                index_type=IndexType.TEXT,
                                properties=[property_name],
                                labels_or_type=labels_or_type,
                            )

    @ensure_connection
    async def close(self) -> None:
        """
        Closes the current connection to the database.
        """
        logger.info("Closing connection to database")
        await cast(AsyncDriver, self._driver).close()
        self._driver = None
        logger.info("Connection to database closed")

    @ensure_connection
    async def cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        resolve_models: bool = True,
    ) -> Tuple[List[List[Any]], List[str]]:
        """
        Runs the provided cypher query with given parameters against the database.

        Args:
            query (str): Query to run.
            parameters (Dict[str, Any]): Parameters passed to the transaction. Defaults to `None`.
            resolve_models (bool, optional): Whether to try and resolve query results to their
                corresponding database models or not. Defaults to `True`.

        Returns:
            Tuple[List[List[Any]], List[str]]: A tuple containing the query result and the names
                of the returned variables.
        """
        if parameters is None:
            parameters = {}

        logger.debug("Checking for open transaction")
        if getattr(self, "_session", None) is None or getattr(self, "_transaction", None) is None:
            await self._begin_transaction()

        try:
            parameters = parameters if parameters is not None else {}

            logger.debug("Running query \n%s \nwith parameters %s", query, parameters)
            result_data = await cast(AsyncTransaction, self._transaction).run(
                query=cast(LiteralString, query), parameters=parameters
            )

            results = [list(r.values()) async for r in result_data]
            meta = list(result_data.keys())

            if resolve_models:
                logger.debug("Resolving results to models")
                for list_index, result_list in enumerate(results):
                    for result_index, result in enumerate(result_list):
                        resolved = self._resolve_database_model(result)

                        if resolved is not None:
                            results[list_index][result_index] = resolved

            if self._batch_enabled is False:
                await self._commit_transaction()

            logger.debug("Query finished with results %s", results)
            return results, meta
        except Exception as exc:
            logger.error("Error running query %s", exc)
            if self._batch_enabled is False:
                await self._rollback_transaction()

            raise exc

    @ensure_connection
    async def create_constraint(
        self,
        name: str,
        entity_type: EntityType,
        properties: List[str],
        labels_or_type: Union[List[str], str],
    ) -> None:
        """
        Creates a constraint on nodes or relationships in the Neo4j database. Currently only
        `UNIQUENESS` constraints are supported.

        Args:
            name (str): The name of the constraint.
            entity_type (EntityType): The type of entity the constraint is applied to. Must be either
                `NODE` or `RELATIONSHIP`.
            properties (List[str]): A list of properties that should be unique for
                nodes/relationships satisfying the constraint.
            labels_or_type (List[str]): For nodes, a list of labels to which the constraint should
                be applied. For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
        """
        match entity_type:
            case EntityType.NODE:
                if not isinstance(labels_or_type, list):
                    raise InvalidLabelOrType()

                for label in labels_or_type:
                    constraint_name = f"{name}_{label}_{'_'.join(properties)}_unique_constraint"

                    logger.info("Creating constraint %s for node with label %s", constraint_name, label)
                    await self.cypher(
                        query=f"""
                            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                            FOR {self._builder.node_match(labels=[label])}
                            REQUIRE ({", ".join([f"n.{property}" for property in properties])}) IS UNIQUE
                        """,
                        resolve_models=False,
                    )
            case EntityType.RELATIONSHIP:
                if not isinstance(labels_or_type, str):
                    raise InvalidLabelOrType()

                constraint_name = f"{name}_{labels_or_type}_{'_'.join(properties)}_unique_constraint"

                logger.info("Creating constraint %s for relationship with type %s", constraint_name, labels_or_type)
                await self.cypher(
                    query=f"""
                        CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                        FOR {self._builder.relationship_match(type_=labels_or_type)}
                        REQUIRE ({", ".join([f"r.{property}" for property in properties])}) IS UNIQUE
                    """,
                    resolve_models=False,
                )
            case _:
                raise InvalidEntityType(
                    available_types=[option.value for option in EntityType],
                    entity_type=entity_type,
                )

    @ensure_connection
    async def create_index(
        self,
        name: str,
        entity_type: EntityType,
        index_type: IndexType,
        properties: Union[List[str], str],
        labels_or_type: Union[List[str], str],
    ) -> None:
        """
        Creates a index on nodes or relationships in the Neo4j database.

        Args:
            name (str): The name of the constraint.
            entity_type (EntityType): The type of entity the constraint is applied to. Must be either
                `NODE` or `RELATIONSHIP`.
            index_type (IndexType): The type of index to apply.
            properties (Union[List[str], str]): A list of properties or a single property that should be
                indexed for nodes/relationships.
            labels_or_type (Union[List[str], str]): For nodes, a list of labels to which the constraint should
                be applied. For relationships, a string representing the relationship type.

        Raises:
            InvalidEntityType: If an invalid entity_type is provided.
            InvalidIndexType: If an invalid index_type is provided.
        """
        formatted_properties = properties if isinstance(properties, list) else [properties]

        if index_type not in [index.value for index in IndexType]:
            raise InvalidIndexType(
                available_types=[option.value for option in IndexType],
                index_type=index_type,
            )

        normalized_index_type = index_type.value if isinstance(index_type, IndexType) else str(index_type).upper()

        match entity_type:
            case EntityType.NODE:
                if not isinstance(labels_or_type, list):
                    raise InvalidLabelOrType()

                match normalized_index_type:
                    case IndexType.LOOKUP:
                        index_name = f"{name}_{'_'.join(labels_or_type)}_{'_'.join(formatted_properties)}_lookup_index"

                        logger.info(
                            "Creating %s index %s for node with labels %s",
                            normalized_index_type,
                            index_name,
                            labels_or_type,
                        )
                        await self.cypher(
                            query=f"""
                                CREATE LOOKUP INDEX {index_name} IF NOT EXISTS
                                FOR {self._builder.node_match()}
                                ON EACH labels(n)
                            """,
                            resolve_models=False,
                        )
                    case IndexType.RANGE:
                        for label in labels_or_type:
                            index_name = f"{name}_{label}_{'_'.join(formatted_properties)}_range_index"

                            logger.info(
                                "Creating %s index %s for node with labels %s",
                                normalized_index_type,
                                index_name,
                                labels_or_type,
                            )
                            await self.cypher(
                                query=f"""
                                    CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                    FOR {self._builder.node_match(labels=[label])}
                                    ON ({", ".join([f"n.{property_name}" for property_name in formatted_properties])})
                                """,
                                resolve_models=False,
                            )
                    case IndexType.TEXT:
                        for label in labels_or_type:
                            for property_name in formatted_properties:
                                index_name = f"{name}_{label}_{property_name}_text_index"

                                logger.info(
                                    "Creating %s index %s for node with labels %s",
                                    normalized_index_type,
                                    index_name,
                                    labels_or_type,
                                )
                                await self.cypher(
                                    query=f"""
                                        CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                        FOR {self._builder.node_match(labels=[label])}
                                        ON (n.{property_name})
                                    """,
                                    resolve_models=False,
                                )
                    case IndexType.POINT:
                        for label in labels_or_type:
                            for property_name in formatted_properties:
                                index_type_name = f"{IndexType(normalized_index_type).value}".lower()
                                index_name = f"{name}_{label}_{property_name}_{index_type_name}_index"

                                logger.info(
                                    "Creating %s index %s for node with labels %s",
                                    normalized_index_type,
                                    index_name,
                                    labels_or_type,
                                )
                                await self.cypher(
                                    query=f"""
                                        CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                        FOR (n:{label})
                                        ON (n.{property_name})
                                    """,
                                    resolve_models=False,
                                )
            case EntityType.RELATIONSHIP:
                if not isinstance(labels_or_type, str):
                    raise InvalidLabelOrType()

                match normalized_index_type:
                    case IndexType.LOOKUP:
                        index_name = f"{name}_{labels_or_type}_{'_'.join(formatted_properties)}_lookup_index"

                        logger.info(
                            "Creating %s index %s for relationship with labels %s",
                            normalized_index_type,
                            index_name,
                            labels_or_type,
                        )
                        await self.cypher(
                            query=f"""
                                CREATE LOOKUP INDEX {index_name} IF NOT EXISTS
                                FOR {self._builder.relationship_match()}
                                ON EACH type(r)
                            """,
                            resolve_models=False,
                        )
                    case IndexType.RANGE:
                        index_name = f"{name}_{labels_or_type}_{'_'.join(formatted_properties)}_range_index"

                        logger.info(
                            "Creating %s index %s for relationship with labels %s",
                            normalized_index_type,
                            index_name,
                            labels_or_type,
                        )
                        await self.cypher(
                            query=f"""
                                CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                FOR {self._builder.relationship_match(type_=labels_or_type)}
                                ON ({", ".join([f"r.{property}" for property in formatted_properties])})
                            """,
                            resolve_models=False,
                        )
                    case IndexType.TEXT:
                        for property_name in formatted_properties:
                            index_name = f"{name}_{labels_or_type}_{property_name}_text_index"

                            logger.info(
                                "Creating %s index %s for relationship with labels %s",
                                normalized_index_type,
                                index_name,
                                labels_or_type,
                            )
                            await self.cypher(
                                query=f"""
                                    CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                    FOR {self._builder.relationship_match(type_=labels_or_type)}
                                    ON (r.{property_name})
                                """,
                                resolve_models=False,
                            )
                    case IndexType.POINT:
                        for property_name in formatted_properties:
                            index_type_name = f"{IndexType(normalized_index_type).value}".lower()
                            index_name = f"{name}_{labels_or_type}_{property_name}_{index_type_name}_index"

                            logger.info(
                                "Creating %s index %s for relationship with labels %s",
                                normalized_index_type,
                                index_name,
                                labels_or_type,
                            )
                            await self.cypher(
                                query=f"""
                                    CREATE {normalized_index_type} INDEX {index_name} IF NOT EXISTS
                                    FOR {self._builder.relationship_match(type_=labels_or_type)}
                                    ON (r.{property_name})
                                """,
                                resolve_models=False,
                            )
            case _:
                raise InvalidEntityType(
                    available_types=[option.value for option in EntityType],
                    entity_type=entity_type,
                )

    @ensure_connection
    async def drop_nodes(self) -> None:
        """
        Deletes all nodes and relationships in the database.
        """
        logger.warning("Dropping all nodes")
        results, _ = await self.cypher(
            query="""
                MATCH (n)
                DETACH DELETE n
                RETURN count(n)
            """,
            resolve_models=False,
        )
        logger.info("Dropped %s nodes", results[0][0])

    @ensure_connection
    async def drop_constraints(self) -> None:
        """
        Drops all constraints.
        """
        logger.debug("Discovering constraints")
        results, _ = await self.cypher(query="SHOW CONSTRAINTS", resolve_models=False)

        logger.warning("Dropping all constraints")
        for constraint in results:
            logger.debug("Dropping constraint %s", constraint[1])
            await self.cypher(f"DROP CONSTRAINT {constraint[1]}")
        logger.info("Dropped %s constraints", len(results))

    @ensure_connection
    async def drop_indexes(self) -> None:
        """
        Drops all indexes.
        """
        logger.debug("Discovering indexes")
        results, _ = await self.cypher(query="SHOW INDEXES", resolve_models=False)

        logger.warning("Dropping all indexes")
        count = 0

        for index in results:
            try:
                logger.debug("Dropping index %s", index[1])
                await self.cypher(f"DROP INDEX {index[1]}")
                count += 1
            except DatabaseError as exc:
                logger.warning("Failed to drop index %s: %s", index[1], exc.message)
        logger.info("Dropped %s indexes", count)

    def batch(self) -> "BatchManager":
        """
        Combine multiple transactions into a batch transaction.

        Both client queries using the `.cypher()` method and all model methods called within the
        context of the batch transaction will be combined into a single transaction. If any of the
        queries fail, the entire batch transaction will be rolled back.

        Returns:
            BatchManager: A class for managing batch transaction which must be used with a `with`
                statement.
        """
        return BatchManager(self)

    @ensure_connection
    async def _begin_transaction(self) -> None:
        """
        Begin a new transaction from a session. If no session exists, a new one will be cerated.
        """
        if getattr(self, "_session", None):
            raise TransactionInProgress()

        logger.debug("Beginning new session")
        self._session = cast(AsyncDriver, self._driver).session()
        logger.debug("Session %s created", self._session)

        logger.debug("Beginning new transaction for session %s", self._session)
        self._transaction = await self._session.begin_transaction()
        logger.debug("Transaction %s created", self._transaction)

    @ensure_connection
    async def _commit_transaction(self) -> None:
        """
        Commits the currently active transaction and closes it.
        """
        logger.debug("Committing transaction %s", self._transaction)
        try:
            await cast(AsyncTransaction, self._transaction).commit()  # type: ignore
        finally:
            self._session = None
            self._transaction = None

    @ensure_connection
    async def _rollback_transaction(self) -> None:
        """
        Rolls back the currently active transaction and closes it.
        """
        logger.debug("Rolling back transaction %s", self._transaction)
        try:
            await cast(AsyncTransaction, self._transaction).rollback()  # type: ignore
        finally:
            self._session = None
            self._transaction = None

    def _resolve_database_model(self, query_result: Any) -> Optional[Any]:
        """
        Resolves a query result to the corresponding database model, if one is registered.

        Args:
            query_result (Any): The query result to try to resolve.

        Returns:
            Optional[Any]: The database model, if one is registered. If a path is the result, returns the `Path` class
                with `Path.nodes` and `Path.relationships` resolved to the database models.
        """
        if isinstance(query_result, Path):
            logger.debug("Query result %s is a path, resolving nodes and relationship", query_result)
            nodes = []
            relationships = []

            logger.debug("Resolving nodes")
            for node in query_result.nodes:
                resolved = self._resolve_database_model(node)
                nodes.append(resolved if resolved is not None else node)

            logger.debug("Resolving relationships")
            for relationship in query_result.relationships:
                resolved = self._resolve_database_model(relationship)
                relationships.append(resolved if resolved is not None else relationship)

            setattr(query_result, "_nodes", tuple(nodes))
            setattr(query_result, "_relationships", tuple(relationships))

            return query_result
        elif isinstance(query_result, (Node, Relationship)):
            logger.debug("Query result %s is a node or relationship, resolving", query_result)
            labels = set(query_result.labels) if isinstance(query_result, Node) else {query_result.type}

            for model in list(self.models):
                model_labels: set[str] = set()

                if issubclass(model, NodeModel):
                    model_labels = set(getattr(model.__settings__, "labels"))

                    if labels == model_labels:
                        return model._inflate(cast(Node, query_result))
                elif issubclass(model, RelationshipModel):
                    model_labels = {getattr(model.__settings__, "type")}

                    if labels == model_labels:
                        return model._inflate(cast(Relationship, query_result))

            logger.debug("No registered model found for query result %s", query_result)
            return None

        logger.debug("Query result %s is not a node, relationship, or path, skipping", type(query_result))
        return None

    @property
    def is_connected(self) -> bool:
        """
        Returns whether the client is connected to a database or not.

        Returns:
            bool: Whether the client is connected to a database or not.
        """
        return getattr(self, "_driver", None) is not None


class BatchManager:
    """
    Class for handling batch transactions.
    """

    def __init__(self, client: "Pyneo4jClient") -> None:
        logger.info("Starting batch transaction")
        self._client = client

    async def __aenter__(self) -> None:
        logger.debug("Beginning batch transaction")
        self._client._batch_enabled = True
        await self._client._begin_transaction()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val:
            await self._client._rollback_transaction()
        else:
            await self._client._commit_transaction()

        logger.info("Batch transaction complete")
        self._client._batch_enabled = False
