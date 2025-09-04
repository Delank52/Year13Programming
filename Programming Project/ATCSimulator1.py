import pygame
import sys

# --- Config ---
WINDOW_SIZE = (1280, 682)
FONT_NAME = "arial"
FONT_SIZE_TITLE = 36
FONT_SIZE_BUTTON = 28
BG_COLOR = (0, 0, 0)  # black background

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Air Traffic Controller Simulator")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont(FONT_NAME, FONT_SIZE_TITLE)
font_button = pygame.font.SysFont(FONT_NAME, FONT_SIZE_BUTTON)

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
        screen.blit(background, (0, 0))
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

def placeholder_screen(title):
    buttons = [Button("Back", (80, WINDOW_SIZE[1]-40), lambda: change_scene("menu"))]

    while current_scene == title.lower():
        screen.fill((30, 30, 30))
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

# --- Main loop ---
while True:
    if current_scene == "menu":
        main_menu()
    elif current_scene == "start":
        placeholder_screen("Start Simulation")
    elif current_scene == "settings":
        placeholder_screen("Game Settings")
    elif current_scene == "tutorial":
        placeholder_screen("Tutorial")
    elif current_scene == "credits":
        placeholder_screen("Credits")