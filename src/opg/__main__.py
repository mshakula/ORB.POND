"""
Entry point for ORB.POND.GAME when run as a module.
"""

import asyncio
import importlib
import time


def main():
    """Entry point for the installed script."""

    # Import the rest of the modules
    game_module = importlib.import_module('.game', __package__)
    game_loop = getattr(game_module, 'game_loop')

    # Start the game
    game_loop()


if __name__ == "__main__":
    main()
