import pygame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Font
pygame.font.init()
font = pygame.font.SysFont('Arial', 30)

class Button:
    def __init__(self, x, y, width, height, text, text_color, color, disabled_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color
        self.color = color
        self.disabled_color = disabled_color
        self.hovered = False
        self.disabled = False

    def draw(self, screen):
        if self.disabled:
            color = self.disabled_color
        else:
            color = GRAY if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        font = pygame.font.SysFont(None, 30)
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def is_clicked(self, mouse_pos, mouse_click):
        return not self.disabled and self.rect.collidepoint(mouse_pos) and mouse_click
