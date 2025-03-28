import pygame
import math
import random
import sys
import os

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


# --- Helper Functions for RK4 ---
def acceleration(state, asteroids):
    x, y, _, _ = state
    ax, ay = 0, 0
    for asteroid in asteroids:
        ax_, ay_ = asteroid["pos"]
        dx = ax_ - x
        dy = ay_ - y
        r_sq = dx * dx + dy * dy
        if r_sq < 1:
            r_sq = 1
        r = math.sqrt(r_sq)
        a = G * asteroid["mass"] / r_sq
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
    canon_img = pygame.transform.scale(
        canon_img, (80, 80)
    )  # Slightly larger for the bigger screen

    satellite_img = pygame.image.load(
        os.path.join(os.path.dirname(__file__), "assets", "satellite.png")
    ).convert_alpha()
    satellite_img = pygame.transform.scale(satellite_img, (40, 40))

    # Load all four asteroid images
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

    # Load camera flash sound
    camera_flash_sound = pygame.mixer.Sound(
        os.path.join(os.path.dirname(__file__), "assets", "camera.wav")
    )
except Exception as e:
    print(
        "Error loading assets. Ensure all required images and sounds are in the correct folder."
    )
    sys.exit()


# --- Helper for Non-Overlapping Asteroids ---
def get_random_position_for_asteroid(size, existing_asteroids):
    max_attempts = 1000
    for _ in range(max_attempts):
        x = random.randint(
            WIDTH // 2 + size // 2 + EDGE_MARGIN, WIDTH - EDGE_MARGIN - size // 2
        )
        y = random.randint(EDGE_MARGIN + size // 2, HEIGHT - EDGE_MARGIN - size // 2)
        overlap = False
        for a in existing_asteroids:
            ax, ay = a["pos"]
            asize = a["size"]
            # Increase required separation by adding the satellite's width so it can fit between
            required_separation = (
                ((size + asize) // 2) + ASTEROID_BUFFER + satellite_img.get_width()
            )
            if math.hypot(x - ax, y - ay) < required_separation:
                overlap = True
                break
        if not overlap:
            return (x, y)
    return (x, y)


# --- Function to Initialize Asteroids ---
def init_asteroids():
    asteroids = []
    # Randomly select 2 asteroid images from the full list
    asteroid_imgs = random.sample(asteroid_imgs_full, 2)
    for img in asteroid_imgs:
        size = random.randint(80, 150)
        scaled_img = pygame.transform.scale(img, (size, size))
        pos = get_random_position_for_asteroid(size, asteroids)
        mass = (size * size) / 10  # Mass proportional to area
        asteroids.append(
            {
                "img": scaled_img,
                "pos": pos,
                "mass": mass,
                "pictured": False,
                "size": size,
            }
        )
    return asteroids


# --- Game Variables ---
asteroids = init_asteroids()
satellite_launched = False
satellite_state = None  # [x, y, vx, vy]
picture_count = 0

# To store the satellite's path (list of (x,y) tuples)
satellite_path = []

# Game state flags
game_finished = False  # Set when the satellite exits the screen or a collision occurs.
final_message = ""

# Font for messages
font = pygame.font.SysFont("Arial", 24)


def reset_game():
    global satellite_launched, satellite_state, asteroids, picture_count, game_finished, final_message, satellite_path
    satellite_launched = False
    satellite_state = None
    picture_count = 0
    asteroids = init_asteroids()
    game_finished = False
    final_message = ""
    satellite_path = []


# --- Main Loop ---
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Allow restart if game has finished and a key is pressed.
        if game_finished and event.type == pygame.KEYDOWN:
            reset_game()
        # Launch satellite only if game is not finished and not already launched.
        if (
            not game_finished
            and event.type == pygame.MOUSEBUTTONDOWN
            and not satellite_launched
        ):
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - CANON_POS[0]
            dy = mouse_y - CANON_POS[1]
            angle = math.atan2(dy, dx)
            speed = 150  # Adjust as needed
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            satellite_state = [CANON_POS[0], CANON_POS[1], vx, vy]
            satellite_launched = True

    # Draw background
    screen.blit(background_img, (0, 0))

    # Draw asteroids
    for asteroid in asteroids:
        x, y = asteroid["pos"]
        screen.blit(
            asteroid["img"],
            (
                x - asteroid["img"].get_width() // 2,
                y - asteroid["img"].get_height() // 2,
            ),
        )

    # Draw canon platform (if you still want that drawn)
    platform_width = 120
    platform_height = 10
    platform_x = CANON_POS[0] - platform_width // 2
    platform_y = CANON_POS[1] + (canon_img.get_height() // 2) - 5
    platform_rect = (platform_x, platform_y, platform_width, platform_height)
    pygame.draw.rect(screen, (100, 100, 100), platform_rect)

    # Draw canon (rotated to point to mouse)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - CANON_POS[0]
    dy = mouse_y - CANON_POS[1]
    angle_deg = math.degrees(math.atan2(-dy, dx))
    rotated_canon = pygame.transform.rotate(canon_img, angle_deg)
    canon_rect = rotated_canon.get_rect(center=CANON_POS)
    screen.blit(rotated_canon, canon_rect)

    # Always draw the path, even after the game ends
    if len(satellite_path) > 1:
        pygame.draw.lines(screen, GEORGIA_TECH_GOLD, False, satellite_path, 4)

    # Display picture counter and satellite info on screen
    if satellite_state:
        x, y, vx, vy = satellite_state
        info_text = font.render(
            f"Pictures: {picture_count}/{len(asteroids)}  |  x: {x:.1f}, y: {y:.1f}, vx: {vx:.1f}, vy: {-vy:.1f}",
            True,
            (255, 255, 255),
        )
        screen.blit(info_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    # Only update simulation if the game is not finished
    if not game_finished and satellite_launched and satellite_state:
        satellite_state = rk4_step(satellite_state, DT, asteroids)
        x, y, vx, vy = satellite_state

        # Only start tracking the path after the satellite has moved 50 pixels from launch
        if math.hypot(x - CANON_POS[0], y - CANON_POS[1]) > 50:
            satellite_path.append((x, y))

        # Collision detection: if the satellite collides with an asteroid, game over immediately.
        satellite_radius = satellite_img.get_width() // 2
        for asteroid in asteroids:
            ax, ay = asteroid["pos"]
            asteroid_radius = asteroid["size"] // 2
            distance = math.hypot(x - ax, y - ay)
            if distance < (satellite_radius + asteroid_radius):
                final_message = "Collision! You lost."
                game_finished = True
                break

            # Picture condition: if satellite gets close enough to take a picture
            picture_threshold = satellite_radius + asteroid_radius + PICTURE_MARGIN
            if distance < picture_threshold and not asteroid["pictured"]:
                asteroid["pictured"] = True
                picture_count += 1
                camera_flash_sound.play()

        # Check if satellite goes off-screen.
        if x < 0 or x > WIDTH or y < 0 or y > HEIGHT:
            # Game ends only upon exit.
            if not game_finished:
                if picture_count == len(asteroids):
                    final_message = "You win! All pictures taken."
                else:
                    final_message = (
                        f"Game Over! Pictures taken: {picture_count}/{len(asteroids)}"
                    )
            game_finished = True

        # Draw satellite if still on screen and game is not finished
        if not game_finished:
            screen.blit(
                satellite_img,
                (
                    x - satellite_img.get_width() // 2,
                    y - satellite_img.get_height() // 2,
                ),
            )

    # Display picture counter on screen
    counter_text = font.render(
        f"Pictures: {picture_count}/{len(asteroids)}", True, (255, 255, 255)
    )
    screen.blit(counter_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    # If the game is finished, display the final message.
    if game_finished:
        msg = font.render(final_message, True, (255, 255, 0))
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
        restart_msg = font.render("Press any key to restart.", True, (255, 255, 255))
        screen.blit(
            restart_msg,
            (WIDTH // 2 - restart_msg.get_width() // 2, HEIGHT // 2 + 40),
        )

    pygame.display.flip()

pygame.quit()
sys.exit()