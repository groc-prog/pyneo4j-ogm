"""
Exceptions raised by different methods.
"""


class Pyneo4jError(Exception):
    """
    Base exception for all Pyneo4j exceptions.
    """


class NoClientFoundError(Pyneo4jError):
    """
    No active client is available for the query to use.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("No active client found", *args)


class InvalidClientError(Pyneo4jError):
    """
    Invalid client was provided.
    """

    def __init__(self, *args: object) -> None:
        super().__init__("Client must be a registered instance of `Pyneo4jClient`", *args)
