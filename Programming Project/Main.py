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
    buttons = [Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))]

    while current_scene == "tutorial":
        screen.blit(background_generic, (0, 0))

        # Darkened Background
        box_width, box_height = 1100, 600
        box_x = (WINDOW_SIZE[0] - box_width) // 2
        box_y = (WINDOW_SIZE[1] - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        # Draw semi-transparent rectangle
        s = pygame.Surface((box_width, box_height))  
        s.set_alpha(180)  # 0 = fully transparent, 255 = opaque
        s.fill((0, 0, 0))  # black background
        screen.blit(s, (box_x, box_y))

        # Title 
        draw_text("Tutorial", font_title, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 40)

        # Tutorial text inside box 
        draw_text("Welcome to the Air Traffic Control Simulator!", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 120)
        draw_text("Your goal is to guide aircraft to and from the airport,", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 170)
        draw_text("ensuring all aircraft stay safe at all times.", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 220)
        draw_text("You will be able to do this by using the dedicated commands", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 270)
        draw_text("You must first call on the aircraft by using their callsign e.g              ", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 320)
        draw_text("                                                                                             'BA0342'", font_button, (0, 255, 0), screen, WINDOW_SIZE[0]//2, box_y + 320)
        draw_text("Then type out the heading you want the aircraft to follow e.g                ", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 370)
        draw_text("                                                                                               'HDG020'", font_button, (0, 255, 0), screen, WINDOW_SIZE[0]//2, box_y + 370)
        draw_text("Then type out the speed you want the aircraft to travel at e.g               ", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 420)
        draw_text("                                                                                                'SPD250'", font_button, (0, 255, 0), screen, WINDOW_SIZE[0]//2, box_y + 420)
        draw_text("'", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 470)
        draw_text("", font_button, (255, 255, 255), screen, WINDOW_SIZE[0]//2, box_y + 370)
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

