import pygame
import math
import sys
import os

# ----- Simulation parameters -----
G = 0.1  # gravitational constant
# Masses
M_large = 100000
M_small = 10
rocket_mass = 1

# Radii (used for collision detection and drawing)
radius_large = 10
radius_small = 10
radius_rocket = 1

# ----- Full-Screen Setup -----
pygame.init()
infoObject = pygame.display.Info()
WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h

# Real time duration for simulation in seconds
REAL_TIME_SIM_DURATION = 60  # seconds

# Integration settings (fixed simulation timestep)
SUBSTEPS = 80

# Fixed time scale multiplier (set to 6)
time_scale = 6

# Rocket image orientation offset (in degrees)
rocket_offset = 0

# ----- Bottom UI Buttons (Toggle and Spawn) -----
button_margin = 10
button_width = 80
button_height = 40
num_buttons = 6  # 1 toggle + 5 spawn buttons
total_ui_width = num_buttons * button_width + (num_buttons + 1) * button_margin
ui_y = HEIGHT - button_height - button_margin
ui_buttons = []  # list of (rect, label)
start_x = (WIDTH - total_ui_width) / 2 + button_margin
labels = ["LP", "L1", "L2", "L3", "L4", "L5"]
for i in range(num_buttons):
    rect = pygame.Rect(
        start_x + i * (button_width + button_margin), ui_y, button_width, button_height
    )
    ui_buttons.append((rect, labels[i]))

# Initially, Lagrange points are hidden.
show_lagrange = False

# Define an exit button rectangle (top right)
exit_button_rect = pygame.Rect(WIDTH - 50, 10, 40, 40)

# ----- Game States -----
WAITING_FOR_CLICK = 0
SIMULATING = 1
GAME_OVER = 2
game_state = WAITING_FOR_CLICK

# ----- Global variables for rocket spawn, trail, and survival tracking -----
spawn_point = None  # Where the rocket was spawned
rocket_trail = []  # List of tuples (sim_time, position)
trail_lifetime = 1500  # seconds

# --- Revolution tracking variables for orbital period calculation ---
rocket_angle_total = 0
rocket_angle_prev = None
rocket_revolutions = 0
revolution_times = []  # List of orbital periods (in simulation seconds)
last_revolution_time = None

# Track off-screen time in simulation seconds.
rocket_offscreen_time = 0

# Real-world timer for win condition.
real_start_time = None

# ----- Pygame Display Setup, Clock, and Font -----
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Lagrange Points Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

# ----- Load Images -----
assets_dir = os.path.join(os.path.dirname(__file__), "Assets")
background_img = pygame.image.load(os.path.join(assets_dir, "space.png")).convert()
planet_img = pygame.image.load(os.path.join(assets_dir, "planet.png")).convert_alpha()
moon_img = pygame.image.load(os.path.join(assets_dir, "moon.png")).convert_alpha()
rocket_img_orig = pygame.image.load(
    os.path.join(assets_dir, "rocket.png")
).convert_alpha()

planet_img = pygame.transform.scale(planet_img, (40, 40))
moon_img = pygame.transform.scale(moon_img, (20, 20))
rocket_img_orig = pygame.transform.scale(rocket_img_orig, (15, 30))


