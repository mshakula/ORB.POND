import pygame
import math
import random
import sys
import os
from game_buttons import Button
from asteroid import Asteroid

# --- Constants ---
WIDTH, HEIGHT = 1280, 720  # Larger screen size
FPS = 60
DT = 0.02  # Time step for integration (seconds)

# Gravitational constant (adjust as needed)
G = 2000.0

# Starting position for canon (fixed, adjusted for larger screen)
CANON_POS = (100, HEIGHT - 100)

# Margins and buffers for asteroid placement
EDGE_MARGIN = 100
ASTEROID_BUFFER = 100

# Extra margin to allow taking a picture (so the satellite can get close without colliding)
PICTURE_MARGIN = 100

# Georgia Tech Gold color (RGB)
GEORGIA_TECH_GOLD = (179, 163, 105)

# Fuel
fuel_level = 100  # percent

# --- Helper Functions for RK4 ---
def acceleration(state, asteroids):
    x, y, _, _ = state
    ax, ay = 0, 0
    for asteroid in asteroids:
        ax_, ay_ = asteroid.pos  # Use asteroid.pos attribute
        dx = ax_ - x
        dy = ay_ - y
        r_sq = dx * dx + dy * dy
        if r_sq < 1:
            r_sq = 1
        r = math.sqrt(r_sq)
        a = G * asteroid.mass / r_sq
        ax += a * (dx / r)
        ay += a * (dy / r)
    return ax, ay


def rk4_step(state, dt, asteroids):
    def f(s):
        x, y, vx, vy = s
        ax, ay = acceleration(s, asteroids)
        return (vx, vy, ax, ay)

    k1 = f(state)
    s2 = [state[i] + dt / 2 * k1[i] for i in range(4)]
    k2 = f(s2)
    s3 = [state[i] + dt / 2 * k2[i] for i in range(4)]
    k3 = f(s3)
    s4 = [state[i] + dt * k3[i] for i in range(4)]
    k4 = f(s4)
    new_state = [
        state[i] + dt / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(4)
    ]
    return new_state


def impulse_burn(state, dv):
    global fuel_level
    x, y, vx, vy = state
    if fuel_level <= 0:
        return vx, vy
    speed = math.hypot(vx, vy)
    unit_vx = vx / speed
    unit_vy = vy / speed
    vx += dv * unit_vx
    vy += dv * unit_vy
    fuel_level = max(fuel_level - 10, 0)
    return vx, vy

# --- Pygame Initialization ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Satellite Orbit Game")
clock = pygame.time.Clock()

# Initialize mixer for sound effects
pygame.mixer.init()

# Load images and sound
try:
    background_img = pygame.image.load(
        os.path.join(os.path.dirname(__file__), "assets", "space.jpg")
    ).convert()
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

    canon_img = pygame.image.load(
        os.path.join(os.path.dirname(__file__), "assets", "canon.png")
    ).convert_alpha()
    canon_img = pygame.transform.scale(canon_img, (80, 80))

    satellite_img = pygame.image.load(
        os.path.join(os.path.dirname(__file__), "assets", "satellite.png")
    ).convert_alpha()
    satellite_img = pygame.transform.scale(satellite_img, (40, 40))

    asteroid_imgs_full = [
        pygame.image.load(
            os.path.join(os.path.dirname(__file__), "assets", "asteroid1.png")
        ).convert_alpha(),
        pygame.image.load(
            os.path.join(os.path.dirname(__file__), "assets", "asteroid2.png")
        ).convert_alpha(),
        pygame.image.load(
            os.path.join(os.path.dirname(__file__), "assets", "asteroid3.png")
        ).convert_alpha(),
        pygame.image.load(
            os.path.join(os.path.dirname(__file__), "assets", "asteroid4.png")
        ).convert_alpha(),
    ]

    button1 = Button(50, 100, 200, 50, "Posigrade Burn", (255, 255, 255), (100, 255, 100))
    button2 = Button(50, 170, 200, 50, "Retrograde Burn", (255, 255, 255), (255, 100, 100))

    camera_flash_sound = pygame.mixer.Sound(
        os.path.join(os.path.dirname(__file__), "assets", "camera.wav")
    )
except Exception as e:
    print("Error loading assets. Ensure all required images and sounds are in the correct folder.")
    sys.exit()


