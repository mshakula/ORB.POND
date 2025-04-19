# "about" window
import pygame
import os
from . import assets
from . import tools

def open_about(screen, stop_game):
    running = True

    body_lines = [
        "Physics, for the non-obsessed, is often considered a subject to approach",
        "with caution--or maybe a hazmat suit. We argue that its bad reputation is",
        "undeserved. With the ORBital PONDerer Game (ORB.POND.GAME), see orbital",
        "mechanics come to life with the click of a button. Orbits in space are",
        "governed by gravity, and predicting them is a classic physics challenge.",
        "Computers can run simulations using numerical methods, but they're often",
        "static or slow. This project asks: can we make an orbital simulator fast",
        "and interactive enough to feel like a video game? Our hope is that by playing",
        "this game, you will find orbital mechanics intuitive, interactive, and fun!"
    ]

    # Buttons
    poster_button = tools.Button(300, 400, 200, 40, "View Poster", tools.BLUE, tools.GRAY)
    report_button = tools.Button(300, 450, 200, 40, "View Report", tools.BLUE, tools.GRAY)
    button_image = pygame.image.load(assets.get_asset_path('ORB.POND.png'))
    back_button = tools.Button(300, 510, 200, 40, "Back to Menu", image=button_image)
    buttons = [poster_button, report_button, back_button]

    # Initial layout
    layout = tools.update_ui_elements(screen, body_lines, buttons, assets, tools)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                stop_game()

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                layout = tools.update_ui_elements(screen, body_lines, buttons, assets, tools)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if poster_button.is_clicked(pos, True):
                    poster = assets.get_asset_path('POSTER.pdf')
                    os.system(f"open {poster}")
                elif report_button.is_clicked(pos, True):
                    os.system("open final_report.pdf")
                elif back_button.is_clicked(pos, True):
                    running = False

        for btn in buttons:
            btn.check_hover(pygame.mouse.get_pos())

        screen.blit(layout["bg_image"], (0, 0))
        screen.blit(layout["header_text"], (screen.get_width() // 2 - layout["header_text"].get_width() // 2, 80))
        pygame.draw.rect(screen, tools.WHITE, layout["text_box_rect"], border_radius=12)
        pygame.draw.rect(screen, tools.BLACK, layout["text_box_rect"], 2, border_radius=12)

        for surf, rect in layout["text_positions"]:
            screen.blit(surf, rect)

        for btn in buttons:
            btn.draw(screen)

        pygame.display.flip()
