"""A global manager for various state events.
"""

# Better typechecking
from __future__ import annotations

import asyncio
import queue
import pygame.event
import logging
import threading
import functools
import janus

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
        self._active = False
        self._event_list = set()

    async def __aenter__(self) -> EventSubscription:
        """Activate the subscription.
        """

        with self._event_manager._subscriptions_lock:
            self._event_manager._subscriptions[self] = janus.Queue()
            self._active = True
        return self

    async def __aexit__(self, exc_type: type, exc_value: Any, traceback: Any) -> None:
        """Deactivate the subscription.
        """

        with self._event_manager._subscriptions_lock:
            x = self._event_manager._subscriptions[self]
            del self._event_manager._subscriptions[self]
            self._active = False
        await x.aclose()

    def __iter__(self) -> Iterable[int]:
        return iter(self._event_list)

    def subscribe(self, *event_list) -> EventSubscription:
        """Subscribe to a specific event type.
        """

        if self._active:
            with self._event_manager._subscriptions_lock:
                self._event_list.update(event_list)
        else:
            self._event_list.update(event_list)
        return self

    def unsubscribe(self, *event_list) -> EventSubscription:
        """Unsubscribe from a specific event type.
        """

        if self._active:
            with self._event_manager._subscriptions_lock:
                self._event_list.difference_update(event_list)
        else:
            self._event_list.difference_update(event_list)
        return self

    async def get(self) -> pygame.event.Event:
        """Get the next subscribed event.
        """

        if not self._active:
            raise RuntimeError("Cannot get events from an inactive subscription.")

        return await self._event_manager._subscriptions[self].async_q.get()


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

    def __init__(self, timeout_ms: float = 100) -> None:
        """Create a new event manager. Does not enable it or start the event loop.
        """

        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("EventManager must be created in the main thread.")

        if timeout_ms <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self._LOGGER = logging.getLogger(
            f"{self.__class__.__qualname__}#{id(self)}")
        self._thread = threading.current_thread()
        self._loop = None
        self._running = False
        self._timeout_ms = timeout_ms
        self._subscriptions: Mapping[EventSubscription: queue.Queue] = {}
        self._subscriptions_lock = threading.Lock()

    def __enter__(self) -> EventManager:

        if threading.current_thread() is not self._thread:
            raise RuntimeError(
                "EventManager can only be entered in the thread it was created in.")

        if pygame.display.get_init():
            raise RuntimeError(
                "EventManager.__enter__ must be allowed to call pygame.display.init()")
        else:
            pygame.display.init()
            self._LOGGER.debug(
                f"Initialized pygame display with {
                    pygame.display.get_driver()} driver")

        self._loop = asyncio.new_event_loop()

        return self

    def __exit__(self, exc_type: type, exc_value: Any, traceback: Any) -> None:

        assert threading.current_thread() is self._thread
        assert not self._loop.is_running()
        assert not self._running

        self._loop.close()
        self._loop = None

        pygame.display.quit()

    def process_events(self) -> None:
        """Process all events in the pygame event queue.

        This function creates an asyncio event loop, and schedules a task to process
        events from the pygame event queue. Running in an event loop allows other
        threads to schedule tasks that need to be run in the main thread, such as
        operations involving window setup.

        We have to do this timeout-based event loop because pygame.event.wait() is a
        blocking call, and in python signals get processed not at the C level, but at
        a level higher than that, meaning we have to wait until blocking calls complete.
        See more: https://stackoverflow.com/a/25677040

        TODO: maybe we can rip out the asyncio event loop, and create a custom pygame
        event that can be used to request the main thread to do something. The current
        approach is nice enough though because we get the asyncio scheduler.

        Must be run in the main thread.
        """

        if threading.current_thread() is not self._thread:
            raise RuntimeError(
                "EventManager.process_events() must be called in the thread it was created in.")

        assert self._loop is not None

        async def _process_events():
            try:
                self._running = True
                while self._running:
                    event = pygame.event.wait(self._timeout_ms)
                    if event.type != pygame.NOEVENT:
                        with self._subscriptions_lock:
                            for subscription, queue in self._subscriptions.items():
                                if event.type in subscription:
                                    self._LOGGER.debug(
                                        f"Sending event: {event} to {subscription}")
                                    queue.sync_q.put(event)
                    else:
                        pass
                    await asyncio.sleep(0)  # Yield to other tasks
            finally:
                self._running = False

        self._loop.run_until_complete(_process_events())

    def call(self, callback: Any, *args: Any, **kwargs: Any) -> asyncio.Future:
        """Arrange for a callback to be called in the main thread.

        There isn't an actual magic in the wrap_future() function:
        - https://stackoverflow.com/a/49351069

        :param callback: The callback to be called, either a function or a coroutine.
        :param args: The arguments to pass to the callback.
        :param kwargs: The keyword arguments to pass to the callback.
        """

        if self._loop is None:
            raise RuntimeError("EventManager must be entered to arrange callbacks.")

        if asyncio.get_running_loop() is None:
            raise RuntimeError(
                "EventManager.arrange_callback() must be called from an asyncio coroutine.")

        @functools.wraps(callback)
        async def _callback_wrapper(callback, *args, **kwargs):
            if asyncio.iscoroutinefunction(callback):
                return await callback(*args, **kwargs)
            return callback(*args, **kwargs)

        return asyncio.wrap_future(asyncio.run_coroutine_threadsafe(
            _callback_wrapper(callback, *args, **kwargs), self._loop))

    def shutdown(self) -> None:
        if self._loop is not None:
            self._running = False
        else:
            self._LOGGER.warning("shutdown() called while not entered.")

    def get_subscription(self, *events) -> EventSubscription:
        return EventSubscription(self).subscribe(*events)

    def post(self, event: pygame.event.Event) -> None:
        """Post an event to the pygame event queue.
        """

        raise NotImplementedError()
