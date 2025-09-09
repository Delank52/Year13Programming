import pygame
import sys

# Window and font
WINDOW_SIZE = (1280, 832)
FONT_NAME = "arial"
FONT_SIZE_TITLE = 36
FONT_SIZE_BUTTON = 28

pygame.init()
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
    def __init__(self, text, center, action):
        self.text = text
        self.center = center
        self.action = action
        self.rect = None

    def draw(self, surface):
        self.rect = draw_text(self.text, font_button, (255, 255, 255), surface, *self.center)

    def is_clicked(self, pos):
        return self.rect and self.rect.collidepoint(pos)

# --- Scene functions ---
def main_menu():
    buttons = [
        Button("Start simulation", (WINDOW_SIZE[0]//2, 200), lambda: change_scene("start")),
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
                        b.action()

        pygame.display.flip()
        clock.tick(60)
class Button:
    def __init__(self, text, center, action, width=300, height=60):
        self.text = text
        self.center = center
        self.action = action
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center

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

def placeholder_screen(title):
    buttons = [Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))]

    while current_scene == title.lower():
        # --- draw generic background image ---
        screen.blit(background_generic, (0, 0))

        draw_text(title, font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 - 50)
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

# --- Scene manager ---
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
                        b.action()

        pygame.display.flip()
        clock.tick(60)

# Tutorial Screen

def tutorial_screen():


    WHITE = (255,255,255)
    GREEN = (0,255,0)
    pages = [
        ["Welcome to the Air Traffic Controller Simulator", "Your Ultimate goal is to guide aircraft to and from the airport.", "Ensuring maximum aircraft safety at all times.","You will be able to do this by using the dedicated commands"],
        ["You must first call upon a specific aircraft by using their unique identifer (Callsign)", [("An example of this may be:" ,WHITE),("BA0342" ,GREEN)], "YNWA"],
        ["YNWA", "YNWA", "YNWA"],
        ["YNWA", "YNWA", "YNWA"],
        ["YNWA", "YNWA", "YNWA"],
        ["YNWA", "YNWA", "YNWA"],
    ]

    page_index = 0

    def acknowledge():
        nonlocal page_index
        if page_index < len(pages) - 1:
            page_index += 1
        else:
            change_scene("menu")  # Finish returns to menu

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
                # list of (text, color) segments for mixed colors
                draw_text_multi_color(item, font_button, screen, WINDOW_SIZE[0]//2, y)
            y += 50

        # Page indicator
        draw_text(f"Page {page_index + 1} / {len(pages)}", font_button, (200, 200, 200), screen,
                  WINDOW_SIZE[0]//2, box_y + box_height - 90)

        # Buttons
        ack_text = "Acknowledge" if page_index < len(pages) - 1 else "Finish"
        ack_btn = Button(ack_text, (box_x + box_width - 180, box_y + box_height - 40),
                         acknowledge, width=220, height=50)

        back_btn.draw(screen)
        ack_btn.draw(screen)

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.is_clicked(event.pos):
                    back_btn.action()
                elif ack_btn.is_clicked(event.pos):
                    acknowledge()

        pygame.display.flip()
        clock.tick(60)

# Main loop
while True:
    if current_scene == "menu":
        main_menu()
    elif current_scene == "start":
        placeholder_screen("Start Simulation")
    elif current_scene == "settings":
        placeholder_screen("Game Settings")
    elif current_scene == "tutorial":
        tutorial_screen()
    elif current_scene == "credits":
        credits_screen()
