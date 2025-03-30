"""A global manager for various state events.
"""

# Better typechecking
from __future__ import annotations

import asyncio
import queue
import pygame.event
import logging
import threading
import concurrent.futures
import functools
import signal

from typing import *

from .util import suppress_stdout


class EventSubscription:
    """A subscription to a set of specific event types.
    """

    def __init__(self, event_manager: EventManager) -> None:
        """Create a new event subscription.

        :param event_manager: The event manager to subscribe to.
        """
        self._event_manager = event_manager

        raise NotImplementedError()

    def __enter__(self) -> EventSubscription:
        """Enter the context manager, activating the subscription.
        """

        raise NotImplementedError()

    def __exit__(self, exc_type: type, exc_value: Any, traceback: Any) -> None:
        """Exit the context manager, deactivating the subscription.
        """

        raise NotImplementedError()

    def subscribe(self, event_list: Iterable[int]) -> EventSubscription:
        """Subscribe to a specific event type.
        """

        raise NotImplementedError()

        return self

    def unsubscribe(self, event_list: Iterable[int]) -> EventSubscription:
        """Unsubscribe from a specific event type.
        """

        raise NotImplementedError()

        return self

    async def get(self) -> pygame.event.Event:
        """Get the next subscribed event.
        """

        raise NotImplementedError()


class EventManager:
    """A global event manager for various state events.

    Runs in the main thread as pygame event processing only works from the main thread
    From the docs: "This function [pygame.event.wait()]` should only be called in the
    thread that initialized pygame.display". Because of MacOS Cocoa event handling, the
    only thread that is allowed to handle UI events is the main thread, and others end
    in a crash.

    We will use the pygame event queue to process all game events, since it is simple,
    robust, and allows for custom events. This limits the need for a more complex event
    system.

    This class offers an asyncio interface for processes in other threads to get events
    from the main thread.
    - https://docs.python.org/3/library/asyncio-dev.html#asyncio-multithreading
    - https://stackoverflow.com/questions/54096301/can-concurrent-futures-future-be-converted-to-asyncio-future
    - https://stackoverflow.com/questions/49005651/how-does-asyncio-actually-work
    - https://stackoverflow.com/questions/28866651/python-concurrent-futures-using-subprocess-with-a-callback
    """

    def __init__(self):
        self._LOGGER = logging.getLogger(__name__ + f".EventManager({id(self)})")
        self._thread = threading.current_thread()

        self.running = False

        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("EventManager must be created in the main thread.")

        if pygame.display.get_init():
            raise RuntimeError(
                "EventManager must be created before pygame.display.init()")

        pygame.display.init()

    def __enter__(self) -> EventManager:

        if threading.current_thread() is not self._thread:
            raise RuntimeError(
                "EventManager can only be entered in the thread it was created in.")

        self.running = True

        return self

    def __exit__(self, exc_type: type, exc_value: Any, traceback: Any) -> None:

        assert threading.current_thread() is self._thread()

        self._LOGGER.debug("__exit__")

        if self.running:
            self._LOGGER.warning(
                "EventManager exited without being explicitly shutdown.")

        self._LOGGER.info("Shutting down.")

        pygame.display.quit()

        raise NotImplementedError(
            "Notify subscribers of shutdown, and do other cleanup")

    def process_events(self) -> None:
        """Process all events in the pygame event queue.

        Must be run in the main thread.
        """

        if threading.current_thread() is not self._thread:
            raise RuntimeError(
                "EventManager.process_events() must be called in the thread it was created in.")

        while self.running:
            event = pygame.event.wait()
            raise NotImplementedError("Notify subscribers of event")

    def shutdown(self) -> None:

        self.running = False

    def get_subscription(self) -> EventSubscription:

        return EventSubscription(self)

    def post(self, event: pygame.event.Event) -> None:
        """Post an event to the pygame event queue.
        """

        raise NotImplementedError()
