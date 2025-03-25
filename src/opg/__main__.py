"""
Entry point for the ORB.POND game.
"""

import sys
import logging
import argparse
import importlib
import asyncio
import concurrent.futures
import queue

from typing import *

from . import logging_config


async def _main() -> None:
    """
    Asynchronous entry point for ORB.POND.GAME.

    - Asyncio inspired by https://github.com/AlexElvers/pygame-with-asyncio.git
      - Without it, there actually is a constant 100% CPU utilization.
    - Concurrent Futures are the better threading interface https://stackoverflow.com/a/61360215
    """

    try:
        parser = argparse.ArgumentParser(description=__doc__)
        logging_config.set_argparse_common_log_options(parser)
        args = parser.parse_args()
        logging_config.common_logger_config_args(args)
    except Exception as e:
        raise RuntimeError("Failed to configure logging") from e

    # import pygame
    import pygame.display
    import pygame.image
    from .event_manager import EventManager

    event_manager = EventManager()
    await asyncio.sleep(1)

    # Set up the display
    screen: pygame.Surface = pygame.display.set_mode(
        size=(800, 600),
        flags=pygame.SCALED | pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.RESIZABLE,
        depth=0,
        display=0,
        vsync=1
    )
    pygame.display.set_caption('ORB.POND.GAME')

    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     loop = asyncio.get_event_loop()
    #     loop.set_default_executor(executor)

    from .game import Menu
    Menu(screen).run()


def main() -> None:
    """
    Entry point for the installed script.
    """

    try:
        asyncio.run(_main(), debug=True)
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # try:
        #     loop.run_until_complete(_main())
        # finally:
        #     loop.close()
    except KeyboardInterrupt:
        logging.getLogger().warning("Keyboard interrupt!")
    except RuntimeWarning as e:
        logging.getLogger().warning(e, exc_info=e)
    except Exception as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
        sys.exit(1)
    finally:
        logging.getLogger().info("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
