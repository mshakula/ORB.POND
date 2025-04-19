import pygame
import math

class Asteroid:
    def __init__(self, image, pos, size):
        """
        Initialize an Asteroid object.

        Args:
            image (pygame.Surface): The original image for the asteroid.
            pos (tuple): The (x, y) position where the asteroid will be placed.
            size (int): The size (width and height in pixels) to scale the asteroid image.
        """
        # Scale the image to the desired size.
        self.image = pygame.transform.scale(image, (size, size))
        self.pos = pos
        self.size = size
        # Calculate mass proportional to the area.
        self.mass = (size * size) / 10
        # Flag to indicate if the asteroid has been "pictured" (e.g., captured by a camera)
        self.pictured = False

    def draw(self, surface):
        """
        Draw the asteroid on the provided surface.

        Args:
            surface (pygame.Surface): The pygame surface to draw the asteroid on.
        """
        x, y = self.pos
        # Get the rect and set its center to the asteroid's position.
        rect = self.image.get_rect(center=(x, y))
        surface.blit(self.image, rect)