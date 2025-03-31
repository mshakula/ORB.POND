"""General utilities and other definitions for use in project.
"""

import os
import sys
import asyncio
import contextlib
import tempfile
import functools

from typing import *


@contextlib.contextmanager
def suppress_file_descriptor(fileno: int) -> Generator[None, None, None]:
    """A context manager that redirects a file descriptor to /dev/null.

    A problem is that if I redirect underlying C code with just the os.stderr,
    it doesn't work, since those are python-local objects. This is a way to
    redirect the underlying file descriptor.

    Based on: https://stackoverflow.com/questions/24277488
    """

    try:
        save_fd = os.dup(fileno)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, fileno)
        os.close(devnull)
        yield
    finally:
        os.dup2(save_fd, fileno)
        os.close(save_fd)


@contextlib.contextmanager
def capture_file_descriptor(fileno: int) -> Generator[int, None, None]:
    """A context manager that redirects a file descriptor to a temporary read/write file.
    """
    with tempfile.TemporaryFile() as temp_file:
        try:
            save_fd = os.dup(fileno)
            temp_fd = temp_file.fileno()
            os.dup2(temp_fd, fileno)
            yield temp_file
        finally:
            os.dup2(save_fd, fileno)
            os.close(save_fd)


suppress_stdout = functools.partial(suppress_file_descriptor, sys.stdout.fileno())
suppress_stderr = functools.partial(suppress_file_descriptor, sys.stderr.fileno())
capture_stdout = functools.partial(capture_file_descriptor, sys.stdout.fileno())
capture_stderr = functools.partial(capture_file_descriptor, sys.stderr.fileno())


def freeze_class_fields(*fields: str) -> type:
    """A decorator that freezes the given member fields of a class.
    """

    class FrozenFieldClass(type):
        def __setattr__(cls, name: str, value: Any) -> None:
            if name in fields:
                raise AttributeError(f"Cannot set attribute {name}")
            super().__setattr__(name, value)

        def __delattr__(cls, name: str) -> None:
            if name in fields:
                raise AttributeError(f"Cannot delete attribute {name}")
            super().__delattr__(name)

    @functools.wraps(freeze_class_fields)
    def decorator(cls: type) -> None:
        class Frozen(cls, metaclass=FrozenFieldClass):
            pass
        Frozen.__name__ = cls.__name__
        Frozen.__qualname__ = cls.__qualname__
        return Frozen

    return decorator


class TerminateTaskGroup(Exception):
    """A custom exception to terminate a task group.

    From the docs
    https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup :
    '''
    The first time any of the tasks belonging to the group fails with an exception
    other than asyncio.CancelledError, the remaining tasks in the group are cancelled.
    '''
    """
    pass


def terminate_task_group(tg: asyncio.TaskGroup) -> None:
    """Terminate a task group.
    """

    async def cancel():
        raise TerminateTaskGroup()
    tg.create_task(cancel())
