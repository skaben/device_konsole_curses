#!/usr/bin/python3
# -*- coding: utf-8 -*-
import curses
import random
import time
import json
import string
import threading
import codecs
import os
from sys import platform

db_parameters = dict()
main_conf = dict()

main_conf['forceClose'] = False
main_conf['is_db_updating'] = False
main_conf['db_updated'] = False
main_conf['previousState'] = ""
main_conf['dbCheckInterval'] = 2
main_conf['delayTime'] = 40
main_conf['lockTimeOutStart'] = 0
main_conf['start_time'] = time.time()
main_conf['conf_path'] = './conf/'
main_conf['conf_name'] = 'ftjSON.txt'
main_conf['screen_path'] = './resources/screens/'
main_conf['text_path'] = './resources/text/'
main_conf['word_path'] = './resources/wordsets/'


def checkStatus():
    global db_parameters, main_conf
    if (not db_parameters["isPowerOn"] and main_conf['previousState'] != "Unpowered") or \
        (db_parameters["isLocked"] and main_conf['previousState'] != "Locked") or \
        (db_parameters["isHacked"] and main_conf['previousState'] != "Hacked"):
        return(True) 
    if main_conf['db_updated']:
        main_conf['db_updated'] = False
    return(False)

def millis():
    global main_conf
    return (time.time() - main_conf['start_time']) * 1000.0

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
    global db_parameters, main_conf
    while True:
        if main_conf['forceClose']:
            break
        if not main_conf['is_db_updating']:
            main_conf['is_db_updating'] = True
            with codecs.open(main_conf['conf_path'] + main_conf['conf_name'], 'r', 'utf-8') as f:
                db_parameters = json.load(f) 
            main_conf['is_db_updating'] = False
        time.sleep(checkInterval)

def updateDBParameters():
    global db_parameters, main_conf
    while main_conf['is_db_updating']:
        pass
    try:
        main_conf['is_db_updating'] = True
        with codecs.open(main_conf['conf_path'] + main_conf['conf_name'], 'w', 'utf-8') as f:
            json.dump(db_parameters, f, ensure_ascii=False) 
    except Exception as err:
        print(err)
    finally:
        main_conf['is_db_updating'] = False

def loadWords(wordLen):    
    global main_conf
    words = []
    with codecs.open(main_conf['word_path'] + 'words' + str(wordLen) + '.txt','r', 'utf-8') as f:
        for word in f:
            words.append(word.strip("\n\t "))
    return words

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
    word = wordList[wordNum]
    startPos = allStr.index(word)
    wordList.remove(word)
    allStr = allStr.replace(word, '.' * len(word))
    return (startPos, wordList, allStr)

