# Heathrow ATC Simulator with Settings & Aircraft Info Panel
import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
FPS = 60
AIRCRAFT_COUNT = 6
HEATHROW_POS = (WIDTH // 2, HEIGHT // 2)
RUNWAY_RADIUS = 60
APPROACH_RADIUS = 300
SEPARATION_RADIUS = 50

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GRAY = (100, 100, 100)
DARK = (20, 20, 30)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BLACK = (0, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Heathrow ATC Simulator")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 18)
large_font = pygame.font.SysFont("Consolas", 28)

# Aircraft Class
class Aircraft:
    def __init__(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            self.x, self.y = random.randint(0, WIDTH), 0
        elif edge == 'bottom':
            self.x, self.y = random.randint(0, WIDTH), HEIGHT
        elif edge == 'left':
            self.x, self.y = 0, random.randint(0, HEIGHT)
        else:
            self.x, self.y = WIDTH, random.randint(0, HEIGHT)

        self.altitude = random.randint(2000, 35000)
        self.heading = random.randint(0, 359)
        self.speed = random.randint(250, 600)
        self.selected = False
        self.id = f"A{random.randint(100,999)}"
        self.type = random.choice(["A320", "B738", "B777", "A380"])
        self.origin = random.choice(["EGLL", "EGKK", "EGSS", "EGMC"])
        self.target_alt = self.altitude
        self.target_heading = self.heading
        self.target_speed = self.speed

    def update(self, speed_factor):
        if self.heading != self.target_heading:
            diff = (self.target_heading - self.heading + 360) % 360
            if diff > 180:
                self.heading = (self.heading - 1) % 360
            else:
                self.heading = (self.heading + 1) % 360

        if self.altitude != self.target_alt:
            step = 500 * speed_factor
            if self.altitude < self.target_alt:
                self.altitude = min(self.altitude + step, self.target_alt)
            else:
                self.altitude = max(self.altitude - step, self.target_alt)

        if self.speed != self.target_speed:
            if self.speed < self.target_speed:
                self.speed += 1 * speed_factor
            else:
                self.speed -= 1 * speed_factor

        rad = math.radians(self.heading)
        self.x += math.cos(rad) * self.speed / 60 / 10 * speed_factor
        self.y += math.sin(rad) * self.speed / 60 / 10 * speed_factor
        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, screen):
        color = RED if self.selected else WHITE
        size = 10
        angle_rad = math.radians(self.heading)
        tip = (self.x + math.cos(angle_rad) * size, self.y + math.sin(angle_rad) * size)
        left = (self.x + math.cos(angle_rad + math.radians(140)) * size / 1.5,
                self.y + math.sin(angle_rad + math.radians(140)) * size / 1.5)
        right = (self.x + math.cos(angle_rad - math.radians(140)) * size / 1.5,
                 self.y + math.sin(angle_rad - math.radians(140)) * size / 1.5)
        pygame.draw.polygon(screen, color, [tip, left, right])

        label = font.render(f"{self.id}", True, color)
        screen.blit(label, (self.x + 12, self.y - 12))

        if self.selected:
            pygame.draw.rect(screen, GRAY, (WIDTH - 250, 50, 240, 180))
            info_lines = [
                f"CALLSIGN: {self.id}",
                f"TYPE: {self.type}",
                f"ORIGIN: {self.origin}",
                f"ALT: {int(self.altitude)} ft",
                f"HDG: {int(self.heading)}°",
                f"SPD: {int(self.speed)} kt"
            ]
            for i, line in enumerate(info_lines):
                info = font.render(line, True, BLACK)
                screen.blit(info, (WIDTH - 240, 60 + i * 25))

    def is_near_airport(self):
        return math.hypot(self.x - HEATHROW_POS[0], self.y - HEATHROW_POS[1]) < APPROACH_RADIUS

    def is_landed(self):
        return self.is_near_airport() and self.altitude < 1000 and 60 <= self.speed <= 200

# Menu and Settings
menu_active = True
settings_active = False
selected_ac = None
command_text = ""
speed_factor = 1.0
aircraft_list = [Aircraft() for _ in range(AIRCRAFT_COUNT)]

# Drawing Functions
def draw_menu():
    screen.fill(DARK)
    title = large_font.render("Heathrow ATC Simulator", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))
    prompt = font.render("Press [ENTER] to Start | Press [S] for Settings", True, GRAY)
    screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 300))
    pygame.display.flip()

