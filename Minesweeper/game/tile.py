import pygame as py
from constants import *
from .tile_renderer import TileRenderer


class Tile:
    def __init__(self, x=0, y=0, value=0, isBomb=False):
        self.x = x
        self.y = y
        self.state = STATE_HIDDEN
        self.isBomb = isBomb
        self.val = value
        self.renderer = TileRenderer()

    def draw(self, screen):
        self.renderer.draw_tile(screen, self)

    def reveal(self):
        if self.state == STATE_HIDDEN and self.isBomb:
            self.state = STATE_BOMB
        elif self.state == STATE_HIDDEN:
            self.state = STATE_REVEALED

    def plantFlag(self):
        if self.state == STATE_HIDDEN:
            self.state = STATE_FLAGGED
        elif self.state != STATE_REVEALED:
            self.state = STATE_HIDDEN