def get_random_position_for_asteroid(size, existing_asteroids):
    max_attempts = 1000
    for _ in range(max_attempts):
        x = random.randint(WIDTH // 2 + size // 2 + EDGE_MARGIN, WIDTH - EDGE_MARGIN - size // 2)
        y = random.randint(EDGE_MARGIN + size // 2, HEIGHT - EDGE_MARGIN - size // 2)
        overlap = False
        for a in existing_asteroids:
            ax, ay = a.pos
            asize = a.size
            required_separation = (((size + asize) // 2) + ASTEROID_BUFFER + satellite_img.get_width())
            if math.hypot(x - ax, y - ay) < required_separation:
                overlap = True
                break
        if not overlap:
            return (x, y)
    return (x, y)


def init_asteroids():
    asteroids = []
    asteroid_imgs = random.sample(asteroid_imgs_full, 2)
    for img in asteroid_imgs:
        size = random.randint(80, 150)
        pos = get_random_position_for_asteroid(size, asteroids)
        asteroid = Asteroid(img, pos, size)
        asteroids.append(asteroid)
    return asteroids

asteroids = init_asteroids()
satellite_launched = False
satellite_state = None
picture_count = 0
satellite_path = []
game_finished = False
final_message = ""
font = pygame.font.SysFont("Arial", 24)


def reset_game():
    global satellite_launched, satellite_state, asteroids, picture_count, game_finished, final_message, satellite_path, fuel_level
    satellite_launched = False
    satellite_state = None
    picture_count = 0
    asteroids = init_asteroids()
    game_finished = False
    final_message = ""
    satellite_path = []
    fuel_level = 100

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        mouse_clicked_this_frame = False
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        button1.check_hover(mouse_pos)
        button2.check_hover(mouse_pos)

        if fuel_level <= 0:
            button1.disabled = True
            button2.disabled = True
        else:
            button1.disabled = False
            button2.disabled = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_clicked_this_frame = True

        if mouse_clicked_this_frame:
            if button1.is_clicked(mouse_pos, True) and satellite_launched and satellite_state and fuel_level > 0:
                vx, vy = impulse_burn(satellite_state, 15)
                satellite_state[2] = vx
                satellite_state[3] = vy

            if button2.is_clicked(mouse_pos, True) and satellite_launched and satellite_state and fuel_level > 0:
                vx, vy = impulse_burn(satellite_state, -15)
                satellite_state[2] = vx
                satellite_state[3] = vy
        if event.type == pygame.QUIT:
            running = False
        if game_finished and event.type == pygame.KEYDOWN:
            reset_game()
        if not game_finished and event.type == pygame.MOUSEBUTTONDOWN and not satellite_launched:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - CANON_POS[0]
            dy = mouse_y - CANON_POS[1]
            angle = math.atan2(dy, dx)
            speed = 150
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            satellite_state = [CANON_POS[0], CANON_POS[1], vx, vy]
            satellite_launched = True

    screen.blit(background_img, (0, 0))

    for asteroid in asteroids:
        asteroid.draw(screen)

    platform_width = 120
    platform_height = 10
    platform_x = CANON_POS[0] - platform_width // 2
    platform_y = CANON_POS[1] + (canon_img.get_height() // 2) - 5
    platform_rect = (platform_x, platform_y, platform_width, platform_height)
    pygame.draw.rect(screen, (100, 100, 100), platform_rect)

    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - CANON_POS[0]
    dy = mouse_y - CANON_POS[1]
    angle_deg = math.degrees(math.atan2(-dy, dx))
    rotated_canon = pygame.transform.rotate(canon_img, angle_deg)
    canon_rect = rotated_canon.get_rect(center=CANON_POS)
    screen.blit(rotated_canon, canon_rect)

    button1.draw(screen)
    button2.draw(screen)

    fuel_text = font.render(f"Fuel: {fuel_level}%", True, (255, 255, 255))
    screen.blit(fuel_text, (EDGE_MARGIN - 15 , EDGE_MARGIN + 140))

    if len(satellite_path) > 1:
        pygame.draw.lines(screen, GEORGIA_TECH_GOLD, False, satellite_path, 4)

    if satellite_state:
        x, y, vx, vy = satellite_state
        info_text = font.render(
            f"Pictures: {picture_count}/{len(asteroids)}  |  x: {x:.1f}, y: {y:.1f}, vx: {vx:.1f}, vy: {-vy:.1f}",
            True,
            (255, 255, 255),
        )
        screen.blit(info_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    if not game_finished and satellite_launched and satellite_state:
        satellite_state = rk4_step(satellite_state, DT, asteroids)
        x, y, vx, vy = satellite_state

        if math.hypot(x - CANON_POS[0], y - CANON_POS[1]) > 50:
            satellite_path.append((x, y))

        satellite_radius = satellite_img.get_width() // 2
        for asteroid in asteroids:
            ax, ay = asteroid.pos
            asteroid_radius = asteroid.size // 2
            distance = math.hypot(x - ax, y - ay)
            if distance < (satellite_radius + asteroid_radius):
                final_message = "Collision! You lost."
                game_finished = True
                break

            picture_threshold = satellite_radius + asteroid_radius + PICTURE_MARGIN
            if distance < picture_threshold and not asteroid.pictured:
                asteroid.pictured = True
                picture_count += 1
                camera_flash_sound.play()

        if x < 0 or x > WIDTH or y < 0 or y > HEIGHT:
            if not game_finished:
                if picture_count == len(asteroids):
                    final_message = "You win! All pictures taken."  
                else:
                    final_message = f"Game Over! Pictures taken: {picture_count}/{len(asteroids)}"
            game_finished = True

        if not game_finished:
            screen.blit(
                satellite_img,
                (x - satellite_img.get_width() // 2, y - satellite_img.get_height() // 2),
            )

    counter_text = font.render(
        f"Pictures: {picture_count}/{len(asteroids)}", True, (255, 255, 255)
    )
    screen.blit(counter_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    if game_finished:
        msg = font.render(final_message, True, (255, 255, 0))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        restart_msg = font.render("Press any key to restart.", True, (255, 255, 255))
        screen.blit(restart_msg, (WIDTH // 2 - restart_msg.get_width() // 2, HEIGHT // 2 + 40))

    pygame.display.flip()

pygame.quit()
sys.exit()
