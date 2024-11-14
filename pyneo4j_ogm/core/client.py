"""
Clients module containing abstract base class for all clients and client implementations
for both Neo4j and Memgraph.
"""

from abc import ABC, abstractmethod
from asyncio import iscoroutinefunction
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    LiteralString,
    Optional,
    Self,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession, AsyncTransaction, Query
from neo4j.exceptions import AuthError

from pyneo4j_ogm.core.node import NodeModel
from pyneo4j_ogm.core.relationship import RelationshipModel
from pyneo4j_ogm.exceptions import (
    ClientNotInitializedError,
    ModelResolveError,
    NoTransactionInProgress,
    TransactionInProgress,
)
from pyneo4j_ogm.logger import logger

T = TypeVar("T")


def ensure_initialized(func: Callable) -> Callable:
    """
    Ensures the driver of the client is initialized before interacting with the database.

    Args:
        func (Callable): The function to be decorated, which can be either synchronous
            or asynchronous.

    Raises:
        ClientNotInitializedError: The client is not initialized yet.

    Returns:
        Callable: A wrapped function that includes additional functionality for both
            sync and async functions.
    """

    @wraps(func)
    def sync_wrapper(self, *args, **kwargs) -> None:
        if getattr(self, "_driver", None) is None:
            raise ClientNotInitializedError()

        return func(self, *args, **kwargs)

    @wraps(func)
    async def async_wrapper(self, *args, **kwargs) -> None:
        if getattr(self, "_driver", None) is None:
            raise ClientNotInitializedError()

        return await func(self, *args, **kwargs)

    logger.debug("Ensuring client is initialized")
    if iscoroutinefunction(func):
        return async_wrapper

    return sync_wrapper


