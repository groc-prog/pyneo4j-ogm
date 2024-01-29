"""
Pyneo4j exceptions raised by the client or model classes.
"""
from typing import Any, List


class Pyneo4jException(Exception):
    """
    Base exception for all Pyneo4j exceptions
    """


class NotConnectedToDatabase(Pyneo4jException):
    """
    A client tried to run a query without being connected to a database.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Client is not connected to a database", *args)


class UnsupportedNeo4jVersion(Pyneo4jException):
    """
    A client tried to connect to a Neo4j database with a unsupported version (Neo4j 5+ is supported).
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Only Neo4j 5+ is supported.", *args)


class MissingDatabaseURI(Pyneo4jException):
    """
    A client tried to initialize without providing a connection URI.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Trying to initialize client without providing connection URI", *args)


class InvalidEntityType(Pyneo4jException):
    """
    A invalid graph entity type was provided.
    """

    def __init__(self, available_types: List[str], entity_type: str, *args: object) -> None:
        super().__init__(
            f"Invalid entity type. Expected entity type to be one of {available_types}, got {entity_type}",
            *args,
        )


class InvalidRelationshipDirection(Pyneo4jException):
    """
    A invalid relationship direction was provided.
    """

    def __init__(self, direction: str, *args: object) -> None:
        super().__init__(
            f"""Invalid relationship direction {direction} was provided. Expected one of
            'INCOMING', 'OUTGOING' or 'BOTH'""",
            *args,
        )


class InstanceNotHydrated(Pyneo4jException):
    """
    A model was used to run a query, but the instance was not hydrated.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have not been hydrated", *args)


class InstanceDestroyed(Pyneo4jException):
    """
    A model was used to run a query, but the instance was destroyed.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have been destroyed", *args)


class UnexpectedEmptyResult(Pyneo4jException):
    """
    A query should have returned results, but did not. This exception does not include a specific
    reason for why it failed, as it is not possible to determine the reason.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("The query did not match any results.", *args)


class UnregisteredModel(Pyneo4jException):
    """
    A model used another node- or relationship model within a query, but the model was not
    registered with the client.
    """

    def __init__(self, model: str, *args: object) -> None:
        super().__init__(
            f"""Model {model} is not registered or is using other unregistered models. Please register all models
            before using them.""",
            *args,
        )


class InvalidTargetNode(Pyneo4jException):
    """
    A relationship-property method was called on a node model, but the target node was not of the
    expected model type.
    """

    def __init__(self, expected_type: str, actual_type: str, *args: object) -> None:
        super().__init__(
            f"Expected target node to be instance of subclass of {expected_type}, but got {actual_type}",
            *args,
        )


class InvalidLabelOrType(Pyneo4jException):
    """
    Invalid node label or relationship type was provided.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid label or type", *args)


class TransactionInProgress(Pyneo4jException):
    """
    A client tried to start a transaction, but a transaction is already in progress.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("A transaction is already in progress.", *args)


class NotConnectedToSourceNode(Pyneo4jException):
    """
    A relationship-property method was called with a node which is not connected to the source node.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Node not connected to source node.", *args)


class InvalidFilters(Pyneo4jException):
    """
    The method is missing filters or the filters are invalid.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Missing or invalid filters. Maybe you got a typo in the query operators?",
            *args,
        )


class InvalidRelationshipHops(Pyneo4jException):
    """
    A multi-hop relationship query was attempted, but the hops were invalid.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid relationship hop. Hop must be positive integer or '*'.", *args)


class CardinalityViolation(Pyneo4jException):
    """
    A query would have violated a cardinality constraint.
    """

    def __init__(
        self, cardinality_type: str, relationship_type: str, start_model: str, end_model: str, *args: object
    ) -> None:
        super().__init__(
            f"""Cardinality {cardinality_type} for relationship {relationship_type} between {start_model} and
            {end_model} is being violated.""",
            *args,
        )


class NoResultFound(Pyneo4jException):
    """
    A query with required filters did not match any results.
    """

    def __init__(self, filters: Any, *args: object) -> None:
        super().__init__(f"No matching results for filter {filters}", *args)


class InvalidBookmark(Pyneo4jException):
    """
    A bookmark was used to start a transaction, but the bookmark was invalid.
    """

    def __init__(self, bookmarks: Any, *args: object) -> None:
        super().__init__(f"Expected valid bookmarks, but received {bookmarks}", *args)


class MigrationNotInitialized(Pyneo4jException):
    """
    Migrations have not been initialized before usage.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Migrations have not been initialized. Run `pyneo4j_ogm init` to initialize them", *args)


class ListItemNotEncodable(Pyneo4jException):
    """
    A list item is not JSON encodable and can thus not be stored.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("List item is not JSON encodable and can not be stored inside the database", *args)
