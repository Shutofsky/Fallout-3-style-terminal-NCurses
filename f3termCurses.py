#!/usr/bin/python3
# -*- coding: utf-8 -*-
import curses
import random
import time
import json
import string
import threading
#import pygame.mixer

db_parameters = dict()
forceClose = False
is_db_updating = False
db_updated = False
dbCheckInterval = 2
delayTime = 40
lockTimeOutStart = 0

start_time = time.time()

def millis():
    return (time.time() - start_time) * 1000.0

def load_str():
    with open ('tststr.txt', 'r') as fh:
        fullstr = fh.read()
        return fullstr

def initCurses():
    global curses
    curses.initscr()
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.noecho()
    curses.raw()
    curses.curs_set(2)

def readDBParameters(checkInterval=2):
    global db_parameters
    global is_db_updating
    global forceClose
    while True:
        if forceClose:
            break
        if not is_db_updating:
            is_db_updating = True
            with open('ftjSON.txt', 'r', encoding='utf8') as f:
                db_parameters = json.load(f) 
            is_db_updating = False
        time.sleep(checkInterval)

def updateDBParameters():
    # Принимает словарь, где ключ - поле в базе, значение ключа - значение, которое нужно записать в базу.
    global is_db_updating
    global db_parameters
    while is_db_updating:
        pass
    try:
        is_db_updating = True
        with open('ftjSON.txt', 'w', encoding='utf8') as f:
            json.dump(db_parameters, f, ensure_ascii=False) 
    except Exception as err:
        print(err)
    finally:
        is_db_updating = False

def loadWords(wordLen):    # Считывание словаря, отладочная функция.
    words = []
    with open('words'+str(wordLen)+'.txt','r') as f:
        for word in f:
            words.append(word.strip("\n\t "))
    count = len(words)
    return words, count

def getStrPos(x, y):
    if x<32:
        yNew = y
        xNew = x-8
    else:
        yNew = y+17
        xNew = x-32
    return (yNew*12+xNew)

def getStrCoords(strPos):
    if strPos<204:
        y = int(strPos / 12)
        x = strPos%12 + 8
    else:
        y = int(strPos / 12) - 17
        x = strPos%12 + 32
    return (x, y)

def checkWordPosition(charIndex, wordStr):   # Символ проверим на всякий случай
    if not wordStr[charIndex].isalpha():
        return ('', -1, -1)
    i = charIndex
    while wordStr[i].isalpha():
        if i == 0:
            i = -1
            break
        i -= 1
    startPos = i + 1
    i = charIndex
    while wordStr[i].isalpha():
        if i == len(wordStr)-1:
            i = len(wordStr)
            break
        i += 1
    endPos = i - 1
    selWord = wordStr[startPos:endPos+1]
    return (selWord, startPos, endPos)

def checkCheatPosition(charIndex, wordStr):
    leftPar = ['[', '(', '{', '<']
    rightPar = [']', ')', '}', '>']
    direct = 0
    startPos = -1
    endPos = -1
    if wordStr[charIndex] in leftPar:
        direct = 1
        startPos = charIndex
        controlChar = rightPar[leftPar.index(wordStr[charIndex])]
    if wordStr[charIndex] in rightPar:
        direct = -1
        endPos = charIndex - 1
        controlChar = leftPar[rightPar.index(wordStr[charIndex])]
    if direct == 0:
        return('', -1, -1)
    i = charIndex + direct
    if i > (len(wordStr)-1) or i < 0:
        return('', -1, -1)
    startSubStr = int(charIndex/12)*12
    endSubStr = startSubStr + 11
    i = charIndex
    while wordStr[i] != controlChar:
        if wordStr[i].isalpha():
            return ('', -1, -1)
        i += direct
        if i <= startSubStr or i > endSubStr:
            return ('', -1, -1)
    if startPos == -1:
        startPos = i
    if endPos == -1:
        endPos = i - 1
    cheatStr = wordStr[startPos:endPos+2]
    return(cheatStr, startPos, endPos)

