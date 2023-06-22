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
