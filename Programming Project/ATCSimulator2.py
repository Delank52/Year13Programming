''' 
Start of my programming project
'''
import pygame
import sys

# Initialize Pygame
pygame.init()

# Create window
WIDTH, HEIGHT = 1280, 832
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('ATC Simulator')

# Background
background = pygame.image.load("background.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.blit(background, (0, 0))
   
    # Update the display
    pygame.display.flip()

# Quit ygame
pygame.quit()