def delFromStr(allStr, startPos, endPos):
    newStr = allStr[0:startPos] + '.'*(endPos-startPos) + allStr[endPos:]
    return (newStr)

def genString(wordQuan, strLen, dictionary):
    # Функция формирует строку для вывода в терминал. Строка представляет собой 'мусорные' символы,
    # между которыми вставлены слова для подбора пароля.
    password = dictionary[random.randint(0, len(dictionary)-1)]
    wordLen = len(dictionary[0])
    wordList = wordsSelect(dictionary, password, wordQuan)
    screenStr = ""
    lenArea = int(strLen / wordQuan)
    i = 0
    while i < wordQuan:
        startPos = random.randint(i * lenArea, i * lenArea + (lenArea - wordLen - 1) )
        j = i * lenArea
        while j < startPos:
            screenStr += random.choice(string.punctuation)
            j += 1
        screenStr += wordList[i]
        screenStr += random.choice(string.punctuation)
        j += wordLen + 1
        while j < (i + 1) * lenArea:
            screenStr += random.choice(string.punctuation)
            j += 1
        i += 1
    i = len(screenStr)
    while i < strLen:
        screenStr += random.choice(string.punctuation)
        i += 1
    wordList.remove(password)
    return password, wordList, screenStr

def compareWords(fWord, sWord):
    i = 0
    count = 0
    for char in fWord:
        if char == sWord[i]:
            count += 1
        i += 1
    return count

def wordsSelect(words, pwd, wordQuan):
    wordLen = len(pwd)
    wordListMax = []    # Слова, максимально похожие по расположению букв на слово-пароль
    wordListZero = []   # Слова, совершенно не имеющие одинаково расположенных букв с паролем
    wordListOther = []  # Все прочие слова из списка
    wordListSelected = []  # Слова, которые будут использоваться непосредственно в игре
    wordDelta = 2
    while len(wordListMax) == 0:
        i = 0
        for word in words:
            if word != pwd:
                c = compareWords(word, pwd)
                if c == 0:
                    wordListZero.append(word)
                elif c == (wordLen - 1):
                    wordListMax.append(word)
                elif c == (wordLen - wordDelta):
                        wordListMax.append(word)
                else:
                    wordListOther.append(word)
        wordDelta += 1
    wordListSelected.append(pwd)    # Пароль
    if len(wordListMax) > 0:    # Одно слово, максимально близкое к паролю
        wordListSelected.append(wordListMax[random.randint(0, len(wordListMax) - 1)])
    if len(wordListZero) > 0:   #Одно слово, которое совершенно не похоже на пароль
        wordListSelected.append(wordListZero[random.randint(0, len(wordListZero) - 1)])
    i = 0
    while i < wordQuan - 3:        # Добавляем ещё слов из общего списка
        word = wordListOther[random.randint(0, len(wordListOther) - 1)]
        if word not in wordListSelected:
            wordListSelected.append(word)
            i += 1
    random.shuffle(wordListSelected)    #Перемешиваем.
    return wordListSelected

def delRandomWord(wordList, allStr):
    wordNum = random.randint(0, len(wordList) - 1)
    # print (wordNum)
    word = wordList[wordNum]
    startPos = allStr.index(word)
    wordList.remove(word)
    allStr = allStr.replace(word, '.'*len(word))
    return (startPos, wordList, allStr)

def typeWriter(winOut, textOut, delayTime):
    global db_parameters
    curses.curs_set(2)
    winOut.clear()
    winOut.refresh()
    winOut.nodelay(True)
    myDelay = delayTime
    x = 0
    y = 0
    for ch in textOut:
        key = winOut.getch()
        if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == delayTime:
            myDelay = delayTime/4
        if ch == '\n':
            y += 1
            x = 0
            continue
