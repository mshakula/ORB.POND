#!/usr/bin/env python

"""Demo a ModernGL sprite group with a single sprite.

From: https://stackoverflow.com/a/65653236

Look into this for collision detection: https://www.reddit.com/r/gamedev/comments/rws1b9/how_to_design_a_2d_collision_system_that_can/
https://en.wikipedia.org/wiki/Gilbert%E2%80%93Johnson%E2%80%93Keerthi_distance_algorithm
https://github.com/xuzebin/gjk
https://www.reddit.com/r/opengl/comments/zoa4fm/implemented_gjk_and_epa_for_2d_collision/

Sprite Image collage:
https://stackoverflow.com/questions/3590643/multiple-image-placement-algorithm-collage-algorithm

Tangent Mapping:
https://learnopengl.com/Advanced-Lighting/Normal-Mapping
"""

import ctypes
import math

import moderngl
import pygame
import pygame.gfxdraw

from opg.assets import get_asset_path

vertex_shader_sprite = """
#version 330
in vec2 in_position;
in vec2 in_uv;
out vec2 v_uv;

uniform float u_rotation; // Rotation angle in radians
uniform float u_zoom; // Zoom factor

void main()
{
    v_uv = in_uv;

    // Apply zoom
    vec2 zoomed_position = in_position * u_zoom;

    // Apply rotation
    float cos_theta = cos(u_rotation);
    float sin_theta = sin(u_rotation);
    mat2 rotation_matrix = mat2(
        cos_theta, -sin_theta,
        sin_theta, cos_theta
    );

    vec2 transformed_position = rotation_matrix * zoomed_position;
    gl_Position = vec4(transformed_position, 0.0, 1.0);
}
"""

fragment_shader_sprite = """
#version 330
out vec4 fragColor;
uniform sampler2D u_texture;
in vec2 v_uv;
void main()
{
    fragColor = texture(u_texture, v_uv);
}
"""


class ModernGLGroup(pygame.sprite.Group):

    gl_context = None
    gl_program = None
    gl_buffer = None
    gl_vao = None
    gl_textures = {}

    def __init__(self, sprites=None):
        if sprites is None:
            super().__init__()
        else:
            super().__init__(sprites)

    def get_program():
        if ModernGLGroup.gl_program is None:
            ModernGLGroup.gl_program = ModernGLGroup.gl_context.program(
                vertex_shader=vertex_shader_sprite,
                fragment_shader=fragment_shader_sprite,
            )
        return ModernGLGroup.gl_program

    def get_buffer():
        if ModernGLGroup.gl_buffer is None:
            ModernGLGroup.gl_buffer = ModernGLGroup.gl_context.buffer(
                None, reserve=6 * 4 * 4
            )
        return ModernGLGroup.gl_buffer

    def get_vao():
        """
        see https://moderngl.readthedocs.io/en/latest/topics/buffer_format.html#buffer-format-label

        VAO vs VBO: https://computergraphics.stackexchange.com/questions/10332/understanding-vao-and-vbo

        (VBO is just the buffer ctx.buffer(), and VAO is the CPU-side object that describes the VBO)
        """
        if ModernGLGroup.gl_vao is None:
            ModernGLGroup.gl_vao = ModernGLGroup.gl_context.vertex_array(
                ModernGLGroup.get_program(),
                [(ModernGLGroup.get_buffer(), "2f4 2f4", "in_position", "in_uv")],
            )
        return ModernGLGroup.gl_vao

    def get_texture(image) -> moderngl.Texture:
        if image not in ModernGLGroup.gl_textures:
            rgba_image = image.convert_alpha()
            texture = ModernGLGroup.gl_context.texture(
                rgba_image.get_size(), 4, rgba_image.get_buffer()
            )
            texture.swizzle = "BGRA"
            ModernGLGroup.gl_textures[image] = texture
        return ModernGLGroup.gl_textures[image]

    def convert_vertex(pt, surface):
        return pt[0] / surface.get_width() * 2 - 1, 1 - pt[1] / surface.get_height() * 2

    def render(sprite, surface):
        """Uniforms don't change every frame, so we can set them once and reuse
        them:

        From https://www.khronos.org/opengl/wiki/Uniform_(GLSL):
        '''
        Uniforms are so named because they do not change from one shader invocation to the next within a particular rendering call thus their value is uniform among all invocations. This makes them unlike shader stage inputs and outputs, which are often different for each invocation of a shader stage.
        '''
        """
        corners = [
            ModernGLGroup.convert_vertex(sprite.rect.bottomleft, surface),
            ModernGLGroup.convert_vertex(sprite.rect.bottomright, surface),
            ModernGLGroup.convert_vertex(sprite.rect.topright, surface),
            ModernGLGroup.convert_vertex(sprite.rect.topleft, surface),
        ]

        # These make two triangles.
        vertices_quad_2d = (ctypes.c_float * (6 * 4))(
            *corners[0],
            0.0,
            1.0,
            *corners[1],
            1.0,
            1.0,
            *corners[2],
            1.0,
            0.0,
            *corners[0],
            0.0,
            1.0,
            *corners[2],
            1.0,
            0.0,
            *corners[3],
            0.0,
            0.0,
        )

        ModernGLGroup.get_buffer().write(vertices_quad_2d)
        ModernGLGroup.get_texture(sprite.image).use(0)

        # Set the rotation and zoom uniforms
        ModernGLGroup.get_program()["u_rotation"] = getattr(sprite, "rotation", 0.0)
        ModernGLGroup.get_program()["u_zoom"] = getattr(sprite, "zoom", 1.0)

        ModernGLGroup.get_vao().render()

    def draw(self, surface):
        for sprite in self:
            ModernGLGroup.render(sprite, surface)


