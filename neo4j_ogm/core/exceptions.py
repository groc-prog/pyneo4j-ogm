"""
Module containing all exceptions raised by the library.
"""


class Neo4jOGMException(Exception):
    """
    Base exception for all Neo4jOGM exceptions
    """


class NotConnectedToDatabase(Neo4jOGMException):
    """
    Exception which gets raised if the client tries to operate on a database without a valid
    connection.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Client is not connected to a database.", *args)


class MissingDatabaseURI(Neo4jOGMException):
    """
    Exception which gets raised if the client is initialized without providing a connection
    URI
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Trying to initialize client without providing connection URI.", *args)


class InvalidConstraintEntity(Neo4jOGMException):
    """
    Exception which gets raised if the client provides a invalid entity type when creating a new constraint
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Invalid constraint entity type.", *args)


class DeflationFailure(Neo4jOGMException):
    """
    Exception which gets raised when the deflation from a model instance to a Neo4j-compatible dictionary fails
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Failed to deflate model instance to dictionary.", *args)
