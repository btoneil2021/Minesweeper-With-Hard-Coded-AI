import pygame as py
from constants import *


class Tile:
    def __init__(self, x=0, y=0, value=0, isBomb=False):
        self.x = x
        self.y = y
        self.state = STATE_HIDDEN
        self.isBomb = isBomb
        self.val = value
        self.font = py.font.Font(None, 30)

    def draw(self, screen):
        py.draw.rect(screen, COLOR_BACKGROUND, (self.x, self.y, TILE_SIZE, TILE_SIZE))
        if self.state == STATE_HIDDEN:
            py.draw.rect(screen, COLOR_TILE_HIDDEN, (self.x + TILE_SIZE//10, self.y + TILE_SIZE//10, 4 * TILE_SIZE // 5, 4 * TILE_SIZE // 5))
        elif self.state == STATE_REVEALED and self.val != 0:
            textColor = NUMBER_COLORS.get(self.val, COLOR_BLACK)
            text = self.font.render(str(self.val), True, textColor)
            text_rect = text.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(text, text_rect)
        elif self.state == STATE_FLAGGED:
            flag = py.image.load(RESOURCE_FLAG)
            flag = py.transform.scale(flag, (TILE_SIZE*.8, TILE_SIZE*.8))
            image_rect = flag.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(flag, image_rect)
        elif self.state == STATE_BOMB:
            bomb = py.image.load(RESOURCE_BOMB)
            bomb = py.transform.scale(bomb, (TILE_SIZE*.8, TILE_SIZE*.8))
            image_rect2 = bomb.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(bomb, image_rect2)

    def reveal(self):
        if self.state == STATE_HIDDEN and self.isBomb:
            self.state = STATE_BOMB
            return
        elif self.state == STATE_HIDDEN:
            self.state = STATE_REVEALED

    def plantFlag(self):
        if self.state == STATE_HIDDEN:
            self.state = STATE_FLAGGED
            return
        elif self.state != STATE_REVEALED:
            self.state = STATE_HIDDEN
            return
        return
