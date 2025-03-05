import os
import pygame

import assets

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


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont(None, 32)

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
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 300, 200, 50, "Start Game", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 370, 200, 50, "Settings", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 440, 200, 50, "Quit", WHITE, GRAY)
        ]

        # Load background image
        self.bg_image = self.load_background()

    def load_background(self):
        image = pygame.image.load(assets.get_asset_path('ORB.POND.png'))
        return pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
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
        font = pygame.font.SysFont(None, 72)
        title_text = font.render(TITLE, True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 -
                         title_text.get_width() // 2, 100))

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()


def game_loop():
    """Initialize and run the game."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    menu = Menu(screen)
    menu.run()

    # Clean up pygame
    pygame.quit()
