# This Python file uses the following encoding: utf-8

import random, copy, itertools
import decorators
from decorators import profile

dummy = '@'
maxRounds = 100
minWordLength = 2
maxCandidates = 3
profiled = decorators.profiled

@profile
def importDictionary():
    filename = 'dictionary-en.tsv'
    dictionaryRaw = open(filename, 'r')
    lexicon = {}
    for line in dictionaryRaw:
        lang, term, pos, definition = line.split('\t')
        wordLength = len(term)
        if wordLength >= minWordLength and term.isalpha():
            if wordLength not in lexicon: lexicon[wordLength] = [] 
            lexicon[wordLength].append((term.upper(), definition))
    return lexicon

@profile
def generateCrossword(size, lexicon):
    maxHeight = maxWidth = size
    startOrder = set(itertools.combinations_with_replacement(range(size),2))
    startOrder = startOrder.union([(x[1], x[0]) for x in startOrder])
    startOrder = sorted(startOrder, cmp=lambda x,y: x[0]+x[1]-y[0]-y[1]+10*(min(x)-min(y)))
    terms = {}
    grid = [[""]*maxWidth for _ in range(maxHeight)]
    frontStates = [ (terms, grid) ]
    deadEndStates = []
    for i in range(maxRounds):
        terms, grid = copy.deepcopy(frontStates[-1])
        
        if i%(maxRounds/10)==0: print '.', # progress bar; one dot every 10% of the rounds
             
        # find free positions close to left-uppermost corner
        startCandidates = []
        for startRow, startCol in startOrder:
            if len(startCandidates) >= maxCandidates: break
            for across in [True, False]:
                if isValidStart(grid, terms, startRow, startCol, across):
                    startCandidates.append((startRow, startCol, across))
        
        #find all crossing points with pre-existing words for each candidate
        condList = map(lambda x: getConditions(grid, x[0], x[1], x[2]), startCandidates)
        # best candidate is the one with the most crossings
        condLengths = map(len, condList)
        bestPosIndex = condLengths.index(max(condLengths))
        startRow, startCol, across = startCandidates[bestPosIndex]
        conditions = condList[bestPosIndex]
        
        
        # decide whether a dummy character is needed in the beginning of the word
        startdummy = True
        if across and startCol == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False
        elif not across and startRow == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False  
        # calculate the maximum length of the word
        maxWordLength = maxWidth - startCol if across else maxHeight - startRow
        if maxWordLength < minWordLength: continue #again, can't have one-letter words
        
        #find a word that satisfies the above conditions
        wordFound = False
        # iterate through all valid word lengths
        for wordLength in reversed(range(minWordLength, maxWordLength+1)):
            if wordFound: break
            subLexicon = lexicon[wordLength]
            if len(conditions) < 2:
                # start from a random place in the sub-lexicon
                startEntry = random.randint(0, len(subLexicon) - 1)
                # the direction of search is also random
                lexIter = subLexicon[startEntry:] if random.random() > 0.5 else reversed(subLexicon[:startEntry])
            else:
                lexIter = subLexicon if random.random() > 0.5 else reversed(subLexicon)
            for term, definition in lexIter:
                if startdummy: term = dummy + term 
                if len(term) > maxWordLength or term in terms.values(): 
                    continue
                elif len(term) < maxWordLength:
                    term = term + dummy
                satisfiedConditions = sum(i >= len(term) or term[i] == letter for i, letter in conditions)
                if satisfiedConditions == len(conditions):
                    terms[(startRow, startCol, across)] = term.replace(dummy, '')
                    for offset, letter in enumerate(term):
                        if across:
                            grid[startRow][startCol + offset] = letter
                        else:
                            grid[startRow + offset][startCol] = letter
                    #print term
                    #print "Crossword:\n" + "\n".join(str(row) for row in grid) #newline for each row
                    newState = (terms, grid)
                    if newState not in deadEndStates:
                        frontStates.append(newState)
                        #printCrossWord(grid)
                        wordFound = True
                    break #word found
        if not wordFound: # we need to backtrack!
            deadEndStates.append( frontStates.pop() )
    for t, g in frontStates + deadEndStates: #find best state!
        if len(t) > len(terms):
            terms, grid = t, g
    return grid, terms

@profile
def isValidStart(grid, terms, startRow, startCol, across):
    it = reversed(range( (startCol if across else startRow) + 1 )) 
    for i in it:
        r, c = (startRow, i) if across else (i, startCol)
        if (r, c, across) in terms:
            return False
        elif grid[r][c] == dummy:
            break
    return True

@profile
def getConditions(grid, startRow, startCol, across):
    letters = []
    if across: #move horizontally
        letters = grid[startRow][startCol:]
    else:
        letters = [row[startCol] for row in grid[startRow:]]
    return [(index, letter) for index, letter in enumerate(letters) if len(letter) > 0]

def printCrossWord(grid):
    print "\nCrossword:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)

lexicon = importDictionary()
grid, terms = generateCrossword(5, lexicon)
printCrossWord(grid)
print "\nTerms: " + ', '.join(terms.values())

decorators.printProfiled()
