import math
import pygame
import sys
import os
import matplotlib.pyplot as plt
from game_buttons import Button

# Initialize Pygame
pygame.init()
# Remove interactive mode so that plots remain open later
# plt.ioff()
# Enable interactive mode for Matplotlib
plt.ion()
pygame.font.init()
font = pygame.font.SysFont('Arial', 30)

# Screen parameters
WIDTH, HEIGHT = 1400, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbit Game: RK4 vs Verlet")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
DARKGRAY = (100, 100, 100)
LEGEND_BG = (20, 20, 20, 180)

# Load assets
dir_path = os.path.dirname(__file__)
assets_dir = os.path.join(dir_path, "Assets")
background_img = pygame.image.load(os.path.join(assets_dir, "space.png")).convert()
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

planet_img = pygame.image.load(os.path.join(assets_dir, "planet.png")).convert_alpha()
rocket_img = pygame.image.load(os.path.join(assets_dir, "rocket.png")).convert_alpha()
planet_img = pygame.transform.scale(planet_img, (150, 150))
rocket_img = pygame.transform.scale(rocket_img, (15, 30))

# Planet parameters
planet_rect = planet_img.get_rect()
planet_radius = planet_rect.width // 2
planet_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
launch_pos = planet_pos + pygame.Vector2(0, -(planet_radius + 10))

# Physics constants
GM = 500000
# Time step
dt = 0.1
REVOLUTIONS_TO_WIN = 20


# Helper functions
def gravitational_acceleration(pos):
    r_vec = pos - planet_pos
    r = r_vec.length()
    if r == 0:
        return pygame.Vector2(0, 0)
    return -GM * r_vec / (r**3)


def rk4_update(pos, vel, dt):
    a1 = gravitational_acceleration(pos)
    k1v, k1p = a1, vel
    a2 = gravitational_acceleration(pos + 0.5 * dt * k1p)
    k2v, k2p = a2, vel + 0.5 * dt * k1v
    a3 = gravitational_acceleration(pos + 0.5 * dt * k2p)
    k3v, k3p = a3, vel + 0.5 * dt * k2v
    a4 = gravitational_acceleration(pos + dt * k3p)
    k4v, k4p = a4, vel + dt * k3v

    new_vel = vel + dt * (k1v + 2 * k2v + 2 * k3v + k4v) / 6
    new_pos = pos + dt * (k1p + 2 * k2p + 2 * k3p + k4p) / 6
    return new_pos, new_vel

def impulse_burn(rocket, dv):
    if hasattr(rocket, "vel"):
        # RK4: directly adjust velocity vector
        direction = rocket.vel.normalize()
        rocket.vel += direction * dv
    else:
        # Verlet: estimate velocity and update prev_pos accordingly
        v = (rocket.pos - rocket.prev_pos) / dt
        direction = v.normalize()
        new_v = v + direction * dv
        rocket.prev_pos = rocket.pos - new_v * dt

# Rocket classes
class RKRocket:
    def __init__(self, pos, vel):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.trail = []
        self.prev_angle = (self.pos - planet_pos).angle_to(pygame.Vector2(1, 0))
        self.total_angle = 0
        self.status = "In-Orbit"
        # Tracking
        self.time = 0.0
        self.energies = {"t": [], "kin": [], "pot": [], "mech": []}
        self.speed = self.vel.length()
        self.acc = gravitational_acceleration(self.pos)

    def update(self):
        self.pos, self.vel = rk4_update(self.pos, self.vel, dt)
        self.trail.append(self.pos.copy())
        angle = (self.pos - planet_pos).angle_to(pygame.Vector2(1, 0))
        diff = (angle - self.prev_angle + 180) % 360 - 180
        self.total_angle += diff
        self.prev_angle = angle
        self.time += dt
        self.speed = self.vel.length()
        self.acc = gravitational_acceleration(self.pos)
        r = (self.pos - planet_pos).length()
        kin = 0.5 * self.speed**2
        pot = -GM / r
        mech = kin + pot
        self.energies["t"].append(self.time)
        self.energies["kin"].append(kin)
        self.energies["pot"].append(pot)
        self.energies["mech"].append(mech)

    def revolutions(self):
        return abs(self.total_angle) / 360


