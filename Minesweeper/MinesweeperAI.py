import Minesweeper as mn
import pygame as py
import random

class AI():
    def __init__(self):
        self.copyDict = {}

    # Grabs the board in such a way that it cannot see anything but uncovered tiles (-1 is flagged, -2 is unknown)
    def grabBoard(self,dict):
        for i in dict.keys():
            if dict[i].state == 1:
                self.copyDict[i] = dict[i].val
                continue
            if dict[i].state == 2:
                self.copyDict[i] = -1
                continue
            self.copyDict[i] = -2

    # The first few inputs. Absolutely random
    def firstMoves(self):
        while True:
            for i in self.copyDict.keys():
                if random.randint(0,mn.NUM_TILES_X*1000) == 27:
                    return i
            
    # All the linked possible tiles of a given key
    def thePossibleTileTuples(self,key):
        return [(key[0] + 1, key[1]),
                  (key[0], key[1] + 1),
                  (key[0] + 1, key[1] + 1),
                  (key[0] - 1, key[1]),
                  (key[0], key[1] - 1),
                  (key[0] - 1, key[1] - 1),
                  (key[0] - 1, key[1] + 1),
                  (key[0] + 1, key[1] - 1)]
    
    # Linked possible tiles in only the four cardinal directions
    def cardinalDirectionTileTuples(self,key):
        return [(key[0] + 1, key[1]),
                (key[0] - 1, key[1]),
                (key[0], key[1] + 1),
                (key[0], key[1] - 1)]
    
    # Grab the obvious unflagged bombs
    def sameBombsAsSquares(self,key):
        if str(key) in self.copyDict:
            tileValue = self.copyDict[str(key)]
            openSquareNumber = 0
            for i in self.thePossibleTileTuples(key):
                if str(i) not in self.copyDict:
                    continue
                if self.copyDict[str(i)] == -1 or self.copyDict[str(i)] == -2:
                    openSquareNumber += 1
            if openSquareNumber == tileValue:
                tilesToUpdate = []
                for i in self.thePossibleTileTuples(key):
                    if str(i) not in self.copyDict:
                        continue
                    if self.copyDict[str(i)] == -2:
                        tilesToUpdate.append(i)
                return tilesToUpdate
            return None
        return None
    
    def allBombsFound(self,key):
        if str(key) in self.copyDict:
            tileValue = self.copyDict[str(key)]
            flagsAround = 0
            for i in self.thePossibleTileTuples(key):
                if str(i) not in self.copyDict:
                    continue
                if self.copyDict[str(i)] == -1:
                    flagsAround += 1
            if flagsAround == tileValue:
                tilesToUpdate = []
                for i in self.thePossibleTileTuples(key):
                    if str(i) not in self.copyDict:
                        continue
                    if self.copyDict[str(i)] == -2:
                        tilesToUpdate.append(i)
                if len(tilesToUpdate) != 0:
                    return tilesToUpdate
            return None
        return None
    
    def transitiveBombProperty(self,key):
        if str(key) in self.copyDict:
            tileValue = self.copyDict[str(key)]
            adjacentTileValue = 0
            flagsAround = 0
            openSquareNumber = 0
            possibilities = []
            checkAvailability = 4
            for i in self.cardinalDirectionTileTuples(key):
                if str(i) not in self.copyDict:
                    checkAvailability -= 1
                elif self.copyDict[str(i)] >= -1:
                    checkAvailability -= 1
            if checkAvailability == 0:
                return None
            
            # Initialize flagsAround and openSquareNumber
            for i in self.thePossibleTileTuples(key):
                if str(i) not in self.copyDict:
                    continue
                elif self.copyDict[str(i)] == -2:
                    openSquareNumber += 1
                elif self.copyDict[str(i)] == -1:
                    flagsAround += 1
            # Find valued tiles in the four cardinal directions from the source
            for i in self.cardinalDirectionTileTuples(key):
                if str(i) not in self.copyDict:
                    continue
                if self.copyDict[str(i)] == -2 or self.copyDict[str(i)] == -1:
                    continue
                adjacentTileValue = self.copyDict[str(i)]
                flagsAroundAdjacent = 0
                openSquareNumberAroundAdjacent = 0
                # Find the number of flags around each of the adjacent tiles
                for j in self.thePossibleTileTuples(i):
                    if str(j) not in self.copyDict:
                        continue
                    elif self.copyDict[str(j)] == -2:
                        openSquareNumberAroundAdjacent += 1
                        possibilities.append(j)
                    elif self.copyDict[str(j)] == -1:
                        flagsAroundAdjacent += 1
                if all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 1,
                        tileValue == flagsAround + 1, 
                        openSquareNumber == 2]) or all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 1,
                        tileValue == flagsAround + 1, 
                        openSquareNumber == 2]) or all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 2,
                        tileValue == flagsAround + 2,
                        openSquareNumber == 2]):
                        theVal = (-1,-1)
                        if i == (key[0] + 1, key[1]):
                            y = possibilities[0][1]
                            for x,placeholder_y in possibilities:
                                if x >= theVal[0]:
                                    theVal = (x,y)
                                if placeholder_y != y:
                                    return None
                            return theVal
                        elif i == (key[0] - 1, key[1]):
                            theVal = (mn.NUM_TILES_X,mn.NUM_TILES_Y)
                            y = possibilities[0][1]
                            for x,placeholder_y in possibilities:
                                if x < theVal[0]:
                                    theVal = (x,y)
                                if placeholder_y != y:
                                    return None
                            return theVal
                        elif i == (key[0], key[1] + 1):
                            x = possibilities[0][0]
                            for placeholder_x,y in possibilities:
                                if y > theVal[1]:
                                    theVal = (x,y)
                                if placeholder_x != x:
                                    return None
                            return theVal
                        elif i == (key[0], key[1] - 1):
                            theVal = (mn.NUM_TILES_X,mn.NUM_TILES_Y)
                            x = possibilities[0][0]
                            for placeholder_x,y in possibilities:
                                if y < theVal[1]:
                                    theVal = (x,y)
                                if placeholder_x != x:
                                    return None
                            return theVal
                elif all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 2,
                        tileValue == flagsAround + 1,
                        openSquareNumber == 2]) or all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 2,
                        tileValue == flagsAround + 1,
                        openSquareNumber == 3]) or all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 2,
                        tileValue == 1,
                        openSquareNumber == 3]) or all([openSquareNumberAroundAdjacent == 3,
                        adjacentTileValue == flagsAroundAdjacent + 2,
                        tileValue == flagsAround + 1,
                        openSquareNumber in [2,3]]):
                        theVal = (0,0)
                        if i == (key[0] + 1, key[1]):
                            y = possibilities[0][1]
                            for x,placeholder_y in possibilities:
                                if x > theVal[0]:
                                    theVal = (x,y)
                                if placeholder_y != y:
                                    return None
                            return (-1 * theVal[0], -1 * theVal[1])
                        elif i == (key[0] - 1, key[1]):
                            y = possibilities[0][1]
                            theVal = (mn.NUM_TILES_X,mn.NUM_TILES_Y)
                            for x,placeholder_y in possibilities:
                                if x < theVal[0]:
                                    theVal = (x,y)
                                if placeholder_y != y:
                                    return None
                            return (-1 * theVal[0], -1 * theVal[1])
                        elif i == (key[0], key[1] + 1):
                            x = possibilities[0][0]
                            for placeholder_x,y in possibilities:
                                if y > theVal[1]:
                                    theVal = (x,y)
                                if placeholder_x != x:
                                    return None
                            return (-1 * theVal[0], -1 * theVal[1])
                        elif i == (key[0], key[1] - 1):
                            x = possibilities[0][0]
                            theVal = (mn.NUM_TILES_X,mn.NUM_TILES_Y)
                            for placeholder_x,y in possibilities:
                                if y < theVal[1]:
                                    theVal = (x,y)
                                if placeholder_x != x:
                                    return None
                            return (-1 * theVal[0], -1 * theVal[1])
        return None
    ''' New Stuff
    def groupingMethod(self, gameObj):
        groupsDictionary = {}
        valuesInGroups = {} # Has the # of open tiles, number of flags, and value of tile, in that order

        for i in self.copyDict.keys():
            if self.copyDict[i] in [0,-1,-2]:
                continue

            openSquareNumber = 0
            flagsAround = 0
            tileValue = self.copyDict[i]
            key = eval(i)
            groupOfOneTile = []

            for j in self.thePossibleTileTuples(key): # Init the next thing in groupsDictionary
                if str(j) not in self.copyDict:
                    continue
                elif self.copyDict[str(j)] == -2:
                    openSquareNumber += 1
                    groupOfOneTile.append(j)
                elif self.copyDict[str(j)] == -1:
                    flagsAround += 1

            valuesInGroups[i] = [openSquareNumber,flagsAround,tileValue]

            groupsDictionary[i] = groupOfOneTile

        for i in groupsDictionary.keys(): # For the value of the tile next to it beign observed
            for j in groupsDictionary.keys(): # For the value of the current tile
                if groupsDictionary[j] not in groupsDictionary[i] or i != j:
                    continue

                if all([len(groupsDictionary[j]) == 2,
                        valuesInGroups[j][2] - valuesInGroups[j][1] == 1,
                        valuesInGroups[j][0] == 2,
                        valuesInGroups[j][2] -]):

            '''




                    
    def areThereZeros(self):
        for i in self.copyDict.keys():
            if self.copyDict[i] == 0:
                return True
        return False

    def calculateProbabilities(self,key):
        # Search the values around the empty tile
        fullProb = 0
        numValuedTiles = 0
        for i in self.thePossibleTileTuples(key):
            if str(i) not in self.copyDict.keys():
                continue
            if self.copyDict[str(i)] == -1 or self.copyDict[str(i)] == -2:
                continue
            numValuedTiles += 1
            # These are for searching around the values themselves
            theValue = self.copyDict[str(i)]
            bombsLeft = theValue
            openSquares = 0
            for j in self.thePossibleTileTuples(i):
                if str(j) not in self.copyDict.keys():
                    continue
                elif self.copyDict[str(j)] == -2:
                    openSquares += 1
                elif self.copyDict[str(j)] == -1:
                    bombsLeft -= 1
            fullProb += bombsLeft / openSquares
        if numValuedTiles <= 2:
            return 1
        return fullProb / numValuedTiles
                    
    def advancedAiTech(self,theGame):
        canBeEvaluated = False
        self.grabBoard(theGame.dictionary)
        # At the beginning, doing random stuff
        if self.areThereZeros() != True:
            self.movement(key=eval(self.firstMoves()),gameObj=theGame)
            return
        else:
            canBeEvaluated = True
        
        showAndFlagTest = 0
        
        # Flag obvious unflagged bombs
        for i in self.copyDict.keys():
            key = eval(i)
            if self.copyDict[i] == -1 or self.copyDict[i] == -2:
                continue
            if self.sameBombsAsSquares(key) != None:
                for flagEm in self.sameBombsAsSquares(key):
                    if str(flagEm) not in self.copyDict:
                        continue
                    if self.copyDict[str(flagEm)] == -2:
                        self.movement(key=flagEm,gameObj=theGame,rClick=True)
                        showAndFlagTest = 1
        
        # Unhide obvious hidden tiles
        for i in self.copyDict.keys():
            key = eval(i)
            if self.copyDict[i] == -1 or self.copyDict[i] == -2:
                continue
            if self.allBombsFound(key) != None:
                for findEm in self.allBombsFound(key):
                    if str(findEm) not in self.copyDict:
                        continue
                    if self.copyDict[str(findEm)] == -2:
                        self.movement(key=findEm,gameObj=theGame)
                        showAndFlagTest = 1
        
        if showAndFlagTest == 0:
        # If a tile next to another tile has only one bomb left, the tile to the left cannot be a bomb (?)
            for i in self.copyDict.keys():
                key = eval(i)
                if self.copyDict[i] == -1 or self.copyDict[i] == -2:
                    continue
                elif self.transitiveBombProperty(key=key) != None and str(self.transitiveBombProperty(key=key)) in self.copyDict:
                    if self.transitiveBombProperty(key=key)[0] < 0 or self.transitiveBombProperty(key=key)[1] < 0:
                        self.movement(key=(-1*self.transitiveBombProperty(key=key)[0],-1*self.transitiveBombProperty(key=key)[1]),gameObj=theGame,rClick=True)
                        return canBeEvaluated
                    else:
                        self.movement(key=self.transitiveBombProperty(key=key),gameObj=theGame)
                        return canBeEvaluated
        '''
        # Take the rest of the board state and find the probability that a bomb is in each square
            # Make a new dictionary for storing the probabilities
            probabilities = {}
            numFlags = 0
            for i in self.copyDict.keys():
                if self.copyDict[i] != -2:
                    continue
                probabilities[i] = 1
                if self.copyDict[i] == -1:
                    numFlags += 1

            # Grab the number of remaining bombs
            numBombs = mn.NUM_BOMBS - numFlags

            # Calculate the probabilities for each
            for i in probabilities.keys():
                probabilities[i] = self.calculateProbabilities(eval(i))
            min_key = min(probabilities, key=lambda k: probabilities[k])
            self.movement(key=eval(min_key),gameObj=theGame)
        
        return canBeEvaluated
        '''
        

    # The main function for moving and pressing on a key
    def movement(self,key,gameObj,rClick=False):
        py.mouse.set_pos(key[0]*mn.TILE_SIZE + (mn.TILE_SIZE // 2),key[1]*mn.TILE_SIZE + (mn.TILE_SIZE // 2))
        if rClick == False:
            gameObj.dictionary[str(key)].reveal()
            if gameObj.dictionary[str(key)].val == 0:
                gameObj.revealZeros(key)
        elif gameObj.dictionary[str(key)].state != 2:
            gameObj.dictionary[str(key)].plantFlag()
        
def main():
    py.init()
    screen = py.display.set_mode(mn.SCREEN_SIZE)
    theGame = mn.TheGame()
    ai = AI()

    running = True
    gamesPlayed = 1
    gamesWon = 1
    font = py.font.Font(None, 30)
    while running:
        canBeEvaluated = ai.advancedAiTech(theGame)

        for event in py.event.get():
            if event.type == py.QUIT:
                running = False 
            elif event.type == py.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    theGame.clickAction("left")
                elif event.button == 3: # Right Click
                    theGame.clickAction("right")

        screen.fill((255,255,255))
        theGame.draw(screen)
        text = font.render(str(gamesWon/gamesPlayed),True, (0,0,0))
        screen.blit(text, (0,0))
        
        py.display.update()
        if theGame.isLost():
            py.time.delay(1000)
            if canBeEvaluated:
                gamesPlayed += 1
            del theGame
            theGame = mn.TheGame()
        elif theGame.isWon():
            py.time.delay(1000)
            if canBeEvaluated:
                gamesPlayed += 1
                gamesWon += 1
            del theGame
            theGame = mn.TheGame()

    py.quit()

if __name__ == "__main__":
    main()