class SpriteObject(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.image.load(get_asset_path("icon.png")).convert_alpha()
        except BaseException:
            print("Could not load image, using a yellow circle")
            self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255, 255, 0), (50, 50), 50)
        self.rect = self.image.get_rect(center=(x, y))
        self.rotation = 0.0  # Rotation in radians
        self.zoom = 1.0  # Zoom factor, 1.0 is original size

    def update(self, surface):
        keys = pygame.key.get_pressed()
        vel = 5
        rot_speed = 0.05  # Rotation speed in radians
        zoom_speed = 0.05  # Zoom speed factor

        # Movement controls
        if keys[pygame.K_LEFT]:
            self.rect.left = max(0, self.rect.left - vel)
        if keys[pygame.K_RIGHT]:
            self.rect.right = min(surface.get_width(), self.rect.right + vel)
        if keys[pygame.K_UP]:
            self.rect.top = max(0, self.rect.top - vel)
        if keys[pygame.K_DOWN]:
            self.rect.bottom = min(surface.get_height(), self.rect.bottom + vel)

        # Rotation controls
        if keys[pygame.K_q]:
            self.rotation += rot_speed  # Rotate counter-clockwise
        if keys[pygame.K_e]:
            self.rotation -= rot_speed  # Rotate clockwise

        # Zoom controls
        if keys[pygame.K_z]:
            self.zoom = max(0.1, self.zoom - zoom_speed)  # Zoom out
        if keys[pygame.K_x]:
            self.zoom = min(5.0, self.zoom + zoom_speed)  # Zoom in


pygame.init()

pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(
    pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

window = pygame.display.set_mode(
    (960, 500), pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
)
# (500, 500), pygame.DOUBLEBUF | pygame.OPENGL)
clock = pygame.time.Clock()


gl_context = moderngl.create_context()
gl_context.enable(moderngl.BLEND)
ModernGLGroup.gl_context = gl_context

print(gl_context.info)
print(dir(gl_context))


sprite_object = SpriteObject(*window.get_rect().center)
group = ModernGLGroup(sprite_object)

run = True
while run:
    clock.tick(60)
    event_list = pygame.event.get()
    for event in event_list:
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.VIDEORESIZE:
            window = pygame.display.set_mode(
                # (event.w, event.h), pygame.DOUBLEBUF | pygame.OPENGL)
                (event.w, event.h),
                pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE,
            )
            gl_context.viewport = (
                event.w // 2,
                event.h // 2,
                event.w // 2,
                event.h // 2,
            )
            print(f"Resized to {event.w}x{event.h}")

    group.update(window)

    gl_context.clear(0.2, 0.2, 0.2)
    group.draw(window)
    pygame.display.flip()

pygame.quit()
exit()
