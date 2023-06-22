"""
Database client for running queries against the connected database.
"""
import logging
from os import environ
from typing import Any, Callable, LiteralString, TypedDict

from neo4j import AsyncDriver, AsyncGraphDatabase

from neo4j_ogm.core.exceptions import MissingDatabaseURI, NotConnectedToDatabase


class BatchTransaction(TypedDict):
    """
    Dictionary type definition for a batched transaction
    """

    query: LiteralString
    parameters: dict[str, Any] | None


def ensure_connection(func: Callable):
    """
    Decorator which ensures that a connection to a database has been established before running
    any operations on it.
    """

    async def decorator(self: "Neo4jClient", *args, **kwargs):
        if getattr(self, "_driver", None) is None:
            raise NotConnectedToDatabase()

        result = await func(self, *args, **kwargs)
        return result

    return decorator


class Neo4jClient:
    """
    Singleton database client class used to run different operations on the database
    """

    _instance: "Neo4jClient"
    _driver: AsyncDriver
    uri: str
    auth: tuple[str, str] | None

    def __new__(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, uri: str | None = None, auth: tuple[str, str] | None = None) -> None:
        db_uri = uri if uri is not None else environ.get("NEO4J_URI", None)

        if db_uri is None:
            raise MissingDatabaseURI()

        self.uri = db_uri
        self.auth = auth

        self.connect()

    def connect(self):
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
        logging.debug("Connecting to database %s", self.uri)
        self._driver = AsyncGraphDatabase.driver(uri=self.uri, auth=self.auth)
        logging.debug("Connected to database")

    @ensure_connection
    async def close(self):
        """
        Closes the current connection to the client
        """
        logging.debug("Closing connection to database")
        await self._driver.close()
        logging.debug("Connection to database closed")

    @ensure_connection
    async def cypher(
        self, query: LiteralString, parameters: dict[str, Any] | None = None
    ) -> tuple[list[list[Any]], list[str]]:
        """
        Runs the provided cypher query with given parameters against the database.

        Args:
            query (LiteralString): Query to run
            parameters (dict[str, Any]): Parameters passed to the transaction

        Returns:
            tuple[list[list[Any]], list[str]]: A tuple containing the query result and the names
            of the returned variables
        """
        if parameters is None:
            parameters = {}

        async with self._driver.session() as session:
            parameters = parameters if parameters is not None else {}

            logging.debug("Running query %s with parameters %s", query, parameters)
            result_data = await session.run(query=query, parameters=parameters)

            results = [list(r.values()) async for r in result_data]
            meta = list(result_data.keys())

        logging.debug("Query completed")
        return results, meta

    @ensure_connection
    async def batch(
        self, transactions: list[BatchTransaction]
    ) -> list[tuple[list[list[Any]], list[str]]]:
        """
        Run a batch query.

        Args:
            transactions (list[BatchTransaction]): A list of queries with their parameters

        Raises:
            exc: A exception if the batch query fails

        Returns:
            list[tuple[list[list[Any]], list[str]]]: A list of results. The results are in the same
            order as the queries where defined in
        """
        async with self._driver.session() as session:
            tx = await session.begin_transaction()

            try:
                logging.debug("Starting batch query")
                query_results: list[tuple[list[list[Any]], list[str]]] = []

                for transaction in transactions:
                    parameters = (
                        transaction["parameters"]
                        if "parameters" in transaction and transaction["parameters"] is not None
                        else {}
                    )

                    logging.debug(
                        "Running query %s with parameters %s", transaction["query"], parameters
                    )
                    result_data = await tx.run(transaction["query"], parameters=parameters)

                    results = [list(r.values()) async for r in result_data]
                    meta = list(result_data.keys())

                    query_results.append((results, meta))

                logging.debug("Committing transactions")
                await tx.commit()
            except Exception as exc:
                tx.cancel()
                raise exc
            finally:
                logging.debug("Closing transaction")
                await tx.close()

        logging.debug("Batch query completed")
        return query_results

    @ensure_connection
    async def drop_nodes(self):
        """
        Deletes all nodes in the database
        """
        logging.debug("Deleting all nodes in database")
        await self.cypher("MATCH (node) DETACH DELETE node")
