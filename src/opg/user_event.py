"""Metaclass to support creating user events
"""

from __future__ import annotations

import logging
import pygame.event

from typing import *

from . import util


class UserEventMetaclass(type):
    """Metaclass to support creating custom pygame user event factories.

    The created classes will be used to create instances of pygame.event.Event
    with the appropriate fields by overriding the __new__ method. Essentially,
    the objects created by this will not be instances of the factory class, but
    instances of pygame.event.Event. This approach is better than creating normal
    factories however because it provides better scoping and encapsulation.

    - https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
    """

    _LOGGER = logging.getLogger(__name__)

    def __new__(cls, clsname, bases, attrs, **kwargs):
        """Create a new class with a unique event type.
        """
        try:
            event_type = pygame.event.custom_type()
        except pygame.error as e:
            raise RuntimeError("No more custom event types available.") from e

        def __new__(cls, *args, **kwargs):
            """Create a new instance of pygame.event.Event with the appropriate fields.
            """
            for k in kwargs:
                if k not in attrs['__annotations__']:
                    raise AttributeError(f"Attribute {k} not in {clsname}")
            return pygame.event.Event(event_type, **{
                k: kwargs[k] if k in kwargs else None for k in attrs.get('__annotations__', {})
            })

        mod_attrs = attrs.copy()
        mod_attrs["__new__"] = __new__
        mod_attrs["type"] = event_type

        cls._LOGGER.debug(f"Created user event class {clsname} with type {event_type}")
        return super().__new__(cls, clsname, bases, mod_attrs)

    def __setattr__(cls, name: str, value: Any) -> None:
        """Prevent setting attributes on the resulting factory class.
        """
        raise AttributeError(f"Cannot set attribute {name}")

    def __delattr__(self, name):
        """Prevent deleting attributes on the resulting factory class.
        """
        raise AttributeError(f"Cannot delete attribute {name}")


class TimerUpdateEvFactory(metaclass=UserEventMetaclass):
    """Factory to update the timer display.
    """
