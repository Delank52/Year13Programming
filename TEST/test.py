import pygame
import sys

WINDOW_SIZE = (1280, 832)
FONT_NAME = "arial"
FONT_SIZE_TITLE = 36
FONT_SIZE_BUTTON = 28

pygame.init()
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Air Traffic Controller Simulator")
clock = pygame.time.Clock()