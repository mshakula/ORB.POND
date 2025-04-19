# "about" window
import pygame
import os
from . import assets
from . import tools

def update_about_ui_elements(screen, body_lines, buttons, assets, tools):
    screen_width, screen_height = screen.get_size()

    # font
    about_font = pygame.font.SysFont(tools.FONT_NAME, 24)
    header_font = pygame.font.SysFont(tools.FONT_NAME, 36)
    header_text = header_font.render("About ORB.POND.GAME", True, tools.PURPLE)

    # background and text
    image = pygame.image.load(assets.get_asset_path('space.png'))
    bg_image = pygame.transform.scale(image, (screen_width, screen_height))
    padding = 20
    line_spacing = 10
    text_width = max(about_font.size(line)[0] for line in body_lines)
    text_height = len(body_lines) * (about_font.get_linesize() + line_spacing)
    box_width = text_width + padding * 2
    box_height = text_height + padding * 2
    box_x = (screen_width - box_width) // 2
    box_y = 130
    text_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    text_positions = []
    for i, line in enumerate(body_lines):
        text_surf = about_font.render(line, True, tools.PURPLE)
        text_rect = text_surf.get_rect()
        text_rect.midtop = (screen_width // 2, box_y + padding + i * (about_font.get_linesize() + line_spacing))
        text_positions.append((text_surf, text_rect))

    for button in buttons:
        button.update_size(screen_width, screen_height)

    return {
        "bg_image": bg_image,
        "header_text": header_text,
        "text_box_rect": text_box_rect,
        "text_positions": text_positions
    }

def open_about(screen, stop_game):
    about_running = True

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
    layout = update_about_ui_elements(screen, body_lines, buttons, assets, tools)

    while about_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                about_running = False
                stop_game()

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                layout = update_about_ui_elements(screen, body_lines, buttons, assets, tools)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if poster_button.is_clicked(pos, True):
                    poster = assets.get_asset_path('POSTER.pdf')
                    os.system(f"open {poster}")
                elif report_button.is_clicked(pos, True):
                    os.system("open final_report.pdf")
                elif back_button.is_clicked(pos, True):
                    about_running = False

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
