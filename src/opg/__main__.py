"""
Entry point for the ORB.POND game.
"""

import threading
import os
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

    import pygame

    logging.getLogger().info("Starting ORB.POND.GAME")
    try:
        # Set up the display
        screen: pygame.Surface = pygame.display.set_mode(
            size=(800, 600),
            flags=pygame.SCALED | pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.RESIZABLE,
            depth=0,
            display=0,
            vsync=1
        )
        pygame.display.set_caption('ORB.POND.GAME')
        await asyncio.sleep(10)
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
            while (l := f.readline().decode().strip()):
                logging.getLogger().info(l)

        from .event_manager import EventManager

        event_manager = EventManager()

        logging.getLogger().info("Initialized event manager")

        # Spawn a thread for actual game logic, while running event loop in main thread

        thread = threading.Thread(target=asyncio.run, args=(_main(event_manager),))
        thread.start()
        with event_manager as em:
            em.process_events()
        thread.join()

    except KeyboardInterrupt:
        logging.getLogger().warning("Keyboard interrupt!")
    except RuntimeWarning as e:
        logging.getLogger().warning(e, exc_info=e)
    except Exception as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
        sys.exit(1)
    finally:
        logging.getLogger().info("Final cleanup")
        sys.exit(0)


if __name__ == "__main__":
    main()
