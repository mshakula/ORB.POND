"""A global event manager for various state events.
"""

import asyncio
import queue
import pygame.event
import logging
import threading
import concurrent.futures


class EventManager:
    """A global event manager for various state events.

    Maintains a separate thread for processing pygame events.
    This approach is prefereable to having the main thread maintain the event loop,
    for more straightforward programming of other elements.
    """

    LOGGER = logging.getLogger(__name__)

    def __init__(self):
        self.event_queue = queue.Queue()
        self.thread = threading.Thread(target=self._init)
        self.thread.start()

    def __del__(self):
        self.runtask.cancel()
        self.executor.shutdown()

    def _init(self):
        print("ASDKJLKJLKF")
        if pygame.display.get_init():
            raise RuntimeError("pygame display system already initialized")
        self.LOGGER.debug(
            f"Initializing pygame display system in thread {threading.current_thread()}"
        )
        pygame.display.init()

    def _process_events(self):
        """Coroutine to process events from various sources.
        """
        try:
            self._init()
            self._process_pygame_events()
        except asyncio.CancelledError:
            self.LOGGER.info("Task cancelled")
        except Exception as e:
            self.LOGGER.error("Error processing events", exc_info=e)
            raise

    def _process_pygame_events(self):
        """Process pygame events and put them in the event queue.

        Run in a separate thread, since pygame.event.wait() is blocking.
        """
        while True:
            event = pygame.event.wait()
            self.LOGGER.debug(f"Received event: {event}")
            self.event_queue.put(event)

    def get(self):
        """Get the next event from the event queue.
        """
        while not self.event_queue.empty():
            yield self.event_queue.get()
