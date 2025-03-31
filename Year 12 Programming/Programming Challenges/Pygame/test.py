import pygame
import random

# Initialize Pygame
pygame.init()

# Screen setup
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Pajama Picker")

# Fonts and Colors
font = pygame.font.Font(None, 36)
white = (255, 255, 255)
black = (0, 0, 0)

# Random Pajamas
tops = ["T-shirt", "Tank top", "Sweatshirt"]
bottoms = ["Shorts", "Pajama pants", "Sweatpants"]
suggestion = f"{random.choice(tops)} and {random.choice(bottoms)}"

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(white)
    text = font.render(f"Pajamas: {suggestion}", True, black)
    screen.blit(text, (50, 130))
    pygame.display.flip()

pygame.quit()
