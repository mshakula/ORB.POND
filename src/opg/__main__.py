"""
Entry point for ORB.POND.GAME when run as a module.

- Asyncio inspired by https://github.com/AlexElvers/pygame-with-asyncio.git
  - Without it, there actually is a constant 100% CPU utilization.
- Concurrent Futures are the better threading interface https://stackoverflow.com/a/61360215
"""

import sys
import logging
import argparse
import importlib
import asyncio
import concurrent.futures

from typing import *

from . import logging_config


async def _main() -> None:
    """Entry point for the installed script."""

    try:
        parser = argparse.ArgumentParser(description="ORB.POND.GAME")
        logging_config.set_argparse_common_log_options(parser)
        args = parser.parse_args()
        logging_config.common_logger_config_args(args)
    except Exception as e:
        raise RuntimeError("Failed to configure logging") from e

    import pygame
    import pygame.display
    import pygame.image

    pygame.display.init()

    # Set up the display
    screen: pygame.Surface = pygame.display.set_mode(
        size=(800, 600),
        flags=pygame.SCALED | pygame.SRCALPHA | pygame.DOUBLEBUF | pygame.RESIZABLE,
        depth=0,
        display=0,
        vsync=1
    )
    pygame.display.set_caption('ORB.POND.GAME')

    # Start the game
    game_module = importlib.import_module('.menu', __package__)
    main_menu = getattr(game_module, 'Menu')
    main_menu(screen).run()


def main():
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logging.getLogger().warning("Keyboard interrupt!")
    except Exception as e:
        logging.getLogger().critical("Unhandled exception", exc_info=e)
        sys.exit(1)
    finally:
        logging.getLogger().info("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
