import pygame
import math
import random
import sys
import os
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

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

# --- Load images and sounds ---
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
    # Load canon fire and crash sounds
    fire_sound = pygame.mixer.Sound(
        os.path.join(os.path.dirname(__file__), "assets", "fire.flac")
    )
    crash_sound = pygame.mixer.Sound(
        os.path.join(os.path.dirname(__file__), "assets", "crash.flac")
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
        tooFar = False
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
            elif math.hypot(x - ax, y - ay) > (10 * satellite_img.get_width()):
                tooFar = True
                break
        if not overlap:
            if not tooFar:
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
satellite_path = []  # To store the satellite's path as (x,y) tuples

# Data for plots
simulation_time = 0.0
position_times = []  # Log time for each recorded position
accel_data = []  # (time, total_acceleration)
energy_data = []  # (time, KE, PE, ME)

# Game state flags
game_finished = False  # True when satellite exits screen or collides
final_message = ""

# Font for messages
font = pygame.font.SysFont("Arial", 24)


# --- Instructions Screen ---
def show_instructions():
    screen.blit(background_img, (0, 0))
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    text_font = pygame.font.SysFont("Arial", 24)

    instructions = [
        "Welcome to the Astrographer!",
        "",
        "Instructions:",
        "- Click anywhere to launch the satellite from the canon.",
        "- Aim to take pictures of asteroids by flying near them.",
        "- Avoid collisions with asteroids.",
        "- The mission ends if you go off-screen or collide.",
        "- Your path is drawn on the screen.",
        "",
        "Press any key to begin...",
    ]

    for i, line in enumerate(instructions):
        chosen_font = title_font if i == 0 else text_font
        text_surface = chosen_font.render(line, True, (255, 255, 255))
        screen.blit(
            text_surface, (WIDTH // 2 - text_surface.get_width() // 2, 100 + i * 40)
        )

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False


# Display instructions before starting the game
show_instructions()


def reset_game():
    global satellite_launched, satellite_state, asteroids, picture_count, game_finished, final_message, satellite_path, simulation_time, position_times, accel_data, energy_data
    satellite_launched = False
    satellite_state = None
    picture_count = 0
    asteroids = init_asteroids()
    game_finished = False
    final_message = ""
    satellite_path = []
    simulation_time = 0.0
    position_times = []
    accel_data = []
    energy_data = []


# --- Main Game Loop ---
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Restart if game is finished and any key is pressed.
        if game_finished and event.type == pygame.KEYDOWN:
            reset_game()
        # Launch satellite if game is active and not launched yet.
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
            fire_sound.play()  # Play canon fire sound

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

    # Draw canon platform
    platform_width = 120
    platform_height = 10
    platform_x = CANON_POS[0] - platform_width // 2
    platform_y = CANON_POS[1] + (canon_img.get_height() // 2) - 5
    pygame.draw.rect(
        screen,
        (100, 100, 100),
        (platform_x, platform_y, platform_width, platform_height),
    )

    # Draw canon (rotated to face mouse pointer)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    dx = mouse_x - CANON_POS[0]
    dy = mouse_y - CANON_POS[1]
    angle_deg = math.degrees(math.atan2(-dy, dx))
    rotated_canon = pygame.transform.rotate(canon_img, angle_deg)
    canon_rect = rotated_canon.get_rect(center=CANON_POS)
    screen.blit(rotated_canon, canon_rect)

    # Draw the satellite's path (even after game over)
    if len(satellite_path) > 1:
        pygame.draw.lines(screen, GEORGIA_TECH_GOLD, False, satellite_path, 4)

    # Display picture counter and satellite info
    if satellite_state:
        x, y, vx, vy = satellite_state
        info_text = font.render(
            f"Pictures: {picture_count}/{len(asteroids)}  |  x: {x:.1f}, y: {y:.1f}, vx: {vx:.1f}, vy: {-vy:.1f}",
            True,
            (255, 255, 255),
        )
        screen.blit(info_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    # Update simulation if game is active.
    if not game_finished and satellite_launched and satellite_state:
        # Update simulation time and state using RK4 integration.
        simulation_time += DT
        satellite_state = rk4_step(satellite_state, DT, asteroids)
        x, y, vx, vy = satellite_state

        # Start tracking the path after 50 pixels from launch.
        if math.hypot(x - CANON_POS[0], y - CANON_POS[1]) > 50:
            satellite_path.append((x, y))
            position_times.append(simulation_time)

        # Log acceleration
        ax, ay = acceleration(satellite_state, asteroids)
        total_accel = math.sqrt(ax**2 + ay**2)
        accel_data.append((simulation_time, total_accel))

        # Energy calculations:
        speed_sq = vx**2 + vy**2
        KE = 0.5 * speed_sq  # Kinetic Energy (mass assumed 1)
        PE = 0
        for asteroid in asteroids:
            ax_a, ay_a = asteroid["pos"]
            r = math.hypot(x - ax_a, y - ay_a)
            r = max(r, 1)
            PE -= G * asteroid["mass"] / r
        ME = KE + PE
        energy_data.append((simulation_time, KE, PE, ME))

        # Collision detection and picture conditions.
        satellite_radius = satellite_img.get_width() // 2
        for asteroid in asteroids:
            ax_a, ay_a = asteroid["pos"]
            asteroid_radius = asteroid["size"] // 2
            distance = math.hypot(x - ax_a, y - ay_a)
            # Collision (ends game)
            if distance < (satellite_radius + asteroid_radius):
                final_message = "Collision! You lost."
                game_finished = True
                crash_sound.play()  # Play crash sound on collision
                break
            # Picture condition: if within threshold and not yet taken.
            picture_threshold = satellite_radius + asteroid_radius + PICTURE_MARGIN
            if distance < picture_threshold and not asteroid["pictured"]:
                asteroid["pictured"] = True
                picture_count += 1
                camera_flash_sound.play()

        # End game if satellite goes off-screen.
        if x < 0 or x > WIDTH or y < 0 or y > HEIGHT:
            if not game_finished:
                if picture_count == len(asteroids):
                    final_message = "You win! All pictures taken."
                else:
                    final_message = (
                        f"Game Over! Pictures taken: {picture_count}/{len(asteroids)}"
                    )
            game_finished = True

        # Draw the satellite if still within bounds.
        if not game_finished:
            screen.blit(
                satellite_img,
                (
                    x - satellite_img.get_width() // 2,
                    y - satellite_img.get_height() // 2,
                ),
            )

    # Display picture counter overlay.
    counter_text = font.render(
        f"Pictures: {picture_count}/{len(asteroids)}", True, (255, 255, 255)
    )
    screen.blit(counter_text, (EDGE_MARGIN, EDGE_MARGIN // 2))

    # If game is finished, show final message and prompt to restart.
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

# ------------------------------------------------------------------
# Generate plots in separate figures after quitting the game.
# ------------------------------------------------------------------

# 1. 2D Trajectory Plot (x vs. y) with color indicating time progression.
#    We flip the y-values so that the initial y position is 0.
if satellite_path:
    xs, ys = zip(*satellite_path)
    # Convert the y-values by flipping them relative to the canon position.
    # New y value = CANON_POS[1] - original y.
    ys_flipped = [CANON_POS[1] - y for y in ys]
    # Use logged position_times if available; otherwise generate linearly.
    if len(position_times) == len(satellite_path):
        times = np.array(position_times)
    else:
        times = np.linspace(0, simulation_time, len(satellite_path))

    # Create segments for the trajectory.
    points = np.array([xs, ys_flipped]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    fig1, ax1 = plt.subplots()
    lc = LineCollection(
        segments, cmap="viridis", norm=plt.Normalize(times.min(), times.max())
    )
    lc.set_array(times[:-1])
    lc.set_linewidth(2)
    ax1.add_collection(lc)
    ax1.set_xlim(min(xs), max(xs))
    ax1.set_ylim(min(ys_flipped), max(ys_flipped))
    ax1.set_xlabel("X Position")
    ax1.set_ylabel("Y Position")
    ax1.set_title("Satellite Trajectory")
    fig1.colorbar(lc, ax=ax1, label="Time (s)")

# 2. Plot of Acceleration Over Time
if accel_data:
    times_a, accels = zip(*accel_data)
    fig2, ax2 = plt.subplots()
    ax2.plot(times_a, accels, color="red")
    ax2.set_title("Acceleration Over Time")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Acceleration")
    ax2.grid(True)

# 3. Plot of Kinetic, Potential, and Mechanical Energy Over Time
if energy_data:
    times_e, KE_vals, PE_vals, ME_vals = zip(*energy_data)
    fig3, ax3 = plt.subplots()
    ax3.plot(times_e, KE_vals, label="Kinetic")
    ax3.plot(times_e, PE_vals, label="Potential")
    ax3.plot(times_e, ME_vals, label="Mechanical")
    ax3.set_title("Energy Over Time")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Energy")
    ax3.legend()
    ax3.grid(True)

# Display all figures simultaneously.
plt.show()

sys.exit()
