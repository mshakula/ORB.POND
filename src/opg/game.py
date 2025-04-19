# games launch from here
import pygame
import sys
import os
from . import assets
from . import tools
from . import launch

def play_game(button):
    if button=='Game 1':
        launch.main()

def game_menu():
    pygame.init()
    screen = pygame.display.set_mode((tools.SCREEN_WIDTH, tools.SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(tools.TITLE)
    clock = pygame.time.Clock()

    # Text for the "About" box
    body_lines = [
        "Choose a game below to get started. [include explanations?]",
    ]

    game_buttons = [
        tools.Button(100, 400, 200, 60, "Game 1", color=tools.BLUE, hover_color=tools.GRAY),
        tools.Button(320, 400, 200, 60, "Game 2", color=tools.BLUE, hover_color=tools.GRAY),
        tools.Button(540, 400, 200, 60, "Game 3", color=tools.BLUE, hover_color=tools.GRAY),
        tools.Button(320, 480, 200, 60, "Game 4", color=tools.BLUE, hover_color=tools.GRAY),
    ]

    ui_elements = tools.update_ui_elements(screen, body_lines, game_buttons, assets, tools)

    running = True
    while running:
        screen.blit(ui_elements["bg_image"], (0, 0))
        screen.blit(ui_elements["header_text"], (tools.SCREEN_WIDTH // 2 - ui_elements["header_text"].get_width() // 2, 60))

        # Draw text box
        pygame.draw.rect(screen, tools.WHITE, ui_elements["text_box_rect"], border_radius=10)
        pygame.draw.rect(screen, tools.BLACK, ui_elements["text_box_rect"], 2, border_radius=10)

        # Draw text lines
        for text_surf, text_rect in ui_elements["text_positions"]:
            screen.blit(text_surf, text_rect)

        # Input
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                ui_elements = tools.update_ui_elements(screen, body_lines, game_buttons, assets, tools)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_click = True

        for button in game_buttons:
            button.check_hover(mouse_pos)
            button.draw(screen)
            if button.is_clicked(mouse_pos, mouse_click):
                print(f"Launching {button.text}...")
                play_game(button.text)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