class VerletRocket:
    def __init__(self, pos, vel):
        self.pos = pygame.Vector2(pos)
        # Improved initialization: add half-acceleration term for better accuracy.
        self.prev_pos = (
            self.pos
            - pygame.Vector2(vel) * dt
            + 0.5 * gravitational_acceleration(self.pos) * dt**2
        )
        self.trail = []
        self.prev_angle = (self.pos - planet_pos).angle_to(pygame.Vector2(1, 0))
        self.total_angle = 0
        self.status = "In-Orbit"
        self.time = 0.0
        self.energies = {"t": [], "kin": [], "pot": [], "mech": []}
        self.speed = pygame.Vector2(vel).length()
        self.acc = gravitational_acceleration(self.pos)

    def update(self):
        a = gravitational_acceleration(self.pos)
        new_pos = 2 * self.pos - self.prev_pos + a * dt**2
        # Use central difference to compute velocity:
        v_vec = (new_pos - self.prev_pos) / (2 * dt)
        self.prev_pos = self.pos
        self.pos = new_pos
        self.trail.append(self.pos.copy())
        angle = (self.pos - planet_pos).angle_to(pygame.Vector2(1, 0))
        diff = (angle - self.prev_angle + 180) % 360 - 180
        self.total_angle += diff
        self.prev_angle = angle
        self.time += dt
        self.speed = v_vec.length()
        self.acc = gravitational_acceleration(self.pos)
        r = (self.pos - planet_pos).length()
        kin = 0.5 * self.speed**2
        pot = -GM / r
        mech = kin + pot
        self.energies["t"].append(self.time)
        self.energies["kin"].append(kin)
        self.energies["pot"].append(pot)
        self.energies["mech"].append(mech)

    def revolutions(self):
        return abs(self.total_angle) / 360


