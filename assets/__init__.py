"""
Assets package for ORB.POND.GAME.
Makes game assets discoverable via imports using importlib.resources.
"""

import importlib.resources


def get_asset_path(filename):
    """Get the path to an asset file using importlib.resources.

    :param filename: The name of the asset file
    :return: Path to the asset that can be used with pygame.image.load
    """
    return str(importlib.resources.files(__package__) / filename)


def list_available_assets():
    """List all available assets in the package.

    :return: List of asset filenames
    """
    return [
        p.name for p in importlib.resources.files(__package__).iterdir()
        if p.is_file()
    ]
