"""
Module containing all exceptions raised by the library.
"""


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
        super().__init__("Client is not connected to a database.", *args)


class MissingDatabaseURI(Neo4jOGMException):
    """
    Exception which gets raised if the client is initialized without providing a connection.
    URI
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Trying to initialize client without providing connection URI.", *args)


class InvalidConstraintEntity(Neo4jOGMException):
    """
    Exception which gets raised if the client provides a invalid entity type when creating a new constraint.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid constraint entity type.", *args)


class InflationFailure(Neo4jOGMException):
    """
    Exception which gets raised when the inflation from a Neo4j node to a model instance fails.
    """

    def __init__(self, model: str, *args: object) -> None:
        super().__init__(f"Failed to inflate object to {model} instance.", *args)


class InstanceNotHydrated(Neo4jOGMException):
    """
    Exception which gets raised when a query is run with a instance which has not been hydrated yet.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have not been hydrated.", *args)


class InstanceDestroyed(Neo4jOGMException):
    """
    Exception which gets raised when a query is run with a instance which has been destroyed.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Queries can not be run on instances which have been destroyed.", *args)


class UnexpectedEmptyResult(Neo4jOGMException):
    """
    Exception which gets raised when a query returns no result.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("The query was expected to return a result, but did not.", *args)


class UnknownRelationshipDirection(Neo4jOGMException):
    """
    Exception which gets raised when a invalid relationship direction is provided.
    """

    def __init__(self, expected_directions: list[str], actual_direction: str, *args: object) -> None:
        super().__init__(f"Expected one of {expected_directions}, got {actual_direction}", *args)


class UnregisteredModel(Neo4jOGMException):
    """
    Exception which gets raised when a model, which has not been registered, gets used.
    """

    def __init__(self, unregistered_model: str, *args: object) -> None:
        super().__init__(f"Model {unregistered_model} was not registered, but another model is using it.", *args)


class InvalidTargetModel(Neo4jOGMException):
    """
    Exception which gets raised when a relationship property defines a invalid target model.
    """

    def __init__(self, target_model: str, *args: object) -> None:
        super().__init__(f"Expected target model to be string or Neo4jNode, but got {type(target_model)}.", *args)


class InvalidRelationshipModelOrType(Neo4jOGMException):
    """
    Exception which gets raised when a relationship property defines a invalid model or type.
    """

    def __init__(self, relationship_or_type: str, *args: object) -> None:
        super().__init__(
            f"""
                Expected relationship model or type to be string or Neo4jRelationship, but got
                {type(relationship_or_type)}.
            """,
            *args,
        )