def draw_settings():
    screen.fill(DARK)
    title = large_font.render("Settings", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
    options = [
        f"Aircraft Count: {AIRCRAFT_COUNT}",
        f"Simulation Speed: {speed_factor:.1f}x",
        "Back to Menu [ESC]"
    ]
    for i, opt in enumerate(options):
        txt = font.render(opt, True, GRAY)
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 250 + i * 40))
    pygame.display.flip()

def draw_conflict_alerts():
    for i, a1 in enumerate(aircraft_list):
        for a2 in aircraft_list[i+1:]:
            dist = math.hypot(a1.x - a2.x, a1.y - a2.y)
            if dist < SEPARATION_RADIUS:
                pygame.draw.line(screen, ORANGE, (a1.x, a1.y), (a2.x, a2.y), 2)
                label = font.render("CONFLICT!", True, ORANGE)
                screen.blit(label, ((a1.x + a2.x) / 2, (a1.y + a2.y) / 2))

# Main Loop
running = True
while running:
    clock.tick(FPS)

    if menu_active:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    menu_active = False
                elif event.key == pygame.K_s:
                    settings_active = True
                    menu_active = False
        continue

    if settings_active:
        draw_settings()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    settings_active = False
                    menu_active = True
        continue

    screen.fill(DARK)
    for i in range(0, WIDTH, 100):
        pygame.draw.line(screen, (30, 100, 30), (i, 0), (i, HEIGHT))
    for j in range(0, HEIGHT, 100):
        pygame.draw.line(screen, (30, 100, 30), (0, j), (WIDTH, j))

    pygame.draw.circle(screen, GREEN, HEATHROW_POS, RUNWAY_RADIUS, 2)
    pygame.draw.circle(screen, BLUE, HEATHROW_POS, APPROACH_RADIUS, 1)
    pygame.draw.line(screen, GRAY, (HEATHROW_POS[0] - 40, HEATHROW_POS[1]), (HEATHROW_POS[0] + 40, HEATHROW_POS[1]), 3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and selected_ac:
                try:
                    parts = command_text.strip().upper().split()
                    for part in parts:
                        if part.startswith("HDG"):
                            selected_ac.target_heading = int(part[3:]) % 360
                        elif part.startswith("ALT"):
                            selected_ac.target_alt = max(1000, min(int(part[3:]), 40000))
                        elif part.startswith("SPD"):
                            selected_ac.target_speed = max(100, min(int(part[3:]), 900))
                except:
                    pass
                command_text = ""
            elif event.key == pygame.K_BACKSPACE:
                command_text = command_text[:-1]
            elif event.key == pygame.K_LEFTBRACKET:
                speed_factor = max(0.1, speed_factor - 0.1)
            elif event.key == pygame.K_RIGHTBRACKET:
                speed_factor = min(3.0, speed_factor + 0.1)
            else:
                if len(command_text) < 50:
                    command_text += event.unicode.upper()

    for ac in aircraft_list:
        ac.update(speed_factor)
        ac.draw(screen)
        if ac.is_landed():
            aircraft_list.remove(ac)
            aircraft_list.append(Aircraft())

    draw_conflict_alerts()

    pygame.draw.rect(screen, (0, 50, 0), (0, HEIGHT - 40, WIDTH, 40))
    input_text = f"CMD: {command_text}" if selected_ac else "Click an aircraft to issue commands (e.g., HDG270 ALT3000 SPD250)"
    input_surf = large_font.render(input_text, True, WHITE)
    screen.blit(input_surf, (10, HEIGHT - 30))
    speed_surf = font.render(f"Sim Speed: {speed_factor:.1f}x  ([ / ] to adjust)", True, GRAY)
    screen.blit(speed_surf, (WIDTH - 250, HEIGHT - 30))

    pygame.display.flip()

pygame.quit()