"""Display surface for OpenGL rendering."""

from __future__ import annotations

import asyncio
import threading
from typing import *

import moderngl
import pygame.display


class GLSurface(pygame.Surface):
    """OpenGL-based rendering surface.

    Functions as a wrapper for pygame.Surface and moderngl.Context's Framebuffer.
    """

    def __init__(self, size: Tuple[int, int], texture=False) -> None:
        """Initialize the GLSurface object.

        During typical application startup, an OpenGL context is created by whatever
        the environment (GLFW, SDL, pygame, etc.) by hooking into OS-specific windowing
        calls. From the docs:

        - https://www.khronos.org/opengl/wiki/Creating_an_OpenGL_Context_(WGL)#A_Note_on_Platforms

        > Because OpenGL doesn't exist until you create an OpenGL Context, OpenGL
        context creation is not governed by the OpenGL Specification. It is instead
        governed by platform-specific APIs.

        In reality, when we call `moderngl.create_context()` without the standalone
        parameter, it doesn't actually create an OpenGL context, and simply returns a
        handle to the existing one, and the default framebuffer.

        - https://moderngl.readthedocs.io/en/5.8.2/the_guide/basic.html#creating-a-context
        - https://moderngl.readthedocs.io/en/5.8.2/topics/context.html#context
        - https://moderngl.readthedocs.io/en/stable/reference/context.html#Context.screen

        > ModernGL can only create headless contexts (no window), but it can also detect
        and use contexts from a large range of window libraries

        - https://stackoverflow.com/questions/47434994/framebuffer-size-and-viewport-relationship
        - https://www.khronos.org/opengl/wiki/Default_Framebuffer

        :param size: The size of the surface.
        :param standalone: Whether to create a standalone OpenGL context. A standalone
            GLContext will allow to render to a texture, represented as the new
            pygame.Surface object.
        :return: None
        """

        if not texture:
            self._init_real_display(size)
        else:
            self._init_standalone_surface(size)

    def _init_real_display(self, size: Tuple[int, int]):
        """Initialize the real display."""

        if not pygame.display.get_init():
            raise RuntimeError(
                "pygame.display must be initialized before creating a GLSurface."
            )

        if not threading.current_thread() is threading.main_thread():
            raise RuntimeError("Windowed GLSurface must be created in the main thread.")

        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
        )
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        self._surface = pygame.display.set_mode(
            size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
        )
        self._gl_context = moderngl.create_context(require=330, standalone=False)

    def _init_standalone_surface(self, size: Tuple[int, int]):
        """Initialize the standalone surface.

        :param size: The size of the surface.
        :return: None
        """
        self._surface = pygame.Surface(size, pygame.SRCALPHA)
        self._gl_context = moderngl.create_context(requires=330, standalone=True)
        print(self._gl_context.info)
        print(self._gl_context.viewport)
        self._gl_context.viewport = (0, 0, *size)
