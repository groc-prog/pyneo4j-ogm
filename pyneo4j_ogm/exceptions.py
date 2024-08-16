"""
Exceptions module for Pyneo4j OGM.
"""

from typing import Any, List


class Pyneo4jException(Exception):
    """
    Base exception for all Pyneo4j exceptions.
    """


class NotConnectedError(Pyneo4jException):
    """
    Raised if a client tries to run a operation while not connected to a database.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            """Client is not connected to a database. Make sure to call `client.connect()` before running any operations
            against the database.""",
            *args,
        )


class InvalidUriError(Pyneo4jException):
    """
    Raised if a invalid or nor URI was provided for the database connection.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Missing or invalid database URI. If you are using ENV variables, check that they are defined correctly.",
            *args,
        )


class InvalidEntityTypeError(Pyneo4jException):
    """
    Raised if a invalid graph entity type was provided.
    """

    def __init__(self, available_types: List[str], entity_type: str, *args: object) -> None:
        super().__init__(
            f"Invalid entity type. Expected entity type to be one of {available_types}, got {entity_type}.",
            *args,
        )


class InvalidRelationshipDirectionError(Pyneo4jException):
    """
    Raised if a invalid relationship direction was provided.
    """

    def __init__(self, direction: str, *args: object) -> None:
        super().__init__(
            f"""Invalid relationship direction {direction} was provided. Expected one of
            'INCOMING', 'OUTGOING' or 'BOTH'.""",
            *args,
        )


class InstanceNotHydratedError(Pyneo4jException):
    """
    Raised if a model was used to run a query, but the instance was not hydrated.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have not been hydrated.", *args)


class InstanceDestroyedError(Pyneo4jException):
    """
    Raised if a model was used to run a query, but the instance was destroyed.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have been destroyed.", *args)


class UnexpectedEmptyResultError(Pyneo4jException):
    """
    Raised if a query should have returned results, but did not. This exception does not include a specific
    reason for why it failed, as it is not possible to determine the reason at the given time.

    If you see this exception in the wild while using this library, i regret to inform you that you are most
    likely at a point where only god can help you. Your best bet is search for similar issues or open a new issue
    at `https://github.com/groc-prog/pyneo4j-ogm/issues/new?template=bug_report.md`. Good luck soldier.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            """The query did not match any results, but should have. This is likely a internal bug. You can open a
            issue at `https://github.com/groc-prog/pyneo4j-ogm/issues/new?template=bug_report.md`.""",
            *args,
        )


class UnregisteredModelError(Pyneo4jException):
    """
    Raised if a model used another node- or relationship model within a query, but the model was not
    registered with the client.
    """

    def __init__(self, model: str, *args: object) -> None:
        super().__init__(
            f"""Model {model} is not registered or is using other unregistered models. Please register all models
            before using them.""",
            *args,
        )


class InvalidTargetNodeModelError(Pyneo4jException):
    """
    Raised if a relationship-property method was called on a node model, but the target node was not of the
    expected model type.
    """

    def __init__(self, expected_type: str, actual_type: str, *args: object) -> None:
        super().__init__(
            f"Expected target node to be instance of subclass of {expected_type}, but got {actual_type}.",
            *args,
        )


class InvalidLabelOrTypeError(Pyneo4jException):
    """
    Raised if a invalid node label or relationship type was provided.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid label or type.", *args)


class TransactionInProgressError(Pyneo4jException):
    """
    Raised if a client tried to start a transaction, but a transaction is already in progress.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("A transaction is already in progress.", *args)


class NotConnectedToSourceNodeError(Pyneo4jException):
    """
    Raised if a relationship-property method was called with a node which is not connected to the source node.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Node not connected to source node.", *args)


class InvalidFiltersError(Pyneo4jException):
    """
    Raised if a method is missing filters or the filters are invalid.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Missing or invalid filters. Maybe you got a typo in the query operators?",
            *args,
        )


class InvalidRelationshipHopsError(Pyneo4jException):
    """
    Raised if a multi-hop relationship query was attempted, but the hops were invalid.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid relationship hop. Hop must be positive integer or '*'.", *args)


class CardinalityViolationError(Pyneo4jException):
    """
    Raised if a query would have violated a cardinality constraint.
    """

    def __init__(
        self, cardinality_type: str, relationship_type: str, start_model: str, end_model: str, *args: object
    ) -> None:
        super().__init__(
            f"""Cardinality {cardinality_type} for relationship {relationship_type} between {start_model} and
            {end_model} is being violated.""",
            *args,
        )


class NoResultFoundError(Pyneo4jException):
    """
    Raised if a query with required filters did not match any results.
    """

    def __init__(self, filters: Any, *args: object) -> None:
        super().__init__(f"No matching results for filter {filters}.", *args)


class InvalidBookmarkError(Pyneo4jException):
    """
    Raised if a bookmark was used to start a transaction, but the bookmark was invalid.
    """

    def __init__(self, bookmarks: Any, *args: object) -> None:
        super().__init__(f"Expected valid bookmarks, but received {bookmarks}.", *args)


class MigrationNotInitializedError(Pyneo4jException):
    """
    Raised if migrations have not been initialized before usage.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Migrations have not been initialized. Run `pyneo4j_ogm init` to initialize them.", *args)


class ListItemNotEncodableError(Pyneo4jException):
    """
    Raised if a list item is not JSON encodable and can thus not be stored.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("List item is not JSON encodable and can not be stored inside the database.", *args)


class Neo4jException(Pyneo4jException):
    """
    Base exception class for any exceptions only raised when using Neo4j as a database.
    """


class Neo4jVersionError(Pyneo4jException):
    """
    Raised if a client tried to connect to a Neo4j database with a unsupported version (Neo4j 5+ is supported).
    """

    def __init__(self, version: str, *args: object) -> None:
        super().__init__(f"Database version {version} is not supported. Only Neo4j 5+ is currently supported.", *args)


class MemgraphException(Pyneo4jException):
    """
    Base exception class for any exceptions only raised when using Memgraph as a database.
    """