# --- Revised Lagrange Point Calculation using analytical formulas ---
def reset_game():
    global pos_large, pos_small, COM, omega, vel_large, vel_small, vel_large_half, vel_small_half
    global sim_time, rocket_pos, rocket_vel, rocket_vel_half, lagrange_points, TOTAL_SIM_TIME
    global frame_dt, sub_dt, game_state, result_text, rocket_trail
    global rocket_angle_prev, rocket_angle_total, rocket_revolutions, revolution_times, last_revolution_time
    global rocket_offscreen_time, real_start_time, show_lagrange

    show_lagrange = False

    # In the rotating frame, set COM at the center.
    COM = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)
    d = 420  # separation between bodies

    total_mass = M_large + M_small
    offset_large = (M_small / total_mass) * d
    offset_small = (M_large / total_mass) * d
    pos_large = COM - pygame.math.Vector2(offset_large, 0)
    pos_small = COM + pygame.math.Vector2(offset_small, 0)

    # Angular velocity for circular orbit.
    omega = math.sqrt(G * total_mass / (d**3))

    # Set circular orbit velocities about COM.
    r_large = pos_large - COM
    r_small = pos_small - COM
    if r_large.length() != 0:
        vel_large = pygame.math.Vector2(-r_large.y, r_large.x).normalize() * (
            omega * r_large.length()
        )
    else:
        vel_large = pygame.math.Vector2(0, 0)
    if r_small.length() != 0:
        vel_small = pygame.math.Vector2(-r_small.y, r_small.x).normalize() * (
            omega * r_small.length()
        )
    else:
        vel_small = pygame.math.Vector2(0, 0)

    # --- Compute collinear Lagrange points using analytical formulas ---
    b = M_small / total_mass
    c = M_large / total_mass
    L1_offset = d * (1 - (b / 3) ** (1 / 3))
    L2_offset = d * (1 + (b / 3) ** (1 / 3))
    L3_offset = -d * (1 + b ** (5 / 12))
    L1 = COM + pygame.math.Vector2(L1_offset, 0)
    L2 = COM + pygame.math.Vector2(L2_offset, 0)
    L3 = COM + pygame.math.Vector2(L3_offset, 0)

    # Triangular Lagrange points (L4 and L5) via equilateral triangle construction.
    L4 = COM + pygame.math.Vector2(d / 2 * (c - b), d * math.sqrt(3) / 2)
    L5 = COM + pygame.math.Vector2(d / 2 * (c - b), -d * math.sqrt(3) / 2)

    lagrange_points = [L1, L2, L3, L4, L5]

    # Set initial half-step velocities.
    vel_large_half = vel_large.copy()
    vel_small_half = vel_small.copy()

    # Determine orbital period and total simulation time.
    orbital_period = 2 * math.pi / omega
    TOTAL_SIM_TIME = 10 * orbital_period
    frames = REAL_TIME_SIM_DURATION * 60
    frame_dt = TOTAL_SIM_TIME / frames
    sub_dt = frame_dt / SUBSTEPS

    sim_time = 0
    rocket_pos = None
    rocket_vel = None
    rocket_vel_half = None
    rocket_trail = []
    spawn_point = None

    # Reset revolution tracking variables.
    rocket_angle_total = 0
    rocket_angle_prev = None
    rocket_revolutions = 0
    revolution_times = []
    last_revolution_time = None

    # Reset off-screen timer.
    rocket_offscreen_time = 0

    # Reset real-world timer.
    real_start_time = None

    game_state = WAITING_FOR_CLICK
    result_text = ""


reset_game()


def gravitational_acceleration(pos, other_pos, other_mass):
    r_vec = other_pos - pos
    r = r_vec.length()
    if r == 0:
        return pygame.math.Vector2(0, 0)
    return G * other_mass / (r**2) * r_vec.normalize()


def leapfrog_update(pos, vel_half, acceleration, dt):
    new_vel_half = vel_half + acceleration * dt
    new_pos = pos + new_vel_half * dt
    return new_pos, new_vel_half


def draw_buttons():
    # Draw bottom UI buttons only if waiting for spawn.
    if game_state == WAITING_FOR_CLICK:
        for rect, label in ui_buttons:
            if label == "LP":
                color = (0, 200, 0) if show_lagrange else (100, 100, 100)
            else:
                color = (0, 0, 200)
            pygame.draw.rect(screen, color, rect)
            text = font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)


def point_in_ui(pos):
    if exit_button_rect.collidepoint(pos):
        return True
    for rect, _ in ui_buttons:
        if rect.collidepoint(pos):
            return True
    return False


