import sys
import os

fieldDelimiter = ','

class FileTracker:
    def __init__(self, name):
        self.Name = name
        self.__taken = False

    def Take(self):
        self.__taken = True

    def IsTaken(self):
        return self.__taken


class Contestant:
    def __init__(self, name, startingNumber):
        self.Name = name
        self.StartingNumber = startingNumber
        self.MusicFound = False
        self.NameTokens = name.split(' ')


def ParseNameAndNumberFromLine( line ):
#    print( "ParseNameFromLine got following tokens:" )
    tokenList = line.split(fieldDelimiter)
    if( len(tokenList) != 13 ):
        print( "Did not find expected number of tokens in line: '{0}'".format(line) )
    if( len(tokenList) < 8 ):
        print( "Expected at least 8 tokens, but found {0}, don't know how to fetch name from line. Skipping line.".format(len(tokenList)))
        return
    name = tokenList[7].strip()[1:-1]
    number = int(tokenList[6])
    return (name, number)


def ExtractContestantList( contestantsFile ):
    contestantList = []
    maxNameTokens = 0
    for line in ThreeLineRecords( contestantsFile ):
        nameNumber = ParseNameAndNumberFromLine(line)
        if( nameNumber ):
            contestant = Contestant( nameNumber[0], nameNumber[1] )
            maxNameTokens = max( maxNameTokens, len( contestant.NameTokens ) )
            contestantList.append( contestant )
            print( "Name from line: '{0}' (Start number {1})".format( contestant.Name, contestant.StartingNumber ))
    return (contestantList, maxNameTokens)
    

def ThreeLineRecords( file ):
    lines = file.readlines()
    count = 0
    line = ''
    for l in lines:
        if l[0].encode('utf-8') == b'\xef\xbb\xbf':
            l = l[1:]
        l = l.strip()

        if count < 3:
            line += l
            count += 1
        else:
            yield line
            line = l
            count = 1
    return line

def FindFileStartingWith( filenameBeginning, musicFiles ):
    for f in musicFiles:
        if not f.IsTaken() and f.Name.startswith( filenameBeginning ):
            print( "File: {0}".format(f.Name) )
            f.Take()
            return f.Name
    return ""


def RenameFile( basePath, old, new ):
    print( "Renaming file, {0}, to {1}".format(old,new))
    os.rename( os.path.join( basePath, old ), os.path.join( basePath, new ) )


def LocateAndRenameMusicWithStrategy( nameExtractFunction, contestants, musicFiles, musicFilesPath, renameCount):
    for contestant in contestants:
        if( contestant.MusicFound == False ):
            searchedName = nameExtractFunction(contestant)
            if( searchedName != None ):
                print( "Search for file starting with: {0}".format(searchedName) )
                musicFilename = FindFileStartingWith( searchedName, musicFiles)
                if( musicFilename != ""):
                    newMusicFilename = '{0:03d}-{1}'.format(contestant.StartingNumber, musicFilename)
                    RenameFile( musicFilesPath, musicFilename, newMusicFilename )
                    contestant.MusicFound = True
                    renameCount += 1
    return renameCount


def PlainNameStrategy( contestant, numNameTokens, joinCharacter ):
    if( numNameTokens > len( contestant.NameTokens )):
       return None
    return joinCharacter.join( contestant.NameTokens[:numNameTokens] ).lower()

def KeepLastNameStrategy( contestant, numNameTokens, joinCharacter):
    if( numNameTokens > len( contestant.NameTokens ) - 1):
       return None
    tokens = contestant.NameTokens[:numNameTokens]
    tokens.append(contestant.NameTokens[-1])
    return joinCharacter.join( tokens ).lower()

       
def GetFiles(path):
    myFiles = []
    files = os.listdir(path)
    for f in files:
        myFiles.append( FileTracker( f.lower() ) )
    return myFiles


args = sys.argv
argsLength = len(sys.argv)

if( argsLength != 3):
    print( "FileSorter usage:" )
    print( "    FileSorter <Contestants file> <Path to music files>")
    print( "== Failed because number of arguments were {} instead of 2 ==".format(argsLength))
    sys.exit(1)

contestantsFilename = args[1]
musicFilesPath = args[2]

print( "== Arguments are:")
for arg in args:
    print( "==   {0}".format(arg))

print( "Working with contestants file, {0}, and music files in folder, {1}".format( contestantsFilename, musicFilesPath) )


contestantsFile = open( contestantsFilename, encoding = 'utf-8')
(contestants, maxTokens) = ExtractContestantList(contestantsFile)
contestantsFile.close()

musicFiles = GetFiles( musicFilesPath )

renamedFilesCount = 0

joinCharacters = [' ', '-', '_', '.', '']

for tokens in range(maxTokens,0,-1):
    for joinChar in joinCharacters:
        fileMatchingStrategies = [lambda c: PlainNameStrategy(c,tokens,joinChar), lambda c: KeepLastNameStrategy(c,tokens, joinChar)]
        for strategy in fileMatchingStrategies:
            renamedFilesCount = LocateAndRenameMusicWithStrategy( strategy, contestants, musicFiles, musicFilesPath, renamedFilesCount )

missingCount = 0
for c in contestants:
    if( c.MusicFound == False ):
        missingCount += 1

if( missingCount > 0):
    print( "Could not find music for {0} contestant(s):".format( missingCount ) )
    for c in contestants:
        if( c.MusicFound == False ):
            print( "    [{0:03d}] {1}".format( c.StartingNumber, c.Name ) )

print( "===================================\n  Done renaming {0} music file(s)".format(renamedFilesCount))
