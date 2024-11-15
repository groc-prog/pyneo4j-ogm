"""
Registry module managing client/model registration. Active clients used by models to run queries
will be handled by this class.
"""

import threading
from contextlib import contextmanager
from typing import Iterator, List, Optional, Set, cast

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.exceptions import InvalidClientError
from pyneo4j_ogm.logger import logger


class Registry:
    """
    Thread-safe singleton client registry. All used clients have to be registered with this registry to
    be injected/used in models. When using multi-threading, each thread will have it's own registry and
    will need to register it's own clients.
    """

    _thread_ctx = threading.local()

    def __new__(cls):
        if not hasattr(cls._thread_ctx, "instance"):
            instance = super(Registry, cls).__new__(cls)

            setattr(instance._thread_ctx, "clients", set())
            setattr(instance._thread_ctx, "active_client", None)
            setattr(cls._thread_ctx, "instance", instance)

        return cast(Registry, getattr(cls._thread_ctx, "instance"))

    @property
    def active_client(self) -> Optional[Pyneo4jClient]:
        """
        Gets the currently active client. Each thread has it's own active client and registry.

        Returns:
            Optional[Pyneo4jClient]: Either the currently active client or `None` if no clients are available.
        """
        return getattr(self._thread_ctx, "active_client", None)

    def register(self, clients: List[Pyneo4jClient]) -> None:
        """
        Registers multiple clients with the registry. Only registered clients will be injected into a model
        instance/method to run queries.

        Args:
            client (List[Pyneo4jClient]): The list of clients to register.
        """
        logger.debug("Registering %s clients with registry", len(clients))
        registered_clients = cast(Set[Pyneo4jClient], getattr(self._thread_ctx, "clients", set()))

        # Also track the available clients, so in case there are multiple we can set the first one
        # as the active one automatically
        available_clients: List[Pyneo4jClient] = []

        for client in clients:
            if not isinstance(client, Pyneo4jClient):
                continue

            logger.debug("Registering client %s", client)
            registered_clients.add(client)
            available_clients.append(client)

        if getattr(self._thread_ctx, "active_client", None) is None and len(registered_clients) > 0:
            if len(registered_clients) > 1:
                logger.info("Multiple clients registered at once, setting first client as active")

            setattr(self._thread_ctx, "active_client", next(iter(available_clients)))

    def deregister(self, client: Pyneo4jClient) -> None:
        """
        De-registers a previously registered client. If the provided client is the active client,
        a new client will be set as the active one. If no more clients are registered, the active
        client will be set to `None`.

        Args:
            client (Pyneo4jClient): The client to de-register.
        """
        registered_clients = cast(Set[Pyneo4jClient], getattr(self._thread_ctx, "clients", set()))
        if client not in registered_clients:
            logger.debug("Client is not registered, skipping")
            return

        logger.debug("De-registering client %s", client)
        registered_clients.remove(client)

        # TODO: Maybe we want to raise an exception here instead so we don't get some **magic** behavior
        # if someone de-registers the currently active client
        if self.active_client == client:
            logger.debug("Active client de-registered, switching active client")

            if len(registered_clients) > 0:
                logger.debug("Other available client found")
                setattr(self._thread_ctx, "active_client", next(iter(registered_clients)))
            else:
                logger.debug("No other registered clients found")
                setattr(self._thread_ctx, "active_client", None)

    def set_active_client(self, client: Optional[Pyneo4jClient]) -> None:
        """
        Updates the active client.

        Args:
            client (Optional[Pyneo4jClient]): The client to set as active or `None`.

        Raises:
            InvalidClientError: If `client` is not an instance of `Pyneo4jClient` or not registered
                yet.
        """
        if client is not None and (
            not isinstance(client, Pyneo4jClient)
            or client not in cast(Set[Pyneo4jClient], getattr(self._thread_ctx, "clients", set()))
        ):
            raise InvalidClientError()

        setattr(self._thread_ctx, "active_client", client)


@contextmanager
def with_client(client: Pyneo4jClient) -> Iterator[Pyneo4jClient]:
    """
    Temporarily sets the specified client as the active client within a context.

    This context manager sets the provided `client` as the active client for the
    current thread, allowing operations to use this client within the scope of the
    `with` block. When the context exits, the active client is reverted to its
    previous value.

    The provided client must be registered prior to using it, otherwise a `InvalidClientError`
    is raised.

    Args:
        client (Pyneo4jClient): The client instance to set as active within the context.

    Yields:
        Pyneo4jClient: The active client set for the context.

    Example:
        ```python
        client_one = Pyneo4jClient() # Currently active
        client_two = Pyneo4jClient()

        with with_client(client_two) as client:
            # Within this block, the active client is `client_two`.
            pass

        # Outside the block, the active client is reverted back to `client_one`.
        ```
    """
    registry = Registry()

    original_client = registry.active_client
    registry.set_active_client(client)

    try:
        logger.info("Entering context with scoped client %s", client)
        yield cast(Pyneo4jClient, registry.active_client)
    finally:
        registry.set_active_client(original_client)