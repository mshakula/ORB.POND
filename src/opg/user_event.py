"""Metaclass to support creating user events
"""

from __future__ import annotations

import logging
import pygame.event

from typing import *

from . import util


class UserEventMetaclass(type):
    """Metaclass to support creating custom pygame user events.

    https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
    """

    _LOGGER = logging.getLogger(__name__)

    def __new__(cls, clsname, bases, attrs, **kwargs):
        """Create a new class with a unique event type.
        """
        print(attrs)

        try:
            event_type = pygame.event.custom_type()
        except pygame.error as e:
            raise RuntimeError("No more custom event types available.") from e

        def __new__(cls, *args, **kwargs):
            for k in kwargs:
                if k not in attrs['__annotations__']:
                    raise AttributeError(f"Attribute {k} not in {clsname}")
            return pygame.event.Event(event_type, **{
                k: kwargs[k] if k in kwargs else None for k in attrs['__annotations__']
            })

        mod_attrs = attrs.copy()
        mod_attrs["__new__"] = __new__
        mod_attrs["type"] = event_type

        cls._LOGGER.debug(f"Created user event {clsname} with type {event_type}")
        return super().__new__(cls, clsname, bases, mod_attrs)

    def __setattr__(cls, name: str, value: Any) -> None:
        """Prevent setting attributes on the class.
        """

        raise AttributeError(f"Cannot set attribute {name}")

    def __delattr__(self, name):
        """Prevent deleting attributes on the class.
        """

        raise AttributeError(f"Cannot delete attribute {name}")


class TimerUpdateEvent(metaclass=UserEventMetaclass):
    """Event to update the timer display.
    """

    time: int

    def blah(self):
        print("blah")