#        if db_parameters['isSound']:
#            prtSnd.play(loops=0, maxtime=int(myDelay))
        winOut.addstr(y, x, ch, curses.color_pair(1)|curses.A_BOLD)
        time.sleep(myDelay / 1000)
        winOut.refresh()
        x += 1

def outScreen(parName, delayAfter=2):
    global db_parameters
    global delayTime
    global prtSnd
    curses.curs_set(2)
    fullScreenWin = curses.newwin(24, 80, db_parameters["deltaY"], db_parameters["deltaX"])
    fullScreenWin.clear()
    fullScreenWin.refresh()
    fullScreenWin.nodelay(True)
    typeWriter(fullScreenWin, db_parameters[parName], delayTime)
    if delayAfter > 0:
        time.sleep(delayAfter)
        fullScreenWin.clear()
        fullScreenWin.refresh()

def hackScreen():
    global db_parameters
    global db_updated
    global delayTime
    global wrdSnd
    global prtSnd
    curses.curs_set(2)
    (wordDict, lenDict) = loadWords(db_parameters['wordLength'])  # отладочная загрузка словаря
    (pwd, wList, fullStr) = genString(db_parameters['wordsPrinted'], 408, wordDict)
    # fullStr = load_str()
    # pwd = 'FRIERSON'
    # wList = ['INUKSHUK', 'STARLESS', 'HARTWICK', 'FRIERSON', 'DRUMMING', 'SWIMMING',
    #         'DERISIVE', 'MUTATION', 'ADHERENT', 'DRUMLINE', 'WHITMORE', 'PISHOGUE',
    #         'DODDERER', 'CAROLINA', 'WILLHITE', 'UNDERJAW']
    auxStr = [' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, \
              ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32]
    hackServWin = curses.newwin(7, 80, db_parameters["deltaY"], db_parameters["deltaX"])
    hackMainWin = curses.newwin(18, 44, 7+db_parameters["deltaY"], db_parameters["deltaX"])
    hackCursorWin = curses.newwin(18, 3, 7+db_parameters["deltaY"], 44+db_parameters["deltaX"])
    hackAuxWin = curses.newwin(17, 33, 7+db_parameters["deltaY"], 47+db_parameters["deltaX"])
    hackHLWin = curses.newwin(1, 33, 23+db_parameters["deltaY"], 47+db_parameters["deltaY"])
    hackServWin.clear()
    hackServWin.nodelay(True)
    hackMainWin.clear()
    hackMainWin.nodelay(True)
    triesAst = '* ' * db_parameters['attempts']
    numTries = db_parameters['attempts']
    typeWriter(hackServWin, db_parameters['hackHeader'].format(numTries, triesAst), delayTime)
    startHex = random.randint(0x1A00, 0xFA00)
    colStr = 0
    myDelay = delayTime
    while colStr<2:
        y = 0
        while y < 17:
            x = 0
            hexOut = '{0:#4X}  '.format(startHex + y * 12 + colStr*204)
            for ch in hexOut:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == delayTime:
                    myDelay = delayTime / 4
#                if db_parameters['isSound']:
#                    prtSnd.play(loops=0, maxtime=int(myDelay))
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
            i = 0
            for ch in fullStr[(y+colStr*17)*12:(y+colStr*17)*12+12]:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == delayTime:
                    myDelay = delayTime / 4
#                if db_parameters['isSound']:
#                    prtSnd.play(loops=0, maxtime=int(myDelay))
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
                i += 10
            y += 1
        colStr += 1
    hackCursorWin.addstr(16,1,'>',curses.color_pair(1)|curses.A_BOLD)
    hackCursorWin.refresh()
    x = 8
    y = 0
    hackMainWin.move(y, x)
    hackMainWin.nodelay(False)
    hackMainWin.keypad(True)
    wordFlag = False
    cheatFlag = False
    mssTime = millis()
    while True:         # Основной цикл
        mscTime = millis()
        if (mscTime >= (mssTime + 3000)):
            mssTime = mscTime
            # Читаем базу
            if not db_parameters["isPowerOn"] or db_parameters["isLocked"] or db_parameters["isHacked"]:
                return
            if db_updated:
                db_updated = False
                return
        f = False
        key = hackMainWin.getch()
        if key == curses.KEY_LEFT or key == 260:
            f = True
            if x == 8:
                x = 43
            elif x == 32:
                x = 19
            else:
                x -= 1
        if key == curses.KEY_RIGHT or key == 261:
            f = True
            if x == 19:
                x = 32
            elif x == 43:
                x = 8
            else:
                x += 1
        if key == curses.KEY_UP or key == 259:
            f = True
            if y == 0:
                y = 16
            else:
                y -= 1
        if key == curses.KEY_DOWN or key == 258:
            f = True
            if y == 16:
                y = 0
            else:
                y += 1
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            # Выбор позиции
            if wordFlag:
                dWord = compareWords(selGroup, pwd)
                if dWord < db_parameters['wordLength']:
                    auxStr.pop(0)
                    auxStr.append(selGroup + ' ['+str(dWord)+' OF '+str(db_parameters['wordLength'])+']')
                    yAux = 0
                    for tStr in auxStr:
                        hackAuxWin.addstr(yAux, 0, tStr+'\n', curses.color_pair(1)|curses.A_BOLD)
                        yAux += 1
                    hackAuxWin.refresh()
                    numTries -= 1
                    if numTries > 0:
                        triesAst = '* ' * numTries
                        yS = 1
                        xS = 0
                        hackServWin.clear()
                        for ch in db_parameters['hackHeader'].format(numTries, triesAst):
                            if ch == '\n':
                                yS += 1
                                xS = 0
                                continue
                            hackServWin.addstr(yS, xS, ch, curses.color_pair(1)|curses.A_BOLD)
                            xS += 1
                        hackServWin.refresh()
                        hackMainWin.move(y, x)
                    else:   # Блокировка
                        db_parameters["isLocked"] = True
                        updateDBParameters()
                        time.sleep(1)
                        return
                else:   # Терминал успешно взломан
                    db_parameters["isHacked"] = True
                    updateDBParameters()
                    hackMainWin.clear()
                    hackMainWin.refresh()
                    return
            elif cheatFlag: # Был найден чит
                fullStr = delFromStr(fullStr, startPos+1, endPos+1)
                (xSC, ySC) = getStrCoords(startPos+1)
                i = 0
                hackMainWin.addstr(ySC, xSC-1, fullStr[startPos], curses.color_pair(1)|curses.A_BOLD)
                while i<len(selGroup)-1:
                    hackMainWin.addstr(ySC, xSC + i, '.', curses.color_pair(1)|curses.A_BOLD)
                    i += 1
                r = random.randint(1,10)
                if r > 1:   # 9 из 10 случаев - удаляем слово
                    (dPos, wList, fullstr) = delRandomWord(wList, fullStr)
                    i = dPos
                    while i < dPos + db_parameters['wordLength']:
                        (dlX, dlY) = getStrCoords(i)
                        hackMainWin.addstr(dlY, dlX, '.', curses.color_pair(1)|curses.A_BOLD)
                        i += 1
                    auxStr.pop(0)
                    auxStr.append('DUMMY REMOVED')
                    yAux = 0
                    for tStr in auxStr:
                        hackAuxWin.addstr(yAux, 0, tStr+'\n', curses.color_pair(1)|curses.A_BOLD)
                        yAux += 1
                    hackAuxWin.refresh()
                    hackMainWin.move(y, x)
                else:
                    numTries = db_parameters['attempts']
                    triesAst = '* ' * numTries
                    yS = 1
                    xS = 0
                    hackServWin.clear()
                    for ch in db_parameters['hackHeader'].format(numTries, triesAst):
                        if ch == '\n':
                            yS += 1
                            xS = 0
                            continue
                        hackServWin.addstr(yS, xS, ch, curses.color_pair(1)|curses.A_BOLD)
                        xS += 1
                    hackServWin.refresh()
                    auxStr.pop(0)
                    auxStr.append('ATTEMPTS RESTORED')
                    yAux = 0
                    for tStr in auxStr:
                        hackAuxWin.addstr(yAux, 0, tStr+'\n', curses.color_pair(1)|curses.A_BOLD)
                        yAux += 1
                    hackAuxWin.refresh()
                cheatFlag = False
                hackMainWin.move(y, x)
        if f:
#            if db_parameters['isSound']:
#                prtSnd.play(loops=0, maxtime=int(myDelay))
            if wordFlag or cheatFlag:
                i = startPos
                xHL = 0
                while i <= endPos:
                    (hlX, hlY) = getStrCoords(i)
                    hackMainWin.addstr(hlY, hlX, fullStr[i], curses.color_pair(1)|curses.A_BOLD)
                    hackHLWin.addstr(0, xHL, ' ', curses.color_pair(1)|curses.A_BOLD)
                    i += 1
                    xHL += 1
                cheatFlag = False
                wordFlag = False
                hackMainWin.refresh()
                hackHLWin.refresh()
            strPos = getStrPos(x,y)
            (selWGroup, startWPos, endWPos) = checkWordPosition(strPos, fullStr)
            (selCGroup, startCPos, endCPos) = checkCheatPosition(strPos, fullStr)
            # print(key, strPos, selWGroup, selCGroup)
            if startWPos >= 0:
                wordFlag = True
                cheatFlag = False
                startPos = startWPos
                endPos = endWPos
                selGroup = selWGroup
            if startCPos >= 0:
                cheatFlag = True
                wordFlag = False
                startPos = startCPos
                endPos = endCPos + 1
                selGroup = selCGroup
            if wordFlag or cheatFlag:
#                if db_parameters['isSound']:
#                    prtSnd.stop()
#                    wrdSnd.play(loops=0)
                i = startPos
                while i <= endPos:
                    (hlX, hlY) = getStrCoords(i)
                    hackMainWin.addstr(hlY, hlX, fullStr[i], curses.color_pair(1)|curses.A_REVERSE)
                    i += 1
                hackHLWin.addstr(0, 0, selGroup, curses.color_pair(1)|curses.A_BOLD)
                hackMainWin.refresh()
                hackHLWin.refresh()
            hackMainWin.move(y, x)

def readScreen(fName):
    global db_parameters
    global db_updated
    global delayTime
    curses.curs_set(2)
    readServWin = curses.newwin(4, 80, db_parameters["deltaY"], db_parameters["deltaX"])
    readServWin.clear()
    readServWin.refresh()
    typeWriter(readServWin, db_parameters['mainHeader'], delayTime)
    with open(fName, 'r') as fh:
        outTxtStr = fh.read()
    outTxtLst = outTxtStr.split('\n')
    readTextPad = curses.newpad(int(len(outTxtLst)/20 + 1)*20, 80)
    for str in outTxtLst:
        readTextPad.addstr(str+'\n', curses.color_pair(1)|curses.A_BOLD)
    readTextPad.refresh(0, 0, 4+db_parameters['deltaY'], db_parameters['deltaX'], 23, 78)
    curses.curs_set(0)
    readServWin.nodelay(False)
    readServWin.keypad(True)
    rowPos = 0
    mssTime = millis()
    while True:
        mscTime = millis()
        if (mscTime >= (mssTime + 3000)):
            mssTime = mscTime
            # Читаем базу
            if not db_parameters["isPowerOn"] or db_parameters["isLocked"] or not db_parameters["isHacked"]:
                return
            if db_updated:
                db_updated = False
                return
        f = False
        readServWin.move(0, 0)
        kb = readServWin.getch()
        if kb == curses.KEY_NPAGE or kb == 338:
            if rowPos < int(len(outTxtLst)/20)*20:
                rowPos += 20
                f = True
        if kb == curses.KEY_PPAGE or kb == 339:
            if rowPos > 0:
                rowPos -= 20
                f = True
        if kb == curses.KEY_BACKSPACE or kb == 27:
            readServWin.clear()
            readServWin.refresh()
            menuScreen()
        if f:
            readTextPad.refresh(rowPos, 0, 4+db_parameters['deltaY'], db_parameters['deltaX'], 23, 78)
            f = False

def menuScreen():
    global db_parameters
    global db_updated
    global delayTime
    curses.curs_set(2)
    menuSel = []
    myDelay = delayTime
    menuServWin = curses.newwin(4, 80, db_parameters['deltaY'], db_parameters['deltaX'])
    menuServWin.clear()
    menuServWin.refresh()
    menuServWin.nodelay(True)
    menuMainWin = curses.newwin(21, 80, 4+db_parameters['deltaY'], db_parameters['deltaX'])
    menuMainWin.clear()
    menuMainWin.refresh()
    typeWriter(menuServWin, db_parameters['menuHeader'], delayTime)
    maxLen= 0
    rows = 0
    for menuItem in db_parameters['textMenu'].keys():
        if maxLen < len(menuItem):
            maxLen = len(menuItem)
        rows += 1
    y = int((21 - rows * 2) / 2)
    x = int((80 - maxLen)/2)
    for menuItem in db_parameters['textMenu'].keys():
        menuMainWin.addstr(y, x, menuItem, curses.color_pair(1) | curses.A_BOLD)
        menuSel.append(menuItem)
        y += 2
    menuPos = 0
    y = int((21 - rows * 2) / 2)
    menuMainWin.addstr(y, x, menuSel[0], curses.color_pair(1) | curses.A_REVERSE)
    menuMainWin.refresh()
    menuMainWin.keypad(True)
    curses.curs_set(0)
    mssTime = millis()
    while True:
        mscTime = millis()
        if (mscTime >= (mssTime + 3000)):
            mssTime = mscTime
            # Читаем базу
            if not db_parameters["isPowerOn"] or db_parameters["isLocked"] or not db_parameters["isHacked"]:
                return
            if db_updated:
                db_updated = False
                return
        f = False
        key = menuMainWin.getch()
        if key == curses.KEY_UP or key == 259:
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_BOLD)
            f = True
            if menuPos == 0:
                menuPos = len(menuSel) - 1
            else:
                menuPos -= 1
        if key == curses.KEY_DOWN or key == 258:
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_BOLD)
            f = True
            if menuPos == len(menuSel) - 1:
                menuPos = 0
            else:
                menuPos += 1
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            # Выбор позиции
            menuServWin.clear()
            menuServWin.refresh()
            menuMainWin.clear()
            menuMainWin.refresh()
            readScreen(db_parameters['textMenu'][menuSel[menuPos]])
        if f:
            y = int((21 - rows * 2) / 2) + 2*menuPos
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_REVERSE)
            menuMainWin.refresh()
            f = False

