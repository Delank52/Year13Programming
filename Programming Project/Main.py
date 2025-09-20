# --- Simulation Scene ---
def simulation_screen():
    """Displays the blank radar simulation screen with airport at center and UI bars."""
    global current_scene
    # State variables for pause, command input
    paused = False
    command_text = ""
    # For text input cursor blink (optional, not required)
    import time
    cursor_visible = True
    last_cursor_switch = time.time()
    cursor_interval = 0.5

    # --- Message log state ---
    messages = []  # list of (sender, text, timestamp)
    # Helper: append a message to the log
    def append_message(sender, text):
        messages.append((sender, text, time.time()))

    def resume_game():
        nonlocal paused
        paused = False

    def restart_level():
        nonlocal paused
        paused = False
        simulation_screen()

    zoom = 1.0
    ZOOM_MIN = 0.2
    ZOOM_MAX = 2.0
    ZOOM_STEP = 0.1

    base_radar_radius = (min(WINDOW_SIZE[0], WINDOW_SIZE[1]) / 2 - 60) * 0.75

    # Font for chat log/messages
    chat_font = pygame.font.SysFont(FONT_NAME, 22)

    while current_scene == "start":
        # Fill background (dark blue)
        screen.fill((0, 44, 66))

        # Radar circles (concentric)
        center = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
        max_radius = max(40, int(base_radar_radius * zoom))
        circle_color = (40, 60, 80)
        circle_alpha = 150
        num_circles = 5
        # Draw with alpha
        radar_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        for i in range(1, num_circles + 1):
            radius = max_radius * i // num_circles
            pygame.draw.circle(radar_surface, (*circle_color, circle_alpha), center, radius, 2)
        # Draw crosshairs
        pygame.draw.line(radar_surface, (*circle_color, circle_alpha), (center[0], 60), (center[0], WINDOW_SIZE[1]-60), 1)
        pygame.draw.line(radar_surface, (*circle_color, circle_alpha), (60, center[1]), (WINDOW_SIZE[0]-60, center[1]), 1)
        screen.blit(radar_surface, (0, 0))

        # --- Draw runways ---
        def draw_runway(surface, center, length, width, heading_deg, label1, label2, color=(180, 180, 180)):
            """Draws a runway aligned with a true heading: 0° points north (up)."""
            rotation = 90 - heading_deg

            # Runway body
            surf = pygame.Surface((length, width), pygame.SRCALPHA)
            pygame.draw.rect(surf, color, (0, 0, length, width))
            pygame.draw.rect(surf, (255, 255, 255), (0, 0, length, width), 2)
            rotated = pygame.transform.rotate(surf, rotation)
            rect = rotated.get_rect(center=center)
            surface.blit(rotated, rect.topleft)

            import math

            rad = math.radians(heading_deg)
            dx_world = math.sin(rad)
            dy_world = math.cos(rad)
            dx = dx_world
            dy = -dy_world
            half_len = length // 2

            # Threshold positions
            end1 = (center[0] + dx * half_len, center[1] + dy * half_len)
            end2 = (center[0] - dx * half_len, center[1] - dy * half_len)

            offset = max(24, 40 * zoom)
            pos1 = (end1[0] + dx * offset, end1[1] + dy * offset)
            pos2 = (end2[0] - dx * offset, end2[1] - dy * offset)

            label_font = pygame.font.SysFont(FONT_NAME, 22, bold=True)

            def draw_label(text, pos, heading):
                text_surf = label_font.render(text, True, (255, 255, 255))
                text_rot = pygame.transform.rotate(text_surf, rotation)
                text_rect = text_rot.get_rect(center=(int(pos[0]), int(pos[1])))
                surface.blit(text_rot, text_rect)

            draw_label(label1, pos1, heading_deg)
            draw_label(label2, pos2, heading_deg)

        def offset_perpendicular(base_center, heading_deg, distance):
            import math

            rad = math.radians(heading_deg)
            dx_world = math.sin(rad)
            dy_world = math.cos(rad)
            # perpendicular vector (positive to the left of heading) in world coordinates
            px_world = -dy_world
            py_world = dx_world
            px = px_world
            py = -py_world
            return (base_center[0] + px * distance, base_center[1] + py * distance)

        # Draw runways depending on airport
        airport = SETTINGS.get("Airport", "Heathrow")
        # London Heathrow: two parallel east-west runways (09L/27R and 09R/27L)
        if airport.lower() in ["heathrow", "london heathrow"]:
            heading = 90
            r_length = int(260 * zoom)
            r_width = max(8, int(14 * zoom))
            spacing = 48 * zoom
            upper_center = offset_perpendicular(center, heading, spacing)
            lower_center = offset_perpendicular(center, heading, -spacing)
            draw_runway(screen, upper_center, r_length, r_width, heading, "09L", "27R")
            draw_runway(screen, lower_center, r_length, r_width, heading, "09R", "27L")
        # Glasgow: two NE-SW runways (05/23), slightly separated
        elif airport.lower() == "glasgow":
            heading = 50
            r_length = int(220 * zoom)
            r_width = max(8, int(12 * zoom))
            draw_runway(screen, center, r_length, r_width, heading, "05", "23")
        # Los Angeles: two parallel west-east runways (25L/07R and 25R/07L)
        elif airport.lower() in ["los angeles", "lax"]:
            heading = 250
            r_length = int(300 * zoom)
            r_width = max(8, int(16 * zoom))
            spacing = 56 * zoom
            upper_center = offset_perpendicular(center, heading, spacing)
            lower_center = offset_perpendicular(center, heading, -spacing)
            draw_runway(screen, upper_center, r_length, r_width, heading, "25L", "07R")
            draw_runway(screen, lower_center, r_length, r_width, heading, "25R", "07L")

        # --- Top Bar ---
        top_bar_height = 64
        pygame.draw.rect(screen, (0, 32, 48), (0, 0, WINDOW_SIZE[0], top_bar_height))
        pygame.draw.line(screen, (20, 80, 100), (0, top_bar_height), (WINDOW_SIZE[0], top_bar_height), 2)

        # Top bar buttons (simple icons)
        icon_y = top_bar_height // 2
        icon_xs = [40, 110, 180]
        # Icon/text color (light yellow)
        icon_color = (255, 230, 0)
        # --- Zoom icon REMOVED ---
        # Pause icon (2 bars)
        pygame.draw.rect(screen, icon_color, (icon_xs[1]-8, icon_y-14, 6, 28))
        pygame.draw.rect(screen, icon_color, (icon_xs[1]+8, icon_y-14, 6, 28))
        # Help icon (circle with ?)
        pygame.draw.circle(screen, icon_color, (icon_xs[2], icon_y), 16, 2)
        qfont = pygame.font.SysFont(FONT_NAME, 24)
        draw_text("?", qfont, icon_color, screen, icon_xs[2], icon_y)

        # Airport label in top-right
        label_text = SETTINGS.get("Airport", "Heathrow")
        label_surf = font_title.render(label_text, True, icon_color)
        label_rect = label_surf.get_rect(topright=(WINDOW_SIZE[0] - 32, 12))
        screen.blit(label_surf, label_rect)

        # --- Chat/message log (top-left) ---
        now = time.time()
        chat_x = 24
        chat_y = top_bar_height + 12
        line_spacing = 8
        msg_y = chat_y
        # Only show recent messages (not faded out)
        for sender, text, timestamp in messages:
            dt = now - timestamp
            fade = min(dt / 8, 1.0)
            alpha = max(0, 255 - int(fade * 255))
            if alpha == 0:
                continue
            # Render sender label (yellow), then message text (white) next to it, both with alpha
            sender_label = f"{sender}:"
            sender_surf = chat_font.render(sender_label, True, (255, 230, 0))
            sender_surf.set_alpha(alpha)
            text_surf = chat_font.render(text, True, (255, 255, 255))
            text_surf.set_alpha(alpha)
            sender_rect = sender_surf.get_rect(topleft=(chat_x, msg_y))
            text_rect = text_surf.get_rect(topleft=(sender_rect.right + 8, msg_y))
            screen.blit(sender_surf, sender_rect)
            screen.blit(text_surf, text_rect)
            msg_y += max(sender_rect.height, text_rect.height) + line_spacing

        # --- Bottom Bar ---
        bottom_bar_height = 48
        pygame.draw.rect(screen, (0, 32, 48), (0, WINDOW_SIZE[1]-bottom_bar_height, WINDOW_SIZE[0], bottom_bar_height))
        pygame.draw.line(screen, (20, 80, 100), (0, WINDOW_SIZE[1]-bottom_bar_height), (WINDOW_SIZE[0], WINDOW_SIZE[1]-bottom_bar_height), 2)
        # Draw "Command Bar" label at left
        draw_text("Command Bar", font_button, (255, 230, 0), screen, 120, WINDOW_SIZE[1]-bottom_bar_height//2)
        # Draw input box (simple rectangle and text)
        input_box_x = 220
        input_box_y = WINDOW_SIZE[1] - bottom_bar_height + 8
        input_box_w = WINDOW_SIZE[0] - input_box_x - 32
        input_box_h = bottom_bar_height - 16
        input_rect = pygame.Rect(input_box_x, input_box_y, input_box_w, input_box_h)
        pygame.draw.rect(screen, (24, 48, 64), input_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 230, 0), input_rect, 2, border_radius=8)
        # Render the command text inside the input box
        txt_surf = font_button.render(command_text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(midleft=(input_rect.left + 12, input_rect.centery))
        screen.blit(txt_surf, txt_rect)
        # Draw blinking cursor if focused (always focused in this context)
        if now - last_cursor_switch > cursor_interval:
            cursor_visible = not cursor_visible
            last_cursor_switch = now
        if cursor_visible:
            cursor_x = txt_rect.right + 4
            cursor_y1 = txt_rect.top + 4
            cursor_y2 = txt_rect.bottom - 4
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

        # Draw PAUSED overlay with pause menu if paused
        if paused:
            s = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
            s.fill((0, 0, 0, 120))
            screen.blit(s, (0, 0))
            # Draw "PAUSED" text
            paused_center_x = WINDOW_SIZE[0] // 2
            paused_center_y = WINDOW_SIZE[1] // 2 - 90
            draw_text("PAUSED", font_title, (255, 230, 0), screen, paused_center_x, paused_center_y)

            # Define pause menu buttons, centered and vertically spaced below "PAUSED"
            button_spacing = 70
            btn_centers = [
                (paused_center_x, paused_center_y + 60),
                (paused_center_x, paused_center_y + 60 + button_spacing),
                (paused_center_x, paused_center_y + 60 + 2 * button_spacing),
                (paused_center_x, paused_center_y + 60 + 3 * button_spacing),
            ]
            pause_menu_buttons = [
                Button("Resume", btn_centers[0], resume_game),
                Button("Settings", btn_centers[1], lambda: change_scene("settings")),
                Button("Restart Level", btn_centers[2], restart_level),
                Button("Main Menu", btn_centers[3], lambda: change_scene("menu")),
            ]
            # Draw the buttons
            for b in pause_menu_buttons:
                b.draw(screen)

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    change_scene("menu")
                    continue

                if event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                    zoom = max(ZOOM_MIN, round(zoom - ZOOM_STEP, 2))
                    continue
                if event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    zoom = min(ZOOM_MAX, round(zoom + ZOOM_STEP, 2))
                    continue

                # Only handle input if not paused
                if not paused:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        print(command_text)
                        if command_text.strip():
                            append_message("You", command_text)
                        command_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        command_text = command_text[:-1]
                    elif event.key == pygame.K_TAB:
                        pass  # ignore tab
                    elif event.unicode and len(event.unicode) == 1 and event.unicode.isprintable():
                        if len(command_text) < 100:
                            command_text += event.unicode
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    zoom = min(ZOOM_MAX, round(zoom + ZOOM_STEP * event.y, 2))
                elif event.y < 0:
                    zoom = max(ZOOM_MIN, round(zoom + ZOOM_STEP * event.y, 2))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if paused:
                    # Define pause menu buttons in the same way as above to check clicks
                    paused_center_x = WINDOW_SIZE[0] // 2
                    paused_center_y = WINDOW_SIZE[1] // 2 - 90
                    button_spacing = 70
                    btn_centers = [
                        (paused_center_x, paused_center_y + 60),
                        (paused_center_x, paused_center_y + 60 + button_spacing),
                        (paused_center_x, paused_center_y + 60 + 2 * button_spacing),
                        (paused_center_x, paused_center_y + 60 + 3 * button_spacing),
                    ]
                    pause_menu_buttons = [
                        Button("Resume", btn_centers[0], resume_game),
                        Button("Settings", btn_centers[1], lambda: change_scene("settings")),
                        Button("Restart Level", btn_centers[2], restart_level),
                        Button("Main Menu", btn_centers[3], lambda: change_scene("menu")),
                    ]
                    for b in pause_menu_buttons:
                        if b.is_clicked((mx, my)):
                            b.activate()
                            break
                else:
                    # Pause icon click
                    pause_dist = math.hypot(mx - icon_xs[1], my - icon_y)
                    if pause_dist <= 24:
                        paused = not paused
                    # Help icon click
                    help_dist = math.hypot(mx - icon_xs[2], my - icon_y)
                    if help_dist <= 24:
                        change_scene("tutorial")

        pygame.display.flip()
        clock.tick(60)
import pygame
import sys
import os
import math
import webbrowser
from pathlib import Path

# Window and font
WINDOW_SIZE = (1280, 832)
FONT_NAME = "arial"
FONT_SIZE_TITLE = 36
FONT_SIZE_BUTTON = 28

pygame.init()
try:
    pygame.mixer.init()
    _mixer_ready = True
except pygame.error as exc:
    print(f"Audio init failed: {exc}")
    _mixer_ready = False
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Air Traffic Controller Simulator")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont(FONT_NAME, FONT_SIZE_TITLE)
font_button = pygame.font.SysFont(FONT_NAME, FONT_SIZE_BUTTON)

# Load background image 
background_menu = pygame.image.load("background.png")
background_menu = pygame.transform.scale(background_menu, WINDOW_SIZE)

background_generic = pygame.image.load("background.png")
background_generic = pygame.transform.scale(background_generic, WINDOW_SIZE)


def _load_button_sound():
    if not _mixer_ready:
        return None
    candidates = [
        "Soundeffect.wav",
        "Soundeffect.ogg",
        "Soundeffect.mp3",
        "Soundeffect",
    ]
    for name in candidates:
        path = Path(name)
        if path.exists():
            try:
                return pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                print(f"Failed to load button sound '{name}': {exc}")
    return None


BUTTON_SOUND = _load_button_sound()


def play_button_sound():
    if BUTTON_SOUND:
        BUTTON_SOUND.play()

# --- Helper functions ---
def draw_text(text, font, color, surface, x, y):
    """Draw text centered at (x, y)."""
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect(center=(x, y))
    surface.blit(text_obj, text_rect)
    return text_rect

def draw_text_multi_color(segments, font, surface, center_x, center_y):
    """Draw a single line with differently colored segments centered at (center_x, center_y).
    segments: list of (text, (r,g,b)) tuples
    """
    widths = [font.size(txt)[0] for txt, _ in segments]
    total_width = sum(widths)
    x = center_x - total_width // 2
    for (txt, color), w in zip(segments, widths):
        surf = font.render(txt, True, color)
        rect = surf.get_rect(midleft=(x, center_y))
        surface.blit(surf, rect)
        x += w

class Button:
    def __init__(self, text, center, action, play_sound=True):
        self.text = text
        self.center = center
        self.action = action
        self.rect = None
        self.play_sound = play_sound

    def draw(self, surface):
        self.rect = draw_text(self.text, font_button, (255, 255, 255), surface, *self.center)

    def is_clicked(self, pos):
        return self.rect and self.rect.collidepoint(pos)

    def activate(self):
        if self.play_sound:
            play_button_sound()
        if self.action:
            self.action()

# --- Scene functions ---
def main_menu():
    buttons = [
        Button("Start simulation", (WINDOW_SIZE[0]//2, 200), lambda: change_scene("confirm_tutorial")),
        Button("Game settings", (WINDOW_SIZE[0]//2, 270), lambda: change_scene("settings")),
        Button("Tutorial", (WINDOW_SIZE[0]//2, 340), lambda: change_scene("tutorial")),
        Button("Credits", (WINDOW_SIZE[0]//2, 410), lambda: change_scene("credits")),
        Button("Exit", (80, WINDOW_SIZE[1]-40), lambda: pygame.quit() or sys.exit())
    ]

    while current_scene == "menu":
        # --- draw background image ---
        screen.blit(background_menu, (0, 0))

        draw_text("Air Traffic Controller Simulator", font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, 80)
        for b in buttons:
            b.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.activate()

        pygame.display.flip()
        clock.tick(60)
class Button:
    def __init__(self, text, center, action, width=300, height=60, play_sound=True):
        self.text = text
        self.center = center
        self.action = action
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.play_sound = play_sound

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()

        # Change color if hovered
        if self.rect.collidepoint(mouse):
            color = (0, 130, 0)   # hover color (steel blue)
        else:
            color = (0, 149, 0)  # normal color (cornflower blue)

        # Draw button background (rounded corners)
        pygame.draw.rect(surface, color, self.rect, border_radius=12)

        # Draw button border
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=12)

        # Draw button text
        text_surf = font_button.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def activate(self):
        if self.play_sound:
            play_button_sound()
        if self.action:
            self.action()


# Scene manager
current_scene = "menu"
def change_scene(name):
    global current_scene
    current_scene = name

# Credits Page
def credits_screen():
    buttons = [Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))]

    while current_scene == "credits":
        screen.blit(background_generic, (0, 0))

        # Darkened Background
        box_width, box_height = 800, 400
        box_x = (WINDOW_SIZE[0] - box_width) // 2
        box_y = (WINDOW_SIZE[1] - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        # Draw semi-transparent rectangle
        s = pygame.Surface((box_width, box_height))  
        s.set_alpha(180)  # 0 = fully transparent, 255 = opaque
        s.fill((0, 0, 0))  # black background
        screen.blit(s, (box_x, box_y))

        # Title 
        draw_text("Credits", font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 40)

        # Credits text inside box 
        draw_text("Developed by: Delan Karim", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 120)
        draw_text("Inspired by real-world ATC operations", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 170)
        draw_text("Developed at Central foundation Boys School", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 220)

        # Draw buttons
        for b in buttons:
            b.draw(screen)

        # Handle events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.activate()

        pygame.display.flip()
        clock.tick(60)


# Settings Page
SETTINGS = {
    "master_volume": "Medium",   # Off/Low/Medium/High
    "difficulty": "Normal",      # Easy/Normal/Hard
    "gamemode": "Air",           # Ground/Air
    "Airport": "Heathrow",          # Low/Medium/High
}


class Dropdown:
    def __init__(self, label, center, width, options, selected_index=0, row_height=44):
        self.label = label
        self.center = center
        self.width = width
        self.options = options
        self.index = max(0, min(selected_index, len(options) - 1))
        self.row_height = row_height
        self.open = False
        self.rect = pygame.Rect(0, 0, width, row_height)
        self.rect.center = center

    @property
    def value(self):
        return self.options[self.index]

    def draw(self, surface):
        # Main box first
        pygame.draw.rect(surface, (30, 30, 30), self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)

        # Selected text inside the box
        sel_surf = font_button.render(self.value, True, (255, 255, 255))
        sel_rect = sel_surf.get_rect(midleft=(self.rect.left + 12, self.rect.centery))
        surface.blit(sel_surf, sel_rect)

        # Label above the box (drawn after so it isn't covered)
        label_text = f"{self.label}: {self.value}"
        text_surf = font_button.render(label_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(midbottom=(self.center[0], self.rect.top - 8))
        surface.blit(text_surf, text_rect)

        # Arrow
        ax = self.rect.right - 24
        ay = self.rect.centery
        arrow = [(ax - 8, ay - 4), (ax, ay - 4), (ax - 4, ay + 6)] if not self.open else [(ax - 8, ay + 4), (ax, ay + 4), (ax - 4, ay - 6)]
        pygame.draw.polygon(surface, (255, 255, 255), arrow)

        # Options list (open downwards below the box)
        if self.open:
            for i, opt in enumerate(self.options):
                r = pygame.Rect(
                    self.rect.left,
                    self.rect.bottom + i * self.row_height,
                    self.rect.width,
                    self.row_height,
                )
                bg = (60, 60, 60) if i != self.index else (0, 149, 0)
                pygame.draw.rect(surface, bg, r)
                pygame.draw.rect(surface, (255, 255, 255), r, 1)
                osurf = font_button.render(opt, True, (255, 255, 255))
                orect = osurf.get_rect(midleft=(r.left + 12, r.centery))
                surface.blit(osurf, orect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                self.open = not self.open
                return
            if self.open:
                # Check options list (opened downwards)
                for i, _ in enumerate(self.options):
                    r = pygame.Rect(
                        self.rect.left,
                        self.rect.bottom + i * self.row_height,
                        self.rect.width,
                        self.row_height,
                    )
                    if r.collidepoint(mx, my):
                        self.index = i
                        self.open = False
                        return
                # Click outside closes
                self.open = False


def settings_screen():
    # Panel layout similar to tutorial/credits
    panel_w, panel_h = 1000, 600
    panel_x = (WINDOW_SIZE[0] - panel_w) // 2
    panel_y = (WINDOW_SIZE[1] - panel_h) // 2

    # Controls (dropdowns only, no sliders)
    vol_levels = ["Off", "Low", "Medium", "High"]
    difficulties = ["Beginner", "Easy", "Normal", "Realistic"]
    gamemodes = ["Ground", "Air"]
    Airport = ["Los Angeles", "London Heathrow", "Glasgow"]

    dd_master_vol = Dropdown(
        "Master Volume",
        (panel_x + panel_w // 2, panel_y + 200),
        360,
        vol_levels,
        selected_index=vol_levels.index(SETTINGS.get("master_volume", "Medium")) if SETTINGS.get("master_volume", "Medium") in vol_levels else 2,
        row_height=38,
    )

    dd_gamemode = Dropdown(
        "Gamemode",
        (panel_x + panel_w // 2, panel_y + 290),
        360,
        gamemodes,
        selected_index=gamemodes.index(SETTINGS.get("gamemode", "Air")) if SETTINGS.get("gamemode", "Air") in gamemodes else 1,
        row_height=38,
    )

    dd_difficulty = Dropdown(
        "Difficulty",
        (panel_x + panel_w // 2, panel_y + 380),
        360,
        difficulties,
        selected_index=difficulties.index(SETTINGS.get("difficulty", "Normal")) if SETTINGS.get("difficulty", "Normal") in difficulties else 1,
        row_height=38,
    )

    dd_airports = Dropdown(
        "Airport",
        (panel_x + panel_w // 2, panel_y + 480),
        360,
        Airport,
        selected_index=Airport.index(SETTINGS.get("Airport", "High")) if SETTINGS.get("Airport", "High") in Airport else 2,
        row_height=38,
    )

    back_btn = Button("Back", (80, WINDOW_SIZE[1] - 40), lambda: change_scene("menu"))
    apply_btn = Button("Apply", (panel_x + panel_w - 140, panel_y + panel_h - 40), lambda: None, width=200, height=50)
    reset_btn = Button("Reset", (panel_x + 140, panel_y + panel_h - 40), lambda: None, width=200, height=50)

    def apply_changes():
        SETTINGS["master_volume"] = dd_master_vol.value
        SETTINGS["difficulty"] = dd_difficulty.value
        SETTINGS["gamemode"] = dd_gamemode.value
        SETTINGS["Airport"] = dd_airports.value
        change_scene("menu")

    def reset_defaults():
        dd_master_vol.index = vol_levels.index("Medium")
        dd_difficulty.index = difficulties.index("Normal")
        dd_gamemode.index = gamemodes.index("Air")
        dd_airports.index = Airport.index("High")

    apply_btn.action = apply_changes
    reset_btn.action = reset_defaults

    while current_scene == "settings":
        screen.blit(background_generic, (0, 0))

        # Dimmed panel
        s = pygame.Surface((panel_w, panel_h))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (panel_x, panel_y))

        # Title
        draw_text("Game Settings", font_title, (255, 255, 255), screen, panel_x + panel_w // 2, panel_y + 80)

        # Draw controls
        dd_master_vol.draw(screen)
        dd_gamemode.draw(screen)
        dd_difficulty.draw(screen)
        dd_airports.draw(screen)

        # Draw buttons
        reset_btn.draw(screen)
        apply_btn.draw(screen)
        back_btn.draw(screen)

        # Re-draw open dropdowns last so their menus are on top
        for dd in (dd_master_vol, dd_gamemode, dd_difficulty, dd_airports):
            if dd.open:
                dd.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Delegate to controls
            dd_master_vol.handle_event(event)
            dd_gamemode.handle_event(event)
            dd_difficulty.handle_event(event)
            dd_airports.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_clicked(event.pos):
                    back_btn.activate()
                elif reset_btn.is_clicked(event.pos):
                    reset_btn.activate()
                elif apply_btn.is_clicked(event.pos):
                    apply_btn.activate()

        pygame.display.flip()
        clock.tick(60)

# Tutorial Screen

def tutorial_screen():


    WHITE = (255,255,255)
    GREEN = (0,255,0)
    pages = [
        ["Welcome to the Air Traffic Controller Simulator", "Your Ultimate goal is to guide aircraft to and from the Airport.", "Ensuring maximum aircraft safety at all times.","You will be able to do this by using the dedicated commands"],
        ["To contact an aircraft you must follow these steps","You must first call upon a specific aircraft by using their unique identifer (Callsign)", [("An example of this may be:" ,WHITE),("BA0342" ,GREEN)],"You must then let the aircraft know what direction to head (Heading (0 to 360 degrees))", [("Something like this:" ,WHITE),("HDG180" ,GREEN)],"You must then let the aircraft know what speed to travel at", [("e.g" ,WHITE),("SPD250" ,GREEN)]],
        ["Finally you must tell them the altitude they need to be at", [("As shown:" ,WHITE),("FL360" ,GREEN)], "You can then combine these 4 into one statement as shown", ("BA0342 HDG180 SPD250 FL360",GREEN),"If your statement is correct the aircraft will follow your instructions ASAP"],
        ["All aircraft need to be directed into the intended entry point for each runway", "To see an example of what this can look like press the button below", "The red arrow on the left pointing to the right shows exactly where aircraft must be to land", " The departure path is also shown on the right of the runway using the red arrow", "This is the landing/take-off procedure at Heathrow Airport Runway 09L,", " every Airport and runway will have a unique document to follow."],
        ["Once the aircraft have arrived at the entry point, the user must command them to land", [("This can be done like this:", WHITE), ("BA0342 CLEARED TO LAND RWY09L",GREEN)],"Note aircraft must be at the suitable landing altitude stated in the document","Aircraft must also be at a suitable distance from each other (5nm)", [("Similarly, to take off an aircraft simply type: ", WHITE),("BA0342 CLEARED FOR TAKEOFF RWY09L", GREEN)]],
        ["The other gamemode, which the user can also play is ground control", "The user must guide aircraft between the gates and runways", "An example of what the Airport might look like can be seen by pressing the button below.", [("The user can guide aircraft to gates like this:",WHITE), ("BA0342 TAXI TO GATE 45 VIA A B F", GREEN)], "With A B and F being specific taxi-ways"],
    ]

    page_index = 0

    def acknowledge():
        nonlocal page_index
        if page_index < len(pages) - 1:
            page_index += 1
        else:
            change_scene("menu")  # Finish returns to menu

    def open_pdf(pdf_path: str):
        abs_path = os.path.abspath(pdf_path)
        if not os.path.exists(abs_path):
            print(f"PDF not found: {abs_path}")
            return
        webbrowser.open_new(Path(abs_path).as_uri())  # opens in default viewer

    back_btn = Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))

    while current_scene == "tutorial":
        screen.blit(background_generic, (0, 0))

        # Darkened background box
        box_width, box_height = 1100, 600
        box_x = (WINDOW_SIZE[0] - box_width) // 2
        box_y = (WINDOW_SIZE[1] - box_height) // 2

        s = pygame.Surface((box_width, box_height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (box_x, box_y))

        # Title
        draw_text("Tutorial", font_title, (255, 255, 255), screen,
                  WINDOW_SIZE[0]//2, box_y + 40)

        # Draw current page lines supporting strings, (text,color) tuples, and lists of segments
        y = box_y + 120
        for item in pages[page_index]:
            if isinstance(item, str):
                draw_text(item, font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, y)
            elif isinstance(item, tuple) and len(item) == 2:
                text, color = item
                draw_text(text, font_button, color, screen, WINDOW_SIZE[0]//2, y)
            else:
                # list of (text, color) segments
                draw_text_multi_color(item, font_button, screen, WINDOW_SIZE[0]//2, y)
            y += 50

        # Page indicator
        draw_text(f"Page {page_index + 1} / {len(pages)}", font_button, (200, 200, 200), screen,
                  WINDOW_SIZE[0]//2, box_y + box_height - 90)

        # Buttons
        ack_text = "Acknowledge" if page_index < len(pages) - 1 else "Finish"
        ack_btn = Button(ack_text, (box_x + box_width - 180, box_y + box_height - 40),
                         acknowledge, width=220, height=50)

        # PDF button appears only on the 5th page (index 4)
        pdf_btn = None
        if page_index == 3:
            pdf_btn = Button(
                "Open PDF",
                (box_x + 180, box_y + box_height - 40),
                lambda: open_pdf("Runway09L.pdf"),
                width=220,
                height=50,
            )

        back_btn.draw(screen)
        if pdf_btn:
            pdf_btn.draw(screen)
        ack_btn.draw(screen)


        # PDF button appears only on the 5th page (index 4)
        pdf_btn = None
        if page_index == 5:
            pdf_btn = Button(
                "Open PDF",
                (box_x + 180, box_y + box_height - 40),
                lambda: open_pdf("Groundmap.pdf"),
                width=220,
                height=50,
            )


        back_btn.draw(screen)
        if pdf_btn:
            pdf_btn.draw(screen)
        ack_btn.draw(screen)
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_clicked(event.pos):
                    back_btn.activate()
                elif pdf_btn and pdf_btn.is_clicked(event.pos):
                    pdf_btn.activate()
                elif ack_btn.is_clicked(event.pos):
                    ack_btn.activate()

        pygame.display.flip()
        clock.tick(60)


def confirm_tutorial():
    # Panel dimensions similar to credits/tutorial screens
    box_width, box_height = 600, 300
    box_x = (WINDOW_SIZE[0] - box_width) // 2
    box_y = (WINDOW_SIZE[1] - box_height) // 2

    # Buttons centered relative to the box
    buttons = [
        Button("Yes", (box_x + box_width//2 - 80, box_y + box_height - 60),
               lambda: change_scene("tutorial"), width=150, height=50),
        Button("No",  (box_x + box_width//2 + 80, box_y + box_height - 60),
               lambda: change_scene("start"), width=150, height=50),
    ]

    while current_scene == "confirm_tutorial":
        screen.blit(background_generic, (0, 0))

        # Draw semi-transparent dark rectangle
        s = pygame.Surface((box_width, box_height))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        screen.blit(s, (box_x, box_y))

        # Draw prompt text centered in box
        draw_text(
            "Visit tutorial first?",
            font_title,
            (255, 255, 255),
            screen,
            box_x + box_width // 2,
            box_y + 80
        )

        # Draw the buttons
        for b in buttons:
            b.draw(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for b in buttons:
                    if b.is_clicked(event.pos):
                        b.action()

        pygame.display.flip()
        clock.tick(60)

# Main loop
while True:
    if current_scene == "menu":
        main_menu()
    elif current_scene == "confirm_tutorial":
        confirm_tutorial()
    elif current_scene == "settings":
        settings_screen()
    elif current_scene == "tutorial":
        tutorial_screen()
    elif current_scene == "credits":
        credits_screen()
    elif current_scene == "start":
        simulation_screen()
