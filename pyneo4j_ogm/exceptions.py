"""
Neo4jOGM exceptions raised by the client or the models.
"""
from typing import List


class Neo4jOGMException(Exception):
    """
    Base exception for all Neo4jOGM exceptions
    """


class NotConnectedToDatabase(Neo4jOGMException):
    """
    Exception which gets raised if the client tries to operate on a database without a valid.
    connection.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Client is not connected to a database", *args)


class UnsupportedNeo4jVersion(Neo4jOGMException):
    """
    Exception which gets raised if the client tries to connect to a Neo4j database with an unsupported version.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Only Neo4j 5+ is supported.", *args)


class MissingDatabaseURI(Neo4jOGMException):
    """
    Exception which gets raised if the client is initialized without providing a connection.
    URI
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Trying to initialize client without providing connection URI", *args)


class InvalidEntityType(Neo4jOGMException):
    """
    Exception which gets raised if the client provides a invalid entity type
    """

    def __init__(self, available_types: List[str], entity_type: str, *args: object) -> None:
        super().__init__(
            f"Invalid entity type. Expected entity type to be one of {available_types}, got {entity_type}",
            *args,
        )


class InvalidIndexType(Neo4jOGMException):
    """
    Exception which gets raised if the client provides a invalid index type when creating a new
    index.
    """

    def __init__(self, available_types: List[str], index_type: str, *args: object) -> None:
        super().__init__(
            f"Invalid index type. Expected index to be one of {available_types}, got {index_type}",
            *args,
        )


class InvalidRelationshipDirection(Neo4jOGMException):
    """
    Exception which gets raised if a invalid relationship direction is provided.
    """

    def __init__(self, direction: str, *args: object) -> None:
        super().__init__(
            f"""Invalid relationship direction {direction} was provided. Expected one of
            'INCOMING', 'OUTGOING' or 'BOTH'""",
            *args,
        )


class InstanceNotHydrated(Neo4jOGMException):
    """
    Exception which gets raised when a query is run with a instance which has not been hydrated yet.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have not been hydrated", *args)


class InstanceDestroyed(Neo4jOGMException):
    """
    Exception which gets raised when a query is run with a instance which has been destroyed.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have been destroyed", *args)


class NoResultsFound(Neo4jOGMException):
    """
    Exception which gets raised when a query returns no result.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("The query did not match any results.", *args)


class UnregisteredModel(Neo4jOGMException):
    """
    Exception which gets raised when a model, which has not been registered, gets used.
    """

    def __init__(self, model: str, *args: object) -> None:
        super().__init__(
            f"""Model {model} is not registered or is using other unregistered models. Please register all models
            before using them.""",
            *args,
        )


class InvalidTargetNode(Neo4jOGMException):
    """
    Exception which gets raised when a relationship property receives a target node of the wrong
    model type.
    """

    def __init__(self, expected_type: str, actual_type: str, *args: object) -> None:
        super().__init__(
            f"Expected target node to be of type {expected_type}, but got {actual_type}",
            *args,
        )


class InvalidLabelOrType(Neo4jOGMException):
    """
    Exception which gets raised when invalid labels or a invalid type are passed to a method.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid label or type", *args)


class TransactionInProgress(Neo4jOGMException):
    """
    Exception which gets raised when a transaction is in progress, but another one is started.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("A transaction is already in progress.", *args)


class NotConnectedToSourceNode(Neo4jOGMException):
    """
    Exception which gets raised when a node is to be replaced by another, but the node is not
    connected to the source node.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Node not connected to source node.", *args)


class MissingFilters(Neo4jOGMException):
    """
    Exception which gets raised when a filter is required, but none or a invalid one is provided.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(
            "Missing or invalid filters. Maybe you got a typo in the query operators?",
            *args,
        )


class ModelImportFailure(Neo4jOGMException):
    """
    Exception which gets raised when a model dict is imported, but does not have a element_id or id key.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Missing 'element_id' or 'id' key in model dict.", *args)


class InvalidRelationshipHops(Neo4jOGMException):
    """
    Exception which gets raised when a relationship hop is invalid.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid relationship hop. Hop must be positive integer or '*'.", *args)


class CardinalityViolation(Neo4jOGMException):
    """
    Exception which gets raised when defined cardinality is violated.
    """

    def __init__(
        self, cardinality_type: str, relationship_type: str, start_model: str, end_model: str, *args: object
    ) -> None:
        super().__init__(
            f"""Cardinality {cardinality_type} for relationship {relationship_type} between {start_model} and
            {end_model} is being violated.""",
            *args,
        )
