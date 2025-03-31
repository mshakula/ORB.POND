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
    Asynchronous entry point for the ORB.POND. game.
    """

    # This is the top-level function, so set the default event loop for this thread
    # to be the running loop.
    asyncio.set_event_loop(asyncio.get_running_loop())

    from .game import MainMenu
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(MainMenu(event_manager).run())
    except asyncio.CancelledError:
        pass
    except BaseException as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
    finally:
        logging.getLogger().info("Shutting down event manager")
        event_manager.shutdown()
        logging.getLogger().info("Exiting game_thread")


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
                assert not em._running
            except KeyboardInterrupt:
                logging.getLogger().warning("Keyboard interrupt!")
            finally:
                # Canceling the task has to be done from its own event loop
                logging.getLogger().info(f"Waiting for {game_thread.name} to finish")
                game_loop.call_soon_threadsafe(game_task.cancel)
                game_thread.join()

    except KeyboardInterrupt:
        logging.getLogger().warning("Keyboard interrupt!")
    except BaseException as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
        sys.exit(1)
    finally:
        logging.getLogger().info("Exit")
        sys.exit(0)


if __name__ == "__main__":
    main()
