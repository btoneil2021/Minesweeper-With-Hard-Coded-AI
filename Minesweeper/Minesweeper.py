import pygame as py
import math
import random

# Globals
NUM_BOMBS = 300
NUM_TILES_X = 40
NUM_TILES_Y = 40
TILE_SIZE = 20
SCREEN_SIZE = (TILE_SIZE*NUM_TILES_X,TILE_SIZE*NUM_TILES_Y)

class Tile():
    def __init__(self, x=0, y=0, value=0, isBomb = False):
        self.x = x
        self.y = y
        self.state = 0 # 0 - hidden, 1 - shown, 2 - flagged, 3 - bomb tile
        self.isBomb = isBomb
        self.val = value
        self.font = py.font.Font(None, 30)
    
    def draw(self, screen):
        py.draw.rect(screen, (222,184,135), (self.x, self.y, TILE_SIZE, TILE_SIZE))
        if self.state == 0:
            py.draw.rect(screen, (184,134,77), (self.x + TILE_SIZE//10, self.y + TILE_SIZE//10, 4 * TILE_SIZE // 5, 4 * TILE_SIZE // 5))
        elif self.state == 1 and self.val != 0:
            textColor = ()
            if self.val == 1:
                textColor = (2,32,184)
            elif self.val == 2:
                textColor = (1,133,21)
            elif self.val == 3:
                textColor = (242,0,0)
            elif self.val == 4:
                textColor = (30,3,140)
            elif self.val == 5:
                textColor = (99,55,0)
            elif self.val == 6:
                textColor = (0,181,151)
            elif self.val == 7:
                textColor = (0,0,0)
            elif self.val == 8:
                textColor = (97,97,97)
            text = self.font.render(str(self.val),True, textColor)
            text_rect = text.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(text, text_rect)
        elif self.state == 2:
            flag = py.image.load("resources/flag.png")
            flag = py.transform.scale(flag, (TILE_SIZE*.8,TILE_SIZE*.8))
            image_rect = flag.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(flag, image_rect)
        elif self.state == 3:
            bomb = py.image.load("resources/bomb.png")
            bomb = py.transform.scale(bomb, (TILE_SIZE*.8,TILE_SIZE*.8))
            image_rect2 = bomb.get_rect(center=(self.x + TILE_SIZE // 2, self.y + TILE_SIZE // 2))
            screen.blit(bomb, image_rect2)
        
    def reveal(self):
        if self.state == 0 and self.isBomb == True:
            self.state = 3
            return
        elif self.state == 0:
            self.state = 1

    def plantFlag(self):
        if self.state == 0:
            self.state = 2
            return
        elif self.state != 1:
            self.state = 0
            return
        return

class TheGame():
    def __init__(self):
        self.dictionary = {}

        self.initializeTiles()
        for i in range(NUM_TILES_Y):
            for j in range(NUM_TILES_X):
                if self.dictionary[str((j,i))].isBomb == False:
                    self.initializeValues((j,i))
 
    def initializeTiles(self):
        x = 0
        y = 0
        for i in range(NUM_TILES_Y):
            for j in range(NUM_TILES_X):
                self.dictionary[str((j,i))] = Tile(x=x,y=y)
                x += TILE_SIZE
            y += TILE_SIZE
            x = 0
        for i in range(NUM_BOMBS):
            x = random.randint(0,NUM_TILES_X-1)
            y = random.randint(0,NUM_TILES_Y-1)
            if self.dictionary[str((x,y))].isBomb == True:
                while self.dictionary[str((x,y))].isBomb == True:
                    x = random.randint(0,NUM_TILES_X-1)
                    y = random.randint(0,NUM_TILES_Y-1)
            self.dictionary[str((x,y))].isBomb = True
        for i in range(NUM_TILES_Y):
            for j in range(NUM_TILES_X):
                if self.dictionary[str((j,i))].isBomb == False:
                    self.initializeValues((j,i))
        
    def initializeValues(self,key):
        val = 0
        theTuple = [(key[0] + 1, key[1]),
                  (key[0], key[1] + 1),
                  (key[0] + 1, key[1] + 1),
                  (key[0] - 1, key[1]),
                  (key[0], key[1] - 1),
                  (key[0] - 1, key[1] - 1),
                  (key[0] - 1, key[1] + 1),
                  (key[0] + 1, key[1] - 1)]
        for i in theTuple:
            if str(i) in self.dictionary:
                if self.dictionary[str(i)].isBomb == True:
                    val += 1
        self.dictionary[str(key)] = Tile(x=self.dictionary[str(key)].x,
                                       y=self.dictionary[str(key)].y,
                                       value = val,
                                       isBomb = self.dictionary[str(key)].isBomb)

    def draw(self,screen):
        for i in self.dictionary.keys():
            self.dictionary[i].draw(screen)

    def clickAction(self,action):
        pos = py.mouse.get_pos()
        row = math.floor(pos[0] / TILE_SIZE)
        col = math.floor(pos[1] / TILE_SIZE)
        if action == "left":
            self.dictionary[str((row,col))].reveal()
            if self.dictionary[str((row,col))].val == 0:
                self.revealZeros((row,col))
        elif action == "right":
            self.dictionary[str((row,col))].plantFlag()

    def revealZeros(self, key):
        theTuple = [(key[0] + 1, key[1]),
                  (key[0], key[1] + 1),
                  (key[0] + 1, key[1] + 1),
                  (key[0] - 1, key[1]),
                  (key[0], key[1] - 1),
                  (key[0] - 1, key[1] - 1),
                  (key[0] - 1, key[1] + 1),
                  (key[0] + 1, key[1] - 1)]
        statesUpdated = 0
        if str(key) not in self.dictionary or self.dictionary[str(key)].isBomb == True:
            return
        if self.dictionary[str(key)].val == 0:
            for i in theTuple:
                if str(i) in self.dictionary:
                    if not self.dictionary[str(i)].isBomb and self.dictionary[str(i)].state != 1:
                        self.dictionary[str(i)].state = 1
                        statesUpdated += 1
            if statesUpdated != 0:
                for i in range(7):
                    self.revealZeros(theTuple[random.randint(0,7)])

    def isLost(self):
        for i in self.dictionary.keys():
            if self.dictionary[i].state == 3:
                return True
        return False
            
    
    def isWon(self):
        for i in self.dictionary.keys():
            if self.dictionary[i].state not in [1,2]:
                return False
        return True