# Main loop
def main():
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 18)

    # New: Instructions screen
    show_instructions = True
    instructions = [
        "Welcome to the Rocket Rumble!",
        "",
        "Instructions:",
        "1. Aim the rocket by moving the mouse.",
        "2. Click the left mouse button to launch.",
        "3. Maintain an orbit for 150 revolutions to win.",
        "4. Press 'R' at any time to restart.",
        "",
        "Press any key or click to continue...",
    ]

    while show_instructions:
        screen.blit(background_img, (0, 0))
        # Draw planet in background for context
        screen.blit(planet_img, planet_img.get_rect(center=planet_pos))
        y_offset = HEIGHT // 3
        for line in instructions:
            text_surf = font.render(line, True, WHITE)
            text_rect = text_surf.get_rect(center=(WIDTH // 2, y_offset))
            screen.blit(text_surf, text_rect)
            y_offset += 30

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                show_instructions = False

    # Game states
    launch_mode = True
    launched = False
    game_over = False
    win = False

    rkrocket = None
    vrocket = None

    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
    launch_vector = pygame.Vector2(0, 0)
    speed_factor = 0.5

    # button1 = Button(50, 50, 200, 50, "Impulse 1", WHITE, (100, 255, 100))
    # button2 = Button(50, 120, 200, 50, "Impulse 2", WHITE, (255, 100, 100))

    while True:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game state
                    launch_mode = True
                    launched = False
                    game_over = False
                    win = False
                    rkrocket = None
                    vrocket = None
                    plt.close("all")
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_click = True
            
            if launch_mode:
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.Vector2(event.pos)
                    launch_vector = mouse_pos - launch_pos
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    vel = launch_vector * speed_factor
                    rkrocket = RKRocket(launch_pos, vel)
                    vrocket = VerletRocket(launch_pos, vel)
                    launch_mode = False
                    launched = True

        # Clear screen
        screen.blit(background_img, (0, 0))
        screen.blit(planet_img, planet_img.get_rect(center=planet_pos))

        if launch_mode:
            # Draw launch interface
            rocket_rect = rocket_img.get_rect(center=launch_pos)
            screen.blit(rocket_img, rocket_rect)
            pygame.draw.line(screen, WHITE, launch_pos, mouse_pos, 2)
            instr = font.render("Aim with mouse. Click to launch.", True, WHITE)
            screen.blit(instr, (50, 20))
        elif launched and not game_over:
            # Physics updates
            if rkrocket.status == "In-Orbit":
                rkrocket.update()
            if vrocket.status == "In-Orbit":
                vrocket.update()

            # Draw trails
            for rocket, color in [(rkrocket, RED), (vrocket, BLUE)]:
                if len(rocket.trail) > 1:
                    pygame.draw.lines(
                        screen,
                        color,
                        False,
                        [(int(p.x), int(p.y)) for p in rocket.trail],
                        2,
                    )

            # Draw rockets
            def draw_rocket(rocket):
                # For RK4 the velocity is directly stored;
                # For Verlet, we approximate the instantaneous velocity using central difference.
                if hasattr(rocket, "vel"):
                    velocity = rocket.vel
                else:
                    velocity = (rocket.pos - rocket.prev_pos) / (2 * dt)
                angle = velocity.angle_to(pygame.Vector2(1, 0))
                rotated = pygame.transform.rotate(rocket_img, -angle)
                rect = rotated.get_rect(center=(int(rocket.pos.x), int(rocket.pos.y)))
                screen.blit(rotated, rect)

            if rkrocket.status == "In-Orbit":
                draw_rocket(rkrocket)
            if vrocket.status == "In-Orbit":
                draw_rocket(vrocket)

            # Status checks
            for rocket in [rkrocket, vrocket]:
                if rocket.status == "In-Orbit":
                    if not (0 <= rocket.pos.x <= WIDTH and 0 <= rocket.pos.y <= HEIGHT):
                        rocket.status = "Lost"
                    elif (rocket.pos - planet_pos).length() < planet_radius:
                        rocket.status = "Collided"
                    elif rocket.revolutions() >= REVOLUTIONS_TO_WIN:
                        game_over = True
                        win = True
            
            if rkrocket.status != "In-Orbit" and vrocket.status != "In-Orbit":
                game_over = True
                win = False

            # # Draw buttons
            # button1.draw(screen)
            # button2.draw(screen)
            
            # # Button interactions
            # button1.check_hover(mouse_pos)
            # button2.check_hover(mouse_pos)
            
            # if button1.is_clicked(mouse_pos, mouse_click):
            #     print("Impulse burn 1 applied")
            #     impulse_burn(rkrocket, 5)
            #     impulse_burn(vrocket, 5)
            #     button1.disabled = True

            # if button2.is_clicked(mouse_pos, mouse_click):
            #     print("Impulse burn 2 applied")
            #     impulse_burn(rkrocket, 5)
            #     impulse_burn(vrocket, 5)
            #     button2.disabled = True

            # Draw legend
            legend_surface = pygame.Surface((220, 100), pygame.SRCALPHA)
            legend_surface.fill(LEGEND_BG)
            pygame.draw.line(legend_surface, RED, (10, 20), (40, 20), 3)
            legend_surface.blit(small_font.render("RK4", True, WHITE), (50, 12))
            pygame.draw.line(legend_surface, BLUE, (10, 45), (40, 45), 3)
            legend_surface.blit(small_font.render("Verlet", True, WHITE), (50, 37))
            screen.blit(legend_surface, (WIDTH - 240, 20))

            # Draw status text
            status_texts = [
                f"RK4: {int(rkrocket.revolutions())}/{REVOLUTIONS_TO_WIN} revs | {rkrocket.status}",
                f"Verlet: {int(vrocket.revolutions())}/{REVOLUTIONS_TO_WIN} revs | {vrocket.status}",
            ]
            for i, text in enumerate(status_texts):
                screen.blit(
                    small_font.render(text, True, WHITE), (10, HEIGHT - 80 + i * 20)
                )
            
            # Draw info text
            info_texts = [
                f"RK4 Pos: ({rkrocket.pos.x:.1f}, {rkrocket.pos.y:.1f}) Vel: {rkrocket.speed:.2f} Acc: {rkrocket.acc.length():.4f}",
                f"Verlet Pos: ({vrocket.pos.x:.1f}, {vrocket.pos.y:.1f}) Vel: {vrocket.speed:.2f} Acc: {vrocket.acc.length():.4f}",
            ]
            for i, text in enumerate(info_texts):
                screen.blit(
                    small_font.render(text, True, WHITE), (10, HEIGHT - 40 + i * 20)
                )

        elif game_over:
            # Game over screen
            msg = (
                f'You Win! {REVOLUTIONS_TO_WIN} revolutions sustained!'
                if win
                else "Game Over! Both rockets lost."
            )
            screen.blit(font.render(msg, True, WHITE), (WIDTH // 2 - 150, HEIGHT // 2))
            screen.blit(
                font.render("Press R to restart", True, WHITE),
                (WIDTH // 2 - 100, HEIGHT // 2 + 30),
            )
            
            if win and not show_graphs:
                # Create energy plots after winning
                # RK4 energies
                fig1, ax1 = plt.subplots()
                ax1.set_title("RK4 Energies")
                ax1.plot(
                    rkrocket.energies["t"],
                    rkrocket.energies["kin"],
                    "r-",
                    label="Kinetic",
                )
                ax1.plot(
                    rkrocket.energies["t"],
                    rkrocket.energies["pot"],
                    "b-",
                    label="Potential",
                )
                ax1.plot(
                    rkrocket.energies["t"],
                    rkrocket.energies["mech"],
                    "g-",
                    label="Mechanical",
                )
                ax1.legend()
                # Verlet energies
                fig2, ax2 = plt.subplots()
                ax2.set_title("Verlet Energies")
                ax2.plot(
                    vrocket.energies["t"],
                    vrocket.energies["kin"],
                    "r-",
                    label="Kinetic",
                )
                ax2.plot(
                    vrocket.energies["t"],
                    vrocket.energies["pot"],
                    "b-",
                    label="Potential",
                )
                ax2.plot(
                    vrocket.energies["t"],
                    vrocket.energies["mech"],
                    "g-",
                    label="Mechanical",
                )
                ax2.legend()
                # Mechanical comparison
                fig3, ax3 = plt.subplots()
                ax3.set_title("Mechanical Energy Comparison")
                ax3.plot(
                    rkrocket.energies["t"], rkrocket.energies["mech"], "r-", label="RK4"
                )
                ax3.plot(
                    vrocket.energies["t"],
                    vrocket.energies["mech"],
                    "b-",
                    label="Verlet",
                )
                ax3.legend()
                plt.show()
                show_graphs = True

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()