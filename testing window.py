import pygame
from pygame._sdl2 import Window

pygame.init()
win = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
Window.from_display_module().maximize()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# Quit ygame
pygame.quit()