def passScreen():
    global db_parameters
    global db_updated
    global delayTime
    curses.curs_set(2)
    menuSel = []
    passServWin = curses.newwin(4, 80, db_parameters['deltaY'], db_parameters['deltaX'])
    passServWin.clear()
    passServWin.refresh()
    passServWin.nodelay(True)
    passMainWin = curses.newwin(21, 80, 4+db_parameters['deltaY'], db_parameters['deltaX'])
    passMainWin.clear()
    passMainWin.refresh()
    typeWriter(passServWin, db_parameters['passHeader'], delayTime)
    passMainWin.refresh()
    passMainWin.keypad(True)
    passMainWin.nodelay(False)
    curses.curs_set(0)
    mssTime = millis()
    passPhrase = ''
    maxLen = max(len(db_parameters['passPart']), len(db_parameters['passFull']))
    while True:
        mscTime = millis()
        if (mscTime >= (mssTime + 3000)):
            mssTime = mscTime
            # Читаем базу
            if not db_parameters["isPowerOn"] or db_parameters["isLocked"]:
                return
            if db_updated:
                db_updated = False
                return
        key = passMainWin.getch()
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            db_parameters['isPassed'] = False
            if passPhrase == db_parameters['passPart']:
                db_parameters['wordLength'] = 6
                updateDBParameters()
                return ()
