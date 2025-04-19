# The mechanics of the game itself, the title screen and routing from there

import os
import pygame

from . import assets
from .about import open_about
from .tools import TITLE, FONT_NAME, WHITE, GRAY, SCREEN_WIDTH, SCREEN_HEIGHT, Button
from .game import game_menu

pygame.init()

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        self.screen_width, self.screen_height = self.screen.get_size()

        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 100, 300, 200, 50, "Start Game", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 370, 200, 50, "About the game!", WHITE, GRAY),
            Button(SCREEN_WIDTH // 2 - 100, 440, 200, 50, "Quit", WHITE, GRAY)
        ]
        self.original_bg = self.load_background()
        self.bg_image = pygame.transform.scale(
            self.original_bg, (self.screen_width, self.screen_height))
        self.update_ui_elements()
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
        return image

    def update_ui_elements(self):
        """Update UI elements based on current screen size"""
        self.screen_width, self.screen_height = self.screen.get_size()
        for button in self.buttons:
            button.update_size(self.screen_width, self.screen_height)
        self.title_font_size = max(36, int(72 * (self.screen_height / SCREEN_HEIGHT)))
        self.title_font = pygame.font.SysFont(FONT_NAME, self.title_font_size)
        self.title_text = self.title_font.render(TITLE, True, WHITE)
        self.title_position = (self.screen_width //
                               2 -
                               self.title_text.get_width() //
                               2, int(100 *
                                      (self.screen_height /
                                       SCREEN_HEIGHT)))
        self.bg_image = pygame.transform.scale(
            self.original_bg, (self.screen_width, self.screen_height))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h),
                    pygame.RESIZABLE
                )
                self.update_ui_elements()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.buttons[0].is_clicked(pygame.mouse.get_pos(), True):
                    print("Starting game...")
                    game_menu()
                elif self.buttons[1].is_clicked(pygame.mouse.get_pos(), True):
                    print("Opening about screen...")
                    open_about(self.screen, self._exit_game)
                elif self.buttons[2].is_clicked(pygame.mouse.get_pos(), True):
                    self.running = False

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)

    def render(self):
        self.screen.blit(self.bg_image, (0, 0))
        self.screen.blit(self.title_text, self.title_position)

        for button in self.buttons:
            button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()

    def _exit_game(self):
        self.running = False