def outScreen(parName, delayAfter=2):
    global db_parameters, main_conf
    curses.curs_set(2)
    fullScreenWin = curses.newwin(24, 80, 0, 0)
    fullScreenWin.clear()
    fullScreenWin.refresh()
    fullScreenWin.nodelay(True)
    with codecs.open(main_conf['screen_path'] + db_parameters[parName], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()
    status = outHeader(outTxtStr, fullScreenWin)
    if delayAfter > 0:
        time.sleep(delayAfter)
    return status
 
def outHeader(outStr, win):
    global main_conf
    win.clear()
    win.refresh()
    win.nodelay(True)
    myDelay = main_conf['delayTime']
    y = 0
    x = 0
    for ch in outStr:
        key = win.getch()
        if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
            myDelay = main_conf['delayTime']/4
        if ch == '\n':
            y+=1
            x = 0
            continue
        win.addstr(y, x, ch, curses.color_pair(1)|curses.A_BOLD)
        time.sleep(myDelay / 1000)
        win.refresh()
        x += 1
        if checkStatus():
            return True
    return False

def clearScreen():
    fullScreenWin = curses.newwin(24, 80, 0, 0)
    fullScreenWin.clear()
    fullScreenWin.refresh()

def hackScreen():
    global db_parameters, main_conf
    clearScreen()
    curses.curs_set(2)
    wordDict = loadWords(db_parameters['wordLength'])  
    (pwd, wList, fullStr) = genString(db_parameters['wordsPrinted'], 408, wordDict)
    auxStr = [' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, \
              ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32]
    x = 0
    y = 1
    myDelay = main_conf['delayTime']
    hackServWin = curses.newwin(7, 80, 0, 0)
    hackMainWin = curses.newwin(18, 44, 7, 0)
    hackCursorWin = curses.newwin(18, 3, 7, 44)
    hackAuxWin = curses.newwin(17, 33, 7, 47)
    hackHLWin = curses.newwin(1, 33, 23, 47)
    hackServWin.clear()
    hackServWin.nodelay(True)
    hackMainWin.clear()
    hackMainWin.nodelay(True)
    triesAst = '* ' * db_parameters['attempts']
    numTries = db_parameters['attempts']

    with codecs.open(main_conf['screen_path'] + db_parameters['hackHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()

    if(outHeader(outTxtStr.format(numTries, triesAst), hackServWin)):
        return

    startHex = random.randint(0x1A00, 0xFA00)
    colStr = 0
    while colStr<2:
        y = 0
        while y < 17:
            x = 0
            hexOut = '{0:#4X}  '.format(startHex + y * 12 + colStr*204)
            for ch in hexOut:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
                    myDelay = main_conf['delayTime'] / 4
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
                if checkStatus():
                    return
            i = 0
            for ch in fullStr[(y+colStr*17)*12:(y+colStr*17)*12+12]:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
                    myDelay = main_conf['delayTime'] / 4
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
                i += 10
                if checkStatus():
                    return
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
            if checkStatus():
                return
        f = False
        key = hackMainWin.getch()
        if key == curses.KEY_LEFT or key == 260 or key == ord('A') or key == ord('a'):
            f = True
            if x == 8:
                x = 43
            elif x == 32:
                x = 19
            else:
                x -= 1
        if key == curses.KEY_RIGHT or key == 261 or key == ord('D') or key == ord('d'):
            f = True
            if x == 19:
                x = 32
            elif x == 43:
                x = 8
            else:
                x += 1
        if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
            f = True
            if y == 0:
                y = 16
            else:
                y -= 1
        if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
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
                        for ch in outTxtStr.format(numTries, triesAst):
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
                    for ch in outTxtStr.format(numTries, triesAst):
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
    global db_parameters, main_conf
    curses.curs_set(2)
    readServWin = curses.newwin(4, 80, 0, 0)
    readServWin.clear()
    readServWin.nodelay(True)
    with codecs.open(main_conf['screen_path'] + db_parameters['mainHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()
    if(outHeader(outTxtStr, readServWin)):
        return
    if platform == "linux" or platform == "linux2":
        with open(fName, 'r') as fh: 
            outTxtStr = fh.read()
    else:
        with codecs.open(fName, 'r', 'utf-8') as fh: 
            outTxtStr = fh.read()
    outTxtLst = outTxtStr.split('\n')
    readTextPad = curses.newpad(int(len(outTxtLst)/20 + 1)*20, 80)
    for str in outTxtLst:
        readTextPad.addstr(str+'\n', curses.color_pair(1)|curses.A_BOLD)
    readTextPad.refresh(0, 0, 4, 0, 23, 78)
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
            if checkStatus():
                return
        f = False
        readServWin.move(0, 0)
        key = readServWin.getch()
        if key == curses.KEY_NPAGE or key == 338  or key == ord('S') or key == ord('s'):
            if rowPos < int(len(outTxtLst)/20)*20:
                rowPos += 20
                f = True
        if key == curses.KEY_PPAGE or key == 339 or key == ord('W') or key == ord('w'):
            if rowPos > 0:
                rowPos -= 20
                f = True
        if key == curses.KEY_BACKSPACE or key == 27:
            readServWin.clear()
            readServWin.refresh()
            menuScreen()
        if f:
            readTextPad.refresh(rowPos, 0, 4, 0, 23, 78)
            f = False

def menuScreen():
    global db_parameters, main_conf
    curses.curs_set(2)
    menuSel = []
    menuFullWin = curses.newwin(25, 80, 0, 0)
    menuServWin = curses.newwin(4, 80, 0, 0)
    menuMainWin = curses.newwin(21, 80, 4, 0)
    menuMainWin.clear()
    menuMainWin.refresh()
    x = 0
    y = 0

    with codecs.open(main_conf['screen_path'] + db_parameters['menuHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()

    if(outHeader(outTxtStr, menuServWin)):
        return

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
    while True:
        f = False
        key = menuMainWin.getch()
        if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_BOLD)
            f = True
            if menuPos == 0:
                menuPos = len(menuSel) - 1
            else:
                menuPos -= 1
        if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_BOLD)
            f = True
            if menuPos == len(menuSel) - 1:
                menuPos = 0
            else:
                menuPos += 1
        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            # Выбор позиции
            if db_parameters['textMenu'][menuSel[menuPos]]["type"] == "text":
                menuMainWin.clear()
                menuServWin.clear()
                menuMainWin.refresh()
                menuServWin.refresh()
                readScreen(main_conf['text_path'] + db_parameters['textMenu'][menuSel[menuPos]]["name"])
            elif db_parameters['textMenu'][menuSel[menuPos]]["type"] == "command":
                os.system(db_parameters['textMenu'][menuSel[menuPos]]["name"])
                menuFullWin.clear()
                menuMainWin.refresh()
                menuServWin.refresh()
        if f:
            y = int((21 - rows * 2) / 2) + 2*menuPos
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_REVERSE)
            menuMainWin.refresh()
            f = False

def startTerminal():
    #   Основной игровой цикл.
    global db_parameters, main_conf
    # Предыдущее состояние терминала. Если не совпадает с текущим - будет выполнена очистка и перерисовка экрана.
    # Unpowerd - нет питания. Locked  - заблокирован. Hacked - взломан. Normal - запитан, ждет взлома.
    # Broken - сломан
    initCurses()
    while True:
        main_conf['db_updated'] = False
        if main_conf['forceClose']:
            break
#        checkStatus()
        while main_conf['is_db_updating']:   # Ожидаем, пока обновится состояние из БД.
            pass
        updateDBParameters()
        if main_conf['lockTimeOutStart']!=0:
            if (millis()-main_conf['lockTimeOutStart']) >= db_parameters["lockTimeOut"]*1000:
                main_conf['lockTimeOutStart'] = 0
                db_parameters["isLocked"] = False
                updateDBParameters()
        if not db_parameters["isPowerOn"]:
            if main_conf['previousState'] != "Unpowered":
                main_conf['previousState'] = "Unpowered"
                outScreen('unPowerHeader', 0)
                updateDBParameters()
            time.sleep(main_conf['dbCheckInterval'])
        elif db_parameters["isLocked"]:
            if main_conf['previousState'] != "Locked":
                main_conf['lockTimeOutStart'] = millis()
                main_conf['previousState'] = "Locked"
                outScreen('lockHeader', 0)
                updateDBParameters()
        elif db_parameters["isHacked"]:
            if main_conf['previousState'] != "Hacked":
                main_conf['previousState'] = "Hacked"
                menuScreen()  # Здесь вызываем функцию после взлома
                # main_conf['forceClose'] = True   # Закрываем всё
        else:
            # Взлом.
            main_conf['previousState'] = "Normal"
            outScreen('startHeader', 3)
            hackScreen()

if __name__ == "__main__":
    dbThread = threading.Thread(target=readDBParameters, args=(main_conf['dbCheckInterval'],))
    dbThread.start()
    time.sleep(1)
    while main_conf['is_db_updating']:
        # Ожидаем, пока обновится состояние из БД
        pass
    startTerminal()
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import curses
import random
import time
import json
import string
import threading
import codecs

db_parameters = dict()
main_conf = dict()

main_conf['forceClose'] = False
main_conf['is_db_updating'] = False
main_conf['db_updated'] = False
main_conf['previousState'] = ""
main_conf['dbCheckInterval'] = 2
main_conf['delayTime'] = 40
main_conf['lockTimeOutStart'] = 0
main_conf['start_time'] = time.time()
main_conf['conf_path'] = './conf/'
main_conf['conf_name'] = 'ftjSON.txt'
main_conf['screen_path'] = './resources/screens/'
main_conf['text_path'] = './resources/text/'
main_conf['word_path'] = './resources/wordsets/'


def checkStatus():
    global db_parameters, main_conf
    if (not db_parameters["isPowerOn"] and main_conf['previousState'] != "Unpowered") or \
        (db_parameters["isLocked"] and main_conf['previousState'] != "Locked") or \
        (db_parameters["isHacked"] and main_conf['previousState'] != "Hacked"):
        return(True) 
    if main_conf['db_updated']:
        main_conf['db_updated'] = False
    return(False)

def millis():
    global main_conf
    return (time.time() - main_conf['start_time']) * 1000.0

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
    global db_parameters, main_conf
    while True:
        if main_conf['forceClose']:
            break
        if not main_conf['is_db_updating']:
            main_conf['is_db_updating'] = True
            with codecs.open(main_conf['conf_path'] + main_conf['conf_name'], 'r', 'utf-8') as f:
                db_parameters = json.load(f) 
            main_conf['is_db_updating'] = False
        time.sleep(checkInterval)

def updateDBParameters():
    global db_parameters, main_conf
    while main_conf['is_db_updating']:
        pass
    try:
        main_conf['is_db_updating'] = True
        with codecs.open(main_conf['conf_path'] + main_conf['conf_name'], 'w', 'utf-8') as f:
            json.dump(db_parameters, f, ensure_ascii=False) 
    except Exception as err:
        print(err)
    finally:
        main_conf['is_db_updating'] = False

def loadWords(wordLen):    
    global main_conf
    words = []
    with codecs.open(main_conf['word_path'] + 'words' + str(wordLen) + '.txt','r', 'utf-8') as f:
        for word in f:
            words.append(word.strip("\n\t "))
    return words

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
    word = wordList[wordNum]
    startPos = allStr.index(word)
    wordList.remove(word)
    allStr = allStr.replace(word, '.' * len(word))
    return (startPos, wordList, allStr)

def outScreen(parName, delayAfter=2):
    global db_parameters, main_conf
    curses.curs_set(2)
    fullScreenWin = curses.newwin(24, 80, 0, 0)
    fullScreenWin.clear()
    fullScreenWin.refresh()
    fullScreenWin.nodelay(True)
    with codecs.open(main_conf['screen_path'] + db_parameters[parName], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()
    status = outHeader(outTxtStr, fullScreenWin)
    if delayAfter > 0:
        time.sleep(delayAfter)
    return status
 
def outHeader(outStr, win):
    global main_conf
    win.clear()
    win.refresh()
    win.nodelay(True)
    myDelay = main_conf['delayTime']
    y = 0
    x = 0
    for ch in outStr:
        key = win.getch()
        if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
            myDelay = main_conf['delayTime']/4
        if ch == '\n':
            y+=1
            x = 0
            continue
        win.addstr(y, x, ch, curses.color_pair(1)|curses.A_BOLD)
        time.sleep(myDelay / 1000)
        win.refresh()
        x += 1
        if checkStatus():
            return True
    return False

def clearScreen():
    fullScreenWin = curses.newwin(24, 80, 0, 0)
    fullScreenWin.clear()
    fullScreenWin.refresh()

def hackScreen():
    global db_parameters, main_conf
    clearScreen()
    curses.curs_set(2)
    wordDict = loadWords(db_parameters['wordLength'])  
    (pwd, wList, fullStr) = genString(db_parameters['wordsPrinted'], 408, wordDict)
    auxStr = [' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, \
              ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32, ' '*32]
    x = 0
    y = 1
    myDelay = main_conf['delayTime']
    hackServWin = curses.newwin(7, 80, 0, 0)
    hackMainWin = curses.newwin(18, 44, 7, 0)
    hackCursorWin = curses.newwin(18, 3, 7, 44)
    hackAuxWin = curses.newwin(17, 33, 7, 47)
    hackHLWin = curses.newwin(1, 33, 23, 47)
    hackServWin.clear()
    hackServWin.nodelay(True)
    hackMainWin.clear()
    hackMainWin.nodelay(True)
    triesAst = '* ' * db_parameters['attempts']
    numTries = db_parameters['attempts']

    with codecs.open(main_conf['screen_path'] + db_parameters['hackHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()

    if(outHeader(outTxtStr.format(numTries, triesAst), hackServWin)):
        return

    startHex = random.randint(0x1A00, 0xFA00)
    colStr = 0
    while colStr<2:
        y = 0
        while y < 17:
            x = 0
            hexOut = '{0:#4X}  '.format(startHex + y * 12 + colStr*204)
            for ch in hexOut:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
                    myDelay = main_conf['delayTime'] / 4
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
                if checkStatus():
                    return
            i = 0
            for ch in fullStr[(y+colStr*17)*12:(y+colStr*17)*12+12]:
                key = hackMainWin.getch()
                if (key == curses.KEY_ENTER or key == ord(' ')) and myDelay == main_conf['delayTime']:
                    myDelay = main_conf['delayTime'] / 4
                hackMainWin.addstr(y, (colStr*24)+x, ch, curses.color_pair(1)|curses.A_BOLD)
                time.sleep(myDelay / 1000)
                hackMainWin.refresh()
                x += 1
                i += 10
                if checkStatus():
                    return
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
            if checkStatus():
                return
        f = False
        key = hackMainWin.getch()
        if key == curses.KEY_LEFT or key == 260 or key == ord('A') or key == ord('a'):
            f = True
            if x == 8:
                x = 43
            elif x == 32:
                x = 19
            else:
                x -= 1
        if key == curses.KEY_RIGHT or key == 261 or key == ord('D') or key == ord('d'):
            f = True
            if x == 19:
                x = 32
            elif x == 43:
                x = 8
            else:
                x += 1
        if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
            f = True
            if y == 0:
                y = 16
            else:
                y -= 1
        if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
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
                        for ch in outTxtStr.format(numTries, triesAst):
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
                    for ch in outTxtStr.format(numTries, triesAst):
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
    global db_parameters, main_conf
    curses.curs_set(2)
    readServWin = curses.newwin(4, 80, 0, 0)
    readServWin.clear()
    readServWin.nodelay(True)
    x = 0
    y = 0

    with codecs.open(main_conf['screen_path'] + db_parameters['mainHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()

    if(outHeader(outTxtStr, readServWin)):
        return

    with codecs.open(fName, 'r', 'utf-8') as fh: #!!!
        outTxtStr = fh.read()
   
    outTxtLst = outTxtStr.split('\n')
    readTextPad = curses.newpad(int(len(outTxtLst)/20 + 1)*20, 80)
    for str in outTxtLst:
        readTextPad.addstr(str+'\n', curses.color_pair(1)|curses.A_BOLD)
    readTextPad.refresh(0, 0, 4, 0, 23, 78)
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
            if checkStatus():
                return
        f = False
        readServWin.move(0, 0)
        key = readServWin.getch()
        if key == curses.KEY_NPAGE or key == 338  or key == ord('S') or key == ord('s'):
            if rowPos < int(len(outTxtLst)/20)*20:
                rowPos += 20
                f = True
        if key == curses.KEY_PPAGE or key == 339 or key == ord('W') or key == ord('w'):
            if rowPos > 0:
                rowPos -= 20
                f = True
        if key == curses.KEY_BACKSPACE or key == 27:
            readServWin.clear()
            readServWin.refresh()
            menuScreen()
        if f:
            readTextPad.refresh(rowPos, 0, 4, 0, 23, 78)
            f = False

def menuScreen():
    global db_parameters, main_conf
    curses.curs_set(2)
    menuSel = []
    menuServWin = curses.newwin(4, 80, 0, 0)
    menuMainWin = curses.newwin(21, 80, 4, 0)
    menuMainWin.clear()
    menuMainWin.refresh()
    x = 0
    y = 0

    with codecs.open(main_conf['screen_path'] + db_parameters['menuHeader'], 'r', 'utf-8') as fh:
        outTxtStr = fh.read()

    if(outHeader(outTxtStr, menuServWin)):
        return

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
    while True:
        f = False
        key = menuMainWin.getch()
        if key == curses.KEY_UP or key == 259 or key == ord('W') or key == ord('w'):
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_BOLD)
            f = True
            if menuPos == 0:
                menuPos = len(menuSel) - 1
            else:
                menuPos -= 1
        if key == curses.KEY_DOWN or key == 258 or key == ord('S') or key == ord('s'):
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
            if db_parameters['textMenu'][menuSel[menuPos]]["type"] == "text":
                readScreen(main_conf['text_path'] + db_parameters['textMenu'][menuSel[menuPos]]["name"])
        if f:
            y = int((21 - rows * 2) / 2) + 2*menuPos
            menuMainWin.addstr(y, x, menuSel[menuPos], curses.color_pair(1) | curses.A_REVERSE)
            menuMainWin.refresh()
            f = False

def startTerminal():
    #   Основной игровой цикл.
    global db_parameters, main_conf
    # Предыдущее состояние терминала. Если не совпадает с текущим - будет выполнена очистка и перерисовка экрана.
    # Unpowerd - нет питания. Locked  - заблокирован. Hacked - взломан. Normal - запитан, ждет взлома.
    # Broken - сломан
    initCurses()
    while True:
        main_conf['db_updated'] = False
        if main_conf['forceClose']:
            break
#        checkStatus()
        while main_conf['is_db_updating']:   # Ожидаем, пока обновится состояние из БД.
            pass
        updateDBParameters()
        if main_conf['lockTimeOutStart']!=0:
            if (millis()-main_conf['lockTimeOutStart']) >= db_parameters["lockTimeOut"]*1000:
                main_conf['lockTimeOutStart'] = 0
                db_parameters["isLocked"] = False
                updateDBParameters()
        if not db_parameters["isPowerOn"]:
            if main_conf['previousState'] != "Unpowered":
                main_conf['previousState'] = "Unpowered"
                outScreen('unPowerHeader', 0)
                updateDBParameters()
            time.sleep(main_conf['dbCheckInterval'])
        elif db_parameters["isLocked"]:
            if main_conf['previousState'] != "Locked":
                main_conf['lockTimeOutStart'] = millis()
                main_conf['previousState'] = "Locked"
                outScreen('lockHeader', 0)
                updateDBParameters()
        elif db_parameters["isHacked"]:
            if main_conf['previousState'] != "Hacked":
                main_conf['previousState'] = "Hacked"
                menuScreen()  # Здесь вызываем функцию после взлома
                # main_conf['forceClose'] = True   # Закрываем всё
        else:
            # Взлом.
            main_conf['previousState'] = "Normal"
            outScreen('startHeader', 3)
            hackScreen()

if __name__ == "__main__":
    dbThread = threading.Thread(target=readDBParameters, args=(main_conf['dbCheckInterval'],))
    dbThread.start()
    time.sleep(1)
    while main_conf['is_db_updating']:
        # Ожидаем, пока обновится состояние из БД
        pass
    startTerminal()