#            elif passPhrase == db_parameters['passFull']:
#                db_parameters['isHacked'] = True
#                updateDBParameters()
#                return ()
            else:
                return()
        elif key == curses.KEY_BACKSPACE or key == 8:
            passPhrase = passPhrase[:-1]
            passMainWin.clear()
            passMainWin.addstr(5, int((80 - maxLen) / 2), '*'*len(passPhrase), curses.color_pair(1) | curses.A_BOLD)
            passMainWin.refresh()
        else:
            if len(passPhrase) < maxLen:
                passPhrase = passPhrase + chr(key)
                passMainWin.clear()
                passMainWin.addstr(5, int((80-maxLen)/2), '*'*len(passPhrase), curses.color_pair(1)|curses.A_BOLD)
                passMainWin.refresh()


def startTerminal():
    #   Основной игровой цикл.
    global db_parameters
    global db_updated
    global forceClose
    global prtSnd
    global wrdSnd
    global lockTimeOutStart
    # Предыдущее состояние терминала. Если не совпадает с текущим - будет выполнена очистка и перерисовка экрана.
    # Unpowerd - нет питания. Locked  - заблокирован. Hacked - взломан. Normal - запитан, ждет взлома.
    previous_state = ""
    initCurses()
#    if db_parameters['isSound']:
#        pygame.mixer.pre_init(44100, -16, 2, 512)
#        pygame.mixer.init()
#        prtSnd = pygame.mixer.Sound('f3termprint.wav')
#        wrdSnd = pygame.mixer.Sound('f3termprint.wav')
    while True:
        db_updated = False
        if forceClose:
            break
        while is_db_updating:   #Ожидаем, пока обновится состояние из БД.
            pass
        # Проверяем: 1. Есть ли питание. 2. Не заблокирован ли терминал.
        # Если все в порядке, показываем игру. После взлома показываем меню.
        if lockTimeOutStart!=0:
            if (millis()-lockTimeOutStart) >= db_parameters["lockTimeOut"]*1000:
                lockTimeOutStart = 0
                db_parameters["isLocked"] = False
                updateDBParameters()
        if not db_parameters["isPowerOn"]:
            if previous_state != "Unpowered":
                outScreen('unPowerHeader', 0)
                previous_state = "Unpowered"
            time.sleep(dbCheckInterval)
        elif db_parameters["isLocked"]:
            if previous_state != "Locked":
                lockTimeOutStart = millis()
                outScreen('lockHeader', 0)
                previous_state = "Locked"
        elif db_parameters["isHacked"]:
            if previous_state != "Hacked":
                previous_state = "Hacked"
                menuScreen()  # Здесь вызываем функцию после взлома
                # forceClose = True   # Закрываем всё
        elif db_parameters["isPassed"]:
            previous_state = "Passed"
            outScreen('startHeader', 3)
            passScreen()
        else:
            # Взлом.
            previous_state = "Normal"
            outScreen('startHeader', 3)
            hackScreen()

if __name__ == "__main__":
    dbThread = threading.Thread(target=readDBParameters, args=(dbCheckInterval,))
    dbThread.start()
    time.sleep(1)
    while is_db_updating:
        # Ожидаем, пока обновится состояние из БД
        pass
    startTerminal()
