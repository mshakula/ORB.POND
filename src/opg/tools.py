# This file defines tools and constants used throughout the game. 
# Updated as needed, might split up into multiple tools files (per purpose) later.
# Avoids the need to change everything in individual files.

# Imports
import pygame
from . import assets
import numpy as np

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "ORB.POND.GAME"
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
PURPLE = (160, 32, 240)
FONT_NAME = "Berlin"


class Button:
    def __init__(self, x, y, width, height, text, color=None, hover_color=None, image=None):
        # Store position as ratio of screen size for easy scaling
        self.x_ratio = x / SCREEN_WIDTH
        self.y_ratio = y / SCREEN_HEIGHT
        self.width_ratio = width / SCREEN_WIDTH
        self.height_ratio = height / SCREEN_HEIGHT

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.image = image if not image else pygame.transform.scale(image, (self.rect.width, self.rect.height))
        self.is_hovered = False
        self.font = pygame.font.SysFont(FONT_NAME, 32)
        self.font_size = 32

    def update_size(self, screen_width, screen_height):
        """Update button size and position based on screen dimensions"""
        x = int(self.x_ratio * screen_width)
        y = int(self.y_ratio * screen_height)
        width = int(self.width_ratio * screen_width)
        height = int(self.height_ratio * screen_height)
        self.rect = pygame.Rect(x, y, width, height)

        # Scale font size based on screen height
        self.font_size = max(16, int(32 * (screen_height / SCREEN_HEIGHT)))
        self.font = pygame.font.SysFont(FONT_NAME, self.font_size)

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        if self.image:
            image_scaled = self.image
            if self.is_hovered:
                # Grayscale the image using luminance weights whatever that is
                arr = pygame.surfarray.array3d(image_scaled)
                gray_arr = np.dot(arr[..., :3], [0.299, 0.587, 0.114])
                gray_arr_3ch = np.stack((gray_arr,) * 3, axis=-1).astype(np.uint8)
                image_scaled = pygame.surfarray.make_surface(gray_arr_3ch)
            surface.blit(image_scaled, self.rect.topleft)
            # Sample average background color from the image
            color = self.average_color_from_surface(surface, self.rect)
        else:
            # color
            pygame.draw.rect(surface, color, self.rect, border_radius=5)
        # border
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)
        # Change text color based on background
        text_color = WHITE if self.is_dark_color(color) else BLACK
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click
    
    def is_dark_color(self, rgb):
        r, g, b = rgb
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)  # Perceived brightness formula
        return brightness < 128
    
    def average_color_from_surface(self, surface, rect):
        sub = surface.subsurface(rect)
        pixels = pygame.surfarray.array3d(sub)
        avg_color = pixels.mean(axis=(0, 1)).astype(int)
        return tuple(avg_color)

