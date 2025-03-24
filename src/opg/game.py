import os
import pygame

from . import assets

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "ORB.POND.GAME"
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
FONT_NAME = "Berlin"


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        # Store position as ratio of screen size for easy scaling
        self.x_ratio = x / SCREEN_WIDTH
        self.y_ratio = y / SCREEN_HEIGHT
        self.width_ratio = width / SCREEN_WIDTH
        self.height_ratio = height / SCREEN_HEIGHT

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
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
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5)

        text_surf = self.font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.screen_width, self.screen_height = self.screen.get_size()

        # Initialize buttons
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 300, 200, 50, "Start Game", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 370, 200, 50, "Settings", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 440, 200, 50, "Quit", WHITE, GRAY)
        ]

        # Load and scale background image
        self.original_bg = self.load_background()
        self.bg_image = pygame.transform.scale(
            self.original_bg, (self.screen_width, self.screen_height))

        # Update initial button sizes based on actual screen dimensions
        self.update_ui_elements()

        # Title font
        self.title_font_size = 72
        self.title_font = pygame.font.SysFont(FONT_NAME, self.title_font_size)
        self.title_text = self.title_font.render(TITLE, True, WHITE)
        self.title_position = (
            self.screen_width //
            2 -
            self.title_text.get_width() //
            2,
            100)

    def load_background(self):
        image = pygame.image.load(assets.get_asset_path('ORB.POND.png'))
        return image  # Store original image for rescaling

    def update_ui_elements(self):
        """Update UI elements based on current screen size"""
        self.screen_width, self.screen_height = self.screen.get_size()

        # Update button sizes and positions
        for button in self.buttons:
            button.update_size(self.screen_width, self.screen_height)

        # Update title font size and position
        self.title_font_size = max(36, int(72 * (self.screen_height / SCREEN_HEIGHT)))
        self.title_font = pygame.font.SysFont(FONT_NAME, self.title_font_size)
        self.title_text = self.title_font.render(TITLE, True, WHITE)
        self.title_position = (self.screen_width //
                               2 -
                               self.title_text.get_width() //
                               2, int(100 *
                                      (self.screen_height /
                                       SCREEN_HEIGHT)))

        # Rescale background
        self.bg_image = pygame.transform.scale(
            self.original_bg, (self.screen_width, self.screen_height))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                # Handle window resize event
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE
                )
                self.update_ui_elements()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons[0].is_clicked(pygame.mouse.get_pos(), True):
                    print("Starting game...")
                    # Here you would transition to the actual game
                    # self.start_game()
                elif self.buttons[1].is_clicked(pygame.mouse.get_pos(), True):
                    print("Opening settings...")
                    # self.open_settings()
                elif self.buttons[2].is_clicked(pygame.mouse.get_pos(), True):
                    self.running = False

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)

    def render(self):
        # Draw background
        self.screen.blit(self.bg_image, (0, 0))

        # Draw title
        self.screen.blit(self.title_text, self.title_position)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
