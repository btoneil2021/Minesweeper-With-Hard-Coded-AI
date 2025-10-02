import pygame as py
from constants import *

class TileRenderer:
    def __init__(self):
        self.font = py.font.Font(None, FONT_SIZE)
    
    def draw_tile(self, screen, tile):
        self._draw_background(screen, tile)
        
        if tile.state == STATE_HIDDEN:
            self._draw_hidden(screen, tile)
        elif tile.state == STATE_REVEALED and tile.val != 0:
            self._draw_number(screen, tile)
        elif tile.state == STATE_FLAGGED:
            self._draw_image(screen, tile, RESOURCE_FLAG)
        elif tile.state == STATE_BOMB:
            self._draw_image(screen, tile, RESOURCE_BOMB)
    
    def _draw_background(self, screen, tile):
        py.draw.rect(screen, COLOR_BACKGROUND, (tile.x, tile.y, TILE_SIZE, TILE_SIZE))
    
    def _draw_hidden(self, screen, tile):
        x_position = tile.x + TILE_SIZE//10
        y_position = tile.y + TILE_SIZE//10
        side_length = 4 * TILE_SIZE // 5

        py.draw.rect(screen, COLOR_TILE_HIDDEN, 
                     (x_position, y_position, 
                      side_length, side_length))
    
    def _draw_number(self, screen, tile):
        textColor = NUMBER_COLORS.get(tile.val, COLOR_BLACK)
        text = self.font.render(str(tile.val), True, textColor)
        text_rect = text.get_rect(center=(tile.x + TILE_SIZE // 2, tile.y + TILE_SIZE // 2))
        screen.blit(text, text_rect)
    
    def _draw_image(self, screen, tile, resource_path):
        image = py.image.load(resource_path)
        image = py.transform.scale(image, size=(TILE_SIZE*.8, TILE_SIZE*.8))
        image_rect = image.get_rect(center=(tile.x + TILE_SIZE // 2, tile.y + TILE_SIZE // 2))
        screen.blit(image, image_rect)