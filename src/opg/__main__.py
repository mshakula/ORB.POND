"""
Entry point for the ORB.POND game.
"""

import threading
import sys
import logging
import argparse
import asyncio

from typing import *

from . import logging_config
from .util import capture_stdout


async def _main(event_manager: "EventManager") -> None:
    """
    Asynchronous entry point for ORB.POND.GAME.
    """

    # This is the top-level function, so set the default event loop for this thread
    # to be the running loop.
    asyncio.set_event_loop(asyncio.get_running_loop())

    import pygame

    logging.getLogger().info("Starting ORB.POND.GAME")

    # Set up the display
    async def create_display() -> pygame.Surface:
        disp = pygame.display.set_mode(
            size=(800, 600),
            flags=pygame.SCALED | pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.RESIZABLE,
            depth=0,
            display=0,
            vsync=1)
        pygame.display.set_caption('ORB.POND.GAME')
        logging.getLogger().debug("DISPLAY CREATED")
        return disp

    try:
        logging.getLogger().debug("ARRANGING DISPLAY")
        display = await event_manager.call(create_display)

        async with event_manager.get_subscription().subscribe(pygame.QUIT) as sub:
            await sub.get()
            logging.getLogger().info("QUIT event received")

    except asyncio.CancelledError:
        logging.getLogger().info("Cancelled")
    except BaseException as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
    finally:
        logging.getLogger().info("Shutting down ORB.POND.GAME")
        event_manager.shutdown()


def main() -> None:
    """
    Entry point for the ORB.POND game.
    """

    try:
        try:
            parser = argparse.ArgumentParser(description=__doc__)
            logging_config.set_argparse_common_log_options(parser)
            args = parser.parse_args()
            logging_config.common_logger_config_args(args)
        except Exception as e:
            raise RuntimeError("Failed to configure logging") from e

        with capture_stdout() as f:
            import pygame

            f.seek(0)
            for line in f.read().decode().strip().split("\n"):
                logging.getLogger().info(line)

        # Create the event manager
        from .event_manager import EventManager
        event_manager = EventManager()
        logging.getLogger().info("Initialized event manager")

        # Spawn an asyncio thread for actual game logic, and run event loop
        # in main thread.
        with event_manager as em:
            logging.getLogger().info("Started event manager")
            game_loop = asyncio.new_event_loop()
            game_task = game_loop.create_task(_main(em), name="_main")
            game_thread = threading.Thread(
                target=game_loop.run_until_complete,
                args=[game_task],
                name="game_thread")
            try:
                game_thread.start()
                em.process_events()
            except KeyboardInterrupt:
                logging.getLogger().warning("Keyboard interrupt!")
            finally:
                # Canceling the task has to be done from its own event loop
                game_loop.call_soon_threadsafe(game_task.cancel)
                logging.getLogger().info(f"Waiting for {game_thread.name} to finish.")
                game_thread.join()

    except KeyboardInterrupt:
        logging.getLogger().warning("Keyboard interrupt!")
    except BaseException as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
        sys.exit(1)
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
