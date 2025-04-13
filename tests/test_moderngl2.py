#!/usr/bin/env python

import logging

import moderngl
import pygame

from opg.display_surface import GLSurface

# pygame.init()
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
# pygame.display.gl_set_attribute(
#     pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
# )
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

# # Note: an OpenGL context is created by the OS-specific windowing system, whatever that is.
# # GLFW, SDL, pygame, whatever. From the docs:
# # https://www.khronos.org/opengl/wiki/Creating_an_OpenGL_Context_(WGL)#A_Note_on_Platforms
# #
# # """
# # Because OpenGL doesn't exist until you create an OpenGL Context, OpenGL
# # context creation is not governed by the OpenGL Specification. It is
# # instead governed by platform-specific APIs.
# # """"
# logging.info("Creating display")
# window = pygame.display.set_mode((500, 500), pygame.DOUBLEBUF | pygame.OPENGL)


# # In reality, this doesn't actually create a context:
# #
# # https://moderngl.readthedocs.io/en/5.8.2/the_guide/basic.html#creating-a-context
# # https://moderngl.readthedocs.io/en/5.8.2/topics/context.html#context
# # """
# # ModernGL can only create headless contexts (no window), but it can also
# # detect and use contexts from a large range of window libraries
# # """
# logging.info("Creating context")
# gl_context = moderngl.create_context(require=330)

x = GLSurface((100, 200), True)
