"""Metaclass to support creating user events
"""

import asyncio.events


class UserEvent:
    """Metaclass to support creating custom pygame user events.
    """

    def __new__(cls, name, bases, dct):
        """Create a new class with a unique event type.
        """
        event_type = asyncio.events.UserEvent()
        dct['event_type'] = event_type
        return super().__new__(cls, name, bases, dct)
