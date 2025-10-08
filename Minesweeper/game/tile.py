import pygame as py
from constants import *
from .tile_renderer import TileRenderer


class Tile:
    def __init__(self, x=0, y=0, value=0, isBomb=False, renderer=None):
        self.x = x
        self.y = y
        self.state = STATE_HIDDEN
        self.isBomb = isBomb
        self.val = value
        self.renderer = renderer if renderer is not None else TileRenderer()

    def draw(self, screen):
        self.renderer.draw_tile(screen, self)

    def set_revealed(self):
        """Reveal this tile (sets state to REVEALED or BOMB)"""
        if self.state == STATE_HIDDEN:
            self.state = STATE_BOMB if self.isBomb else STATE_REVEALED

    def plantFlag(self):
        if self.state == STATE_HIDDEN:
            self.state = STATE_FLAGGED
        elif self.state != STATE_REVEALED:
            self.state = STATE_HIDDEN
