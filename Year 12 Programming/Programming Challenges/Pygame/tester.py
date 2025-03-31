import pygame
import random

# Initialize Pygame
pygame.init()

# Screen setup
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Color Changer")

# Function to generate random color
def random_color():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

# Start with a random color
current_color = random_color()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            current_color = random_color()  # Change color on click

    screen.fill(current_color)
    pygame.display.flip()

pygame.quit()