class Pyneo4jClient(ABC):
    """
    Base class for all client implementations.

    This client provides all basic functionality which all clients can use. Additionally, it also implements
    a interface for common methods all clients must implement in order to work with models. Methods for
    indexing/constraints are not added since Neo4j/Memgraph have differences in both how they do
    indexing/constraints and the existing types. To reduce complexity, which would be caused by generic methods,
    each client will implement it's own methods, which should follow a common naming scheme.
    """

    _driver: Optional[AsyncDriver]
    _session: Optional[AsyncSession]
    _transaction: Optional[AsyncTransaction]
    _skip_constraint_creation: bool
    _skip_index_creation: bool
    _using_batches: bool

    def __init__(self) -> None:
        super().__init__()

        self._driver = None
        self._session = None
        self._transaction = None
        self._skip_constraint_creation = False
        self._skip_index_creation = False
        self._using_batches = False

    @abstractmethod
    async def register_models(self, models: List[Union[NodeModel, RelationshipModel]]) -> Self:
        pass

    @abstractmethod
    async def register_models_directory(self, path: str) -> Self:
        pass

    @abstractmethod
    async def drop_nodes(self) -> Self:
        pass

    @abstractmethod
    async def drop_constraints(self) -> Self:
        pass

    @abstractmethod
    async def drop_indexes(self) -> Self:
        pass

    @abstractmethod
    async def with_batching(self) -> Iterator[None]:
        pass

    @abstractmethod
    async def _check_database_version(self) -> None:
        pass

    @ensure_initialized
    async def connected(self) -> bool:
        """
        Checks if the client is already connected or not. If the client has been connected, but
        no connection can be established, or the authentication details are invalid, `False` is
        returned.

        Returns:
            bool: `True` if the client is connected and ready, otherwise `False`.
        """
        try:
            logger.info("Checking client connection and authentication")
            if self._driver is None:
                logger.debug("Client not initialized yet")
                return False

            logger.debug("Verifying connectivity to database")
            await self._driver.verify_connectivity()

            logger.debug("Checking database authentication")
            authenticated = await self._driver.verify_authentication()

            if not authenticated:
                raise AuthError()

            return True
        except Exception as exc:
            logger.error(exc)
            return False

    async def connect(
        self,
        uri: str,
        *args,
        skip_constraints: bool = False,
        skip_indexes: bool = False,
        **kwargs,
    ) -> Self:
        """
        Connects to the specified Neo4j/Memgraph database. This method also accepts the same arguments
        as the Neo4j Python driver.

        Args:
            uri (str): The URI to connect to.
            skip_constraints (bool): Whether to skip creating any constraints defined by models. Defaults
                to `False`.
            skip_indexes (bool): Whether to skip creating any indexes defined by models. Defaults to
                `False`.

        Returns:
            Self: The client instance, which allows for chained calls.
        """
        self._skip_constraint_creation = skip_constraints
        self._skip_index_creation = skip_indexes

        logger.info("Connecting to database %s with %s", uri, self)
        self._driver = AsyncGraphDatabase.driver(uri=uri, *args, **kwargs)

        try:
            logger.debug("Checking connectivity and authentication")
            await self._driver.verify_connectivity()
            authenticated = await self._driver.verify_authentication()

            if not authenticated:
                raise AuthError()
        except Exception as exc:
            logger.error(exc)
            await self.close()

        logger.debug("Checking for compatible database version")
        await self._check_database_version()

        logger.info("%s connected to database %s", uri, self)
        return self

    @abstractmethod
    @ensure_initialized
    async def close(self) -> None:
        """
        Closes the connection to the database.
        """
        logger.info("Closing database connection for %s", self)
        await cast(AsyncDriver, self._driver).close()
        self._driver = None
        logger.info("Connection to database for %s closed", self)

    @ensure_initialized
    async def cypher(
        self,
        query: Union[str, LiteralString, Query],
        parameters: Optional[Dict[str, Any]] = None,
        resolve_models: bool = False,
        raise_on_resolve_exc: bool = False,
    ) -> Tuple[List[List[Any]], List[str]]:
        """
        Runs the defined Cypher query with the given parameters. Returned nodes/relationships
        can be resolved to `registered models` by settings the `resolve_models` parameter to `True`.
        By default, the model parsing will not raise an exception if it fails. This can be changed
        with the `raise_on_resolve_exc` parameter.

        Args:
            query (Union[str, LiteralString, Query]): Neo4j Query class or query string. Same as queries
                for the Neo4j driver.
            parameters (Optional[Dict[str, Any]]): Optional parameters used by the query. Same as parameters
                for the Neo4j driver. Defaults to `None`.
            resolve_models (bool): Whether to attempt to resolve the nodes/relationships returned by the query
                to their corresponding models. Models must be registered for this to work. Defaults to `False`.
            raise_on_resolve_exc (bool): Whether to silently fail or raise a `ModelResolveError` error if resolving
                a node/relationship fails. Defaults to `False`.

        Raises:
            ModelResolveError: `raise_on_resolve_exc` is set to `True` and resolving a result fails.

        Returns:
            Tuple[List[List[Any]], List[str]]: A tuple containing the query result and the names of the returned
                variables.
        """
        query_parameters: Dict[str, Any] = {}

        if parameters is not None and isinstance(parameters, dict):
            query_parameters = parameters

        if not self._using_batches:
            # If we are currently using batching, we should already be inside a active session/transaction
            await self._begin_transaction()

        try:
            logger.info("%s with parameters %s", query, query_parameters)
            query_result = await cast(AsyncTransaction, self._transaction).run(
                cast(LiteralString, query), query_parameters
            )

            logger.debug("Parsing query results")
            results = [list(result.values()) async for result in query_result]
            keys = list(query_result.keys())
        except Exception as exc:
            logger.error("Query exception: %s", exc)

            if not self._using_batches:
                # Same as in the beginning, we don't want to roll back anything if we use batching
                await self._rollback_transaction()

        if resolve_models:
            try:
                # TODO: Try to resolve models and raise an exception depending on the parameters provided
                pass
            except Exception as exc:
                logger.warning("Resolving models failed with %s", exc)
                if raise_on_resolve_exc:
                    raise ModelResolveError() from exc

        if not self._using_batches:
            # Again, don't commit anything to the database when batching is enabled
            await self._commit_transaction()

        return results, keys

    @ensure_initialized
    async def _begin_transaction(self) -> None:
        """
        Checks for existing sessions/transactions and begins new ones if none exist.

        Raises:
            TransactionInProgress: A session/transaction is already in progress.
        """
        if self._session is not None or self._transaction is not None:
            raise TransactionInProgress()

        logger.debug("Acquiring new session")
        self._session = cast(AsyncDriver, self._driver).session()
        logger.debug("Session %s acquired", self._session)

        logger.debug("Starting new transaction for session %s", self._session)
        self._transaction = await self._session.begin_transaction()
        logger.debug("Transaction %s for session %s acquired", self._transaction, self._session)

    @ensure_initialized
    async def _commit_transaction(self) -> None:
        """
        Commits the current transaction and closes it.

        Raises:
            NoTransactionInProgress: No active session/transaction to commit.
        """
        if self._session is None or self._transaction is None:
            raise NoTransactionInProgress()

        logger.debug("Committing transaction %s and closing session %s", self._transaction, self._session)
        await self._transaction.commit()
        self._transaction = None
        logger.debug("Transaction committed")

        await self._session.close()
        self._session = None
        logger.debug("Session closed")

    @ensure_initialized
    async def _rollback_transaction(self) -> None:
        """
        Rolls the current transaction back and closes it.

        Raises:
            NoTransactionInProgress: No active session/transaction to roll back.
        """
        if self._session is None or self._transaction is None:
            raise NoTransactionInProgress()

        logger.debug("Rolling back transaction %s and closing session %s", self._transaction, self._session)
        await self._transaction.rollback()
        self._transaction = None
        logger.debug("Transaction rolled back")

        await self._session.close()
        self._session = None
        logger.debug("Session closed")


class Neo4jClient(Pyneo4jClient):
    pass


class MemgraphClient(Pyneo4jClient):
    pass
