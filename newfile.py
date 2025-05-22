import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 800
FPS = 60
AIRCRAFT_COUNT = 5
RADAR_COLOR = (0, 255, 0)
AIRCRAFT_COLOR = (255, 255, 255)
SELECTED_COLOR = (255, 0, 0)
BACKGROUND_COLOR = (0, 0, 30)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ATC Simulator")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
large_font = pygame.font.SysFont(None, 28)

# Aircraft Class
class Aircraft:
    def __init__(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.altitude = random.randint(2000, 35000)
        self.heading = random.randint(0, 359)
        self.speed = random.randint(200, 600)
        self.selected = False
        self.id = f"A{random.randint(100,999)}"

    def update(self, speed_factor):
        rad = math.radians(self.heading)
        self.x += math.cos(rad) * self.speed / 60 / 10 * speed_factor
        self.y += math.sin(rad) * self.speed / 60 / 10 * speed_factor
        # Wrap around screen
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, screen):
        color = SELECTED_COLOR if self.selected else AIRCRAFT_COLOR
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 6)
        label = font.render(f"{self.id} H:{self.heading} A:{self.altitude} S:{self.speed}", True, color)
        screen.blit(label, (self.x + 10, self.y - 10))

# Create aircraft
aircraft_list = [Aircraft() for _ in range(AIRCRAFT_COUNT)]
selected_ac = None
command_text = ""
speed_factor = 1.0

# Main loop
running = True
while running:
    clock.tick(FPS)
    screen.fill(BACKGROUND_COLOR)

    # Radar grid
    for i in range(0, WIDTH, 100):
        pygame.draw.line(screen, (30, 100, 30), (i, 0), (i, HEIGHT))
    for j in range(0, HEIGHT, 100):
        pygame.draw.line(screen, (30, 100, 30), (0, j), (WIDTH, j))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Select aircraft with mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            for ac in aircraft_list:
                if math.hypot(ac.x - mx, ac.y - my) < 10:
                    if selected_ac:
                        selected_ac.selected = False
                    ac.selected = True
                    selected_ac = ac
                    command_text = ""
                    break

        # Handle keyboard input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and selected_ac:
                parts = command_text.strip().split()
                if len(parts) == 2:
                    cmd, val = parts[0].upper(), parts[1]
                    try:
                        val = int(val)
                        if cmd == "HDG":
                            selected_ac.heading = val % 360
                        elif cmd == "ALT":
                            selected_ac.altitude = max(1000, min(val, 40000))
                        elif cmd == "SPD":
                            selected_ac.speed = max(100, min(val, 900))
                    except ValueError:
                        pass  # invalid input
                command_text = ""
            elif event.key == pygame.K_BACKSPACE:
                command_text = command_text[:-1]
            elif event.key == pygame.K_LEFTBRACKET:
                speed_factor = max(0.1, speed_factor - 0.1)
            elif event.key == pygame.K_RIGHTBRACKET:
                speed_factor = min(3.0, speed_factor + 0.1)
            else:
                if len(command_text) < 20:
                    command_text += event.unicode.upper()

    # Update and draw aircraft
    for ac in aircraft_list:
        ac.update(speed_factor)
        ac.draw(screen)

    # Draw command input area
    pygame.draw.rect(screen, (0, 50, 0), (0, HEIGHT - 40, WIDTH, 40))
    input_text = f"CMD: {command_text}" if selected_ac else "Click an aircraft to issue commands"
    input_surf = large_font.render(input_text, True, (255, 255, 255))
    screen.blit(input_surf, (10, HEIGHT - 30))

    # Draw sim speed
    speed_surf = font.render(f"Sim Speed: {speed_factor:.1f}x  ([ / ] to adjust)", True, (200, 200, 200))
    screen.blit(speed_surf, (WIDTH - 250, HEIGHT - 30))

    pygame.display.flip()

pygame.quit()