# Prepare bottom UI buttons.
ui_buttons = []
start_x = (WIDTH - total_ui_width) / 2 + button_margin
for i in range(num_buttons):
    rect = pygame.Rect(
        start_x + i * (button_width + button_margin), ui_y, button_width, button_height
    )
    ui_buttons.append((rect, labels[i]))

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if exit_button_rect.collidepoint(event.pos):
                running = False
                break

            # Process UI clicks.
            if point_in_ui(event.pos):
                for rect, label in ui_buttons:
                    if rect.collidepoint(event.pos):
                        if label == "LP":
                            show_lagrange = not show_lagrange
                        else:
                            idx = int(label[1]) - 1  # L1 -> index 0, etc.
                            rocket_pos = lagrange_points[idx].copy()
                            spawn_point = rocket_pos.copy()
                            r_rocket = rocket_pos - COM
                            if r_rocket.length() != 0:
                                rocket_vel = pygame.math.Vector2(
                                    -r_rocket.y, r_rocket.x
                                ).normalize() * (omega * r_rocket.length())
                            else:
                                rocket_vel = pygame.math.Vector2(0, 0)
                            rocket_vel_half = rocket_vel.copy()
                            rocket_trail = [(sim_time, rocket_pos.copy())]
                            rocket_angle_prev = math.atan2(
                                (rocket_pos - pos_large).y, (rocket_pos - pos_large).x
                            )
                            rocket_angle_total = 0
                            rocket_revolutions = 0
                            revolution_times = []
                            last_revolution_time = None
                            rocket_offscreen_time = 0
                            real_start_time = pygame.time.get_ticks()
                            game_state = SIMULATING
                continue

            # Free-click spawn if not in UI.
            if game_state == WAITING_FOR_CLICK:
                rocket_pos = pygame.math.Vector2(event.pos)
                spawn_point = rocket_pos.copy()
                r_rocket = rocket_pos - COM
                if r_rocket.length() != 0:
                    rocket_vel = pygame.math.Vector2(
                        -r_rocket.y, r_rocket.x
                    ).normalize() * (omega * r_rocket.length())
                else:
                    rocket_vel = pygame.math.Vector2(0, 0)
                rocket_vel_half = rocket_vel.copy()
                rocket_trail = [(sim_time, rocket_pos.copy())]
                rocket_angle_prev = math.atan2(
                    (rocket_pos - pos_large).y, (rocket_pos - pos_large).x
                )
                rocket_angle_total = 0
                rocket_revolutions = 0
                revolution_times = []
                last_revolution_time = None
                rocket_offscreen_time = 0
                real_start_time = pygame.time.get_ticks()
                game_state = SIMULATING

        elif event.type == pygame.KEYDOWN and game_state == GAME_OVER:
            if event.key == pygame.K_r:
                reset_game()

    screen.blit(pygame.transform.scale(background_img, (WIDTH, HEIGHT)), (0, 0))
    pygame.draw.rect(screen, (200, 0, 0), exit_button_rect)
    exit_text = font.render("X", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
    screen.blit(exit_text, exit_text_rect)

    if game_state == WAITING_FOR_CLICK:
        draw_buttons()

    if show_lagrange:
        for pt in lagrange_points:
            pygame.draw.circle(screen, (255, 255, 0), (int(pt.x), int(pt.y)), 5)

    planet_rect = planet_img.get_rect(center=(int(pos_large.x), int(pos_large.y)))
    screen.blit(planet_img, planet_rect)
    moon_rect = moon_img.get_rect(center=(int(pos_small.x), int(pos_small.y)))
    screen.blit(moon_img, moon_rect)

    if rocket_pos and rocket_vel_half is not None:
        if rocket_vel_half.length() > 0:
            angle = math.degrees(math.atan2(rocket_vel_half.y, rocket_vel_half.x))
        else:
            angle = 0
        rotated_rocket = pygame.transform.rotate(
            rocket_img_orig, -angle + rocket_offset
        )
        rocket_rect = rotated_rocket.get_rect(
            center=(int(rocket_pos.x), int(rocket_pos.y))
        )
        screen.blit(rotated_rocket, rocket_rect)
        if spawn_point is not None:
            pygame.draw.circle(
                screen, (0, 0, 255), (int(spawn_point.x), int(spawn_point.y)), 5
            )
        rocket_trail = [
            (t, pos) for (t, pos) in rocket_trail if sim_time - t <= trail_lifetime
        ]
        if len(rocket_trail) > 1:
            pygame.draw.lines(
                screen,
                (255, 100, 100),
                False,
                [(int(p.x), int(p.y)) for (t, p) in rocket_trail],
                2,
            )

    time_text = font.render(f"Simulated Time: {sim_time:.1f} s", True, (255, 255, 255))
    screen.blit(time_text, (20, HEIGHT - 60))

    if game_state == WAITING_FOR_CLICK:
        instr_text = font.render(
            "Click to spawn the rocket or use the buttons below", True, (255, 255, 255)
        )
        screen.blit(instr_text, (20, 20))
    if game_state == GAME_OVER:
        result_surface = font.render(result_text, True, (255, 255, 255))
        restart_surface = font.render("Press 'R' to play again.", True, (255, 255, 255))
        screen.blit(
            result_surface,
            (WIDTH // 2 - result_surface.get_width() // 2, HEIGHT // 2 - 20),
        )
        screen.blit(
            restart_surface,
            (WIDTH // 2 - restart_surface.get_width() // 2, HEIGHT // 2 + 10),
        )

    if game_state == SIMULATING:
        for _ in range(SUBSTEPS):
            dt = sub_dt * time_scale
            acc_large = gravitational_acceleration(pos_large, pos_small, M_small)
            pos_large, vel_large_half = leapfrog_update(
                pos_large, vel_large_half, acc_large, dt
            )
            acc_small = gravitational_acceleration(pos_small, pos_large, M_large)
            pos_small, vel_small_half = leapfrog_update(
                pos_small, vel_small_half, acc_small, dt
            )
            acc_rocket = pygame.math.Vector2(0, 0)
            acc_rocket += gravitational_acceleration(rocket_pos, pos_large, M_large)
            acc_rocket += gravitational_acceleration(rocket_pos, pos_small, M_small)
            rocket_pos, rocket_vel_half = leapfrog_update(
                rocket_pos, rocket_vel_half, acc_rocket, dt
            )
            rocket_trail.append((sim_time, rocket_pos.copy()))
            sim_time += dt

            # --- Update Revolution Tracking for Orbital Period ---
            current_angle = math.atan2(
                (rocket_pos - pos_large).y, (rocket_pos - pos_large).x
            )
            if rocket_angle_prev is not None:
                delta_angle = abs(current_angle - rocket_angle_prev)
                if delta_angle > math.pi:
                    delta_angle = 2 * math.pi - delta_angle
                rocket_angle_total += delta_angle
                new_rev_count = int(rocket_angle_total // (2 * math.pi))
                if new_rev_count > rocket_revolutions:
                    if last_revolution_time is not None:
                        revolution_times.append(sim_time - last_revolution_time)
                    last_revolution_time = sim_time
                rocket_revolutions = new_rev_count
            rocket_angle_prev = current_angle

            # --- Update Off-Screen Timer ---
            if (
                rocket_pos.x < 0
                or rocket_pos.x > WIDTH
                or rocket_pos.y < 0
                or rocket_pos.y > HEIGHT
            ):
                rocket_offscreen_time += dt
            else:
                rocket_offscreen_time = 0

            if rocket_offscreen_time > 300:
                game_state = GAME_OVER
                result_text = "You Lose! Your rocket was lost to space."
                break

            # --- Check for Collision ---
            if (rocket_pos - pos_large).length() < (radius_large + radius_rocket) or (
                rocket_pos - pos_small
            ).length() < (radius_small + radius_rocket):
                game_state = GAME_OVER
                result_text = "Game Over! Rocket collided with a body."
                break

            # --- Check Win Condition: Surviving 10 Real-World Seconds ---
            if real_start_time is not None:
                elapsed_real = pygame.time.get_ticks() - real_start_time
                if elapsed_real >= 20000:
                    game_state = GAME_OVER
                    if revolution_times:
                        mean_period = sum(revolution_times) / len(revolution_times)
                        variance = sum(
                            (t - mean_period) ** 2 for t in revolution_times
                        ) / len(revolution_times)
                        std = math.sqrt(variance)
                        result_text = f"You Win! Period standard deviation: {std:.3f} s"
                    else:
                        result_text = (
                            "You Win! Not enough data for period standard deviation."
                        )
                    break

    pygame.display.flip()

pygame.quit()
sys.exit()