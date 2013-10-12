#Embedded file name: /Volumes/Home/development/goprodumper/lcd_menu.py
import time
import os
import Queue
from emulator import emulator as plate
import datetime
import threading
import atexit
import traceback
from exception import MenuBuildingException

class EventQueue(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.message_queue = Queue.Queue()
        self.alive = threading.Event()
        self.alive.set()

    def invokeLater(self, instruction):
        try:
            self.message_queue.put_nowait(instruction)
        except Queue.Full:
            return False

        return True

    def invokeAndWait(self, instruction):
        self.message_queue.put(instruction, True)

    def run(self):
        while self.alive.is_set():
            self.processInstruction(self.message_queue.get())

    def close(self):
        self.alive.clear()

    def processInstruction(self, instruction):
        pass


class LcdEventQueue(EventQueue):
    REFRESH_FIRST_LINE = 0
    REFRESH_SECOND_LINE = 1
    REFRESH_ALL = 2
    CLEAR = 3
    SHUTDOWN = 4
    KILL = 5

    def __init__(self, lcd):
        EventQueue.__init__(self)
        self.lcd = lcd
        self.firstLine = ''
        self.secondLine = ''

    def processInstruction(self, instruction):
        code, param1, param2 = instruction
        if code == LcdEventQueue.REFRESH_FIRST_LINE:
            self.firstLine = param1
            self.lcd.clear()
            self.lcd.message(self.firstLine + '\n' + self.secondLine)
        elif code == LcdEventQueue.REFRESH_SECOND_LINE:
            self.secondLine = param1
            self.lcd.clear()
            self.lcd.message(self.firstLine + '\n' + self.secondLine)
        elif code == LcdEventQueue.REFRESH_ALL:
            self.firstLine = param1
            self.secondLine = param2
            self.lcd.clear()
            self.lcd.message(self.firstLine + '\n' + self.secondLine)
        elif code == LcdEventQueue.CLEAR:
            self.lcd.clear()
        elif code == LcdEventQueue.SHUTDOWN:
            self.lcd.clear()
            if param1 == None:
                self.lcd.message('Shutdown...')
            else:
                self.lcd.message(param1)
            self.close()
        elif code == LcdEventQueue.KILL:
            self.close()


class LcdManager(object):

    def __init__(self, lcd, root_menu_item = None):
        atexit.register(self.onExit)
        self.eventQueue = LcdEventQueue(lcd)
        self.eventQueue.start()
        self.lcd = lcd
        self.btn = []
        self.setCurrentItem(root_menu_item)

    def onExit(self):
        self.eventQueue.close()
        self.eventQueue.invokeLater((LcdEventQueue.KILL, None, None))

    def setCurrentItem(self, menu_item):
        if menu_item != None:
            self.btn = menu_item.getButtonMapping()
            self.eventQueue.invokeLater((LcdEventQueue.REFRESH_ALL, menu_item.getFirstLine(), menu_item.getSecondLine()))
        else:
            self.eventQueue.invokeLater((LcdEventQueue.CLEAR, None, None))

    def getEventQueue(self):
        return self.eventQueue

    def start_loop(self):
        try:
            prev = -1
            while True:
                found = False
                for b in self.btn:
                    if self.lcd.buttonPressed(b[0]):
                        found = True
                        if b[0] != prev:
                            self.setCurrentItem(b[1]())
                            prev = b[0]
                        break

                if not found:
                    prev = -1

        except BaseException as ex:
            traceback.print_exc()
            self.eventQueue.invokeLater((LcdEventQueue.KILL, None, None))


class Lcd_item(object):

    def execute(self):
        """execute un traitement sur le menu courant lors de l'appui sur le bouton select"""
        return self

    def executeOnPush(self):
        """methode appelle par un parent lorsque le noeud courant est selectionne avec le bouton lors de son affichage dans le menu parent"""
        return self

    def executeOnSelect(self):
        """execute un traitement sur un child lorsqu'un item est selectionne"""
        pass

    def executeOnDeselect(self):
        """execute un traitement sur un child lorsqu'un item etait precedement selectionne"""
        pass

    def getParent(self):
        return self

    def setParent(self):
        pass

    def up(self):
        return self

    def down(self):
        return self

    def left(self):
        return self

    def right(self):
        return self

    def getName(self):
        return '-- name not set --'

    def getFirstLine(self):
        return ''

    def getSecondLine(self):
        return ''

    def getButtonMapping(self):
        return ((plate.LEFT, self.left),
         (plate.UP, self.up),
         (plate.DOWN, self.down),
         (plate.RIGHT, self.right),
         (plate.SELECT, self.execute))


class Lcd_content_item(Lcd_item):

    def __init__(self, init_content = [], two_line = False):
        self.content = init_content
        self.contentIndex = 0
        self.onTwoLine = two_line
        self.init_content = init_content

    def restoreInitialContent(self):
        self.content = self.init_content
        self.contentIndex = 0

    def setContent(self, content):
        self.content = content
        self.contentIndex = 0

    def up(self):
        if len(self.content) == 0:
            return
        if self.contentIndex == 0:
            self.contentIndex = len(self.content)
        self.contentIndex -= 1
        return self

    def down(self):
        if len(self.content) == 0:
            return
        self.contentIndex = (self.contentIndex + 1) % len(self.content)
        return self

    def getFirstLine(self):
        if len(self.content) > 0:
            return self.content[self.contentIndex]
        return ''

    def getSecondLine(self):
        pass


class Lcd_menu_item(Lcd_content_item):

    def __init__(self, Name, enableBackMenu = True, parent = None):
        Lcd_content_item.__init__(self, (Name,), False)
        self.Name = Name
        self.parent = parent
        self.menuIndex = 0
        self.childItems = []
        self.childItems.append(backMenuItem(self))

    def addChild(self, child):
        back_menu = self.childItems[-1]
        self.childItems[-1] = child
        self.childItems.append(back_menu)
        child.setParent(self)
        return child

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def getName(self):
        return self.Name

    def left(self):
        if len(self.childItems) == 0:
            self.menuIndex = 0
            return self
        self.childItems[self.menuIndex].executeOnDeselect()
        if self.menuIndex == 0:
            self.menuIndex = len(self.childItems)
        self.menuIndex -= 1
        self.childItems[self.menuIndex].executeOnSelect()
        return self

    def right(self):
        if len(self.childItems) == 0:
            self.menuIndex = 0
            return self
        self.childItems[self.menuIndex].executeOnDeselect()
        self.menuIndex = (self.menuIndex + 1) % len(self.childItems)
        self.childItems[self.menuIndex].executeOnSelect()
        return self

    def execute(self):
        if len(self.childItems) == 0:
            return self
        return self.childItems[self.menuIndex].executeOnPush()

    def executeOnPush(self):
        if len(self.childItems) > 0:
            self.childItems[self.menuIndex].executeOnSelect()
        return Lcd_content_item.executeOnPush(self)

    def getSecondLine(self):
        if len(self.childItems) == 0:
            return '-- no menu --'
        return self.childItems[self.menuIndex].getName()


class InformationMenuItem(Lcd_item):
    """ce menu change juste l'affichage du content du parent lorsqu'il est survole"""

    def __init__(self, Name, methToRefreshContent, parent = None, refreshOnlyOnPush = True):
        self.parent = parent
        self.methToRefreshContent = methToRefreshContent
        self.content = methToRefreshContent()
        self.refreshOnlyOnPush = refreshOnlyOnPush
        self.Name = Name

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def executeOnPush(self):
        self.content = self.methToRefreshContent()
        self.getParent().setContent(self.content)
        return self.getParent()

    def executeOnSelect(self):
        if not self.refreshOnlyOnPush:
            self.content = self.methToRefreshContent()
        self.getParent().setContent(self.content)

    def executeOnDeselect(self):
        self.getParent().restoreInitialContent()

    def getName(self):
        return self.Name


class StaticInformationMenuItem(Lcd_item):
    """ce menu change juste l'affichage du content du parent lorsqu'il est survole"""

    def __init__(self, Name, information, parent = None):
        self.parent = parent
        self.content = information
        self.Name = Name

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def executeOnPush(self):
        self.getParent().setContent(self.content)
        return self.getParent()

    def executeOnSelect(self):
        self.getParent().setContent(self.content)

    def executeOnDeselect(self):
        self.getParent().restoreInitialContent()

    def getName(self):
        return self.Name


class SimpleProcessMenuItem(Lcd_item):
    """Ce menu execute un process simple lors de son survol ou de son clic mais ne modifie pas l'affichage"""

    def __init__(self, name, function = None, OnPush = True, OnSelect = False, backToGreatParent = True, parent = None):
        self.parent = parent
        self.name = name
        self.OnSelect = OnSelect
        self.OnPush = OnPush
        self.function = function
        self.backToGreatParent = backToGreatParent

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def executeOnPush(self):
        if not self.OnSelect and self.OnPush:
            if self.function != None:
                self.function()
        if self.backToGreatParent and self.getParent().getParent() != None:
            return self.getParent().getParent()
        return self.getParent()

    def executeOnSelect(self):
        if self.OnSelect:
            if self.function != None:
                self.function()

    def getName(self):
        return self.name


class BooleanMenuItem(Lcd_menu_item):
    """ce menu possede deux sous menu yes/no"""

    def __init__(self, Name, actionOnYes = None, actionOnNo = None, yesText = 'Yes', noText = 'No', OnPush = True, OnSelect = False, parent = None):
        Lcd_menu_item.__init__(self, Name, False, parent)
        self.addChild(SimpleProcessMenuItem(yesText, actionOnYes, OnPush, OnSelect))
        self.addChild(SimpleProcessMenuItem(noText, actionOnNo, OnPush, OnSelect))


class backMenuItem(SimpleProcessMenuItem):
    """ce menu permet de revenir au menu parent"""

    def __init__(self, parent):
        if not isinstance(parent, Lcd_menu_item):
            raise MenuBuildingException('The parent object can only be a Lcd_menu_item object, current type is ' + str(type(picker)))
        SimpleProcessMenuItem.__init__(self, 'retour', self.toExecuteOnPush, True, False, True, parent)

    def toExecuteOnPush(self):
        self.parent.menuIndex = 0


class PickerMenuItem(Lcd_item):

    def __init__(self, pickerName, parent = None, separator = ' '):
        self.parent = parent
        self.pickerName = pickerName
        self.separator = separator
        self.selectedElementIndex = 0

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        return self.parent

    def up(self):
        self.changeElementValuePlus(self.selectedElementIndex)
        return self

    def down(self):
        self.changeElementValueMinus(self.selectedElementIndex)
        return self

    def left(self):
        if self.selectedElementIndex == 0:
            self.selectedElementIndex = self.getElementCount()
        self.selectedElementIndex -= 1
        return self

    def right(self):
        self.selectedElementIndex = (self.selectedElementIndex + 1) % self.getElementCount()
        return self

    def execute(self):
        self.saveValue()
        return self.getParent()

    def executeOnPush(self):
        return self

    def getName(self):
        return self.pickerName

    def getFirstLine(self):
        return self.pickerName

    def getSecondLine(self):
        to_ret = ''
        limit = self.getElementCount()
        if limit == 0:
            return ''
        i = 0
        while i < limit:
            to_ret += str(self.getElementValue(i)) + str(self.separator)
            i += 1

        if len(self.separator) == 0:
            return to_ret
        return to_ret[:-len(self.separator)]

    def reset(self):
        pass

    def saveValue(self):
        pass

    def getValue(self):
        pass

    def getElementCount(self):
        pass

    def getElementValue(self, index):
        pass

    def changeElementValuePlus(self, index):
        pass

    def changeElementValueMinus(self, index):
        pass


class IntegerPickerMenuItem(PickerMenuItem):

    def __init__(self, name, init_meth = None, save_meth = None, changeValue = 1, signed = True, bound = None, parent = None):
        PickerMenuItem.__init__(self, name, parent)
        self.reset()
        self.signed = signed
        self.changeValue = changeValue
        self.init_meth = init_meth
        self.save_meth = save_meth
        self.bound = bound

    def reset(self):
        self.value = 0
        self.initialized = False

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.value)

    def getValue(self):
        return self.value

    def getElementCount(self):
        return 1

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                self.value = self.init_meth()
            self.initialized = True
        return self.value

    def changeElementValuePlus(self, index):
        self.value += self.changeValue

    def changeElementValueMinus(self, index):
        self.value -= self.changeValue


class FloatPickerMenuItem(PickerMenuItem):
    pass


class TimePickerMenuItem(PickerMenuItem):

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        PickerMenuItem.__init__(self, name, parent, ':')
        self.reset()
        self.max = [24, 60]
        self.init_meth = init_meth
        self.save_meth = save_meth

    def reset(self):
        self.value = [0, 0]
        self.initialized = False

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.value[0], self.value[1])

    def getValue(self):
        return (self.value[0], self.value[1])

    def getElementCount(self):
        return 2

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                self.value[0], self.value[1] = self.init_meth()
            self.initialized = True
        return self.value[index]

    def changeElementValuePlus(self, index):
        self.value[index] = (self.value[index] + 1) % self.max[index]

    def changeElementValueMinus(self, index):
        if self.value[index] == 0:
            self.value[index] = self.max[index]
        self.value[index] -= 1


class DatePickerMenuItem(PickerMenuItem):

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        PickerMenuItem.__init__(self, name, parent, '/')
        self.reset()
        self.max = [None, 12, None]
        self.init_meth = init_meth
        self.save_meth = save_meth

    def reset(self):
        self.value = [1, 1, 2013]
        self.initialized = False

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.value[0], self.value[1], self.value[2])

    def getValue(self):
        return (self.value[0], self.value[1], self.value[2])

    def getElementCount(self):
        return 3

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                self.value[0], self.value[1], self.value[2] = self.init_meth()
            self.initialized = True
        return self.value[index]

    def changeElementValuePlus(self, index):
        if index == 0:
            self.value[0] += 1
            try:
                datetime.date(self.value[2], self.value[1], self.value[0])
            except ValueError:
                self.value[0] = 1
                self.value[1] += 1
                try:
                    datetime.date(self.value[2], self.value[1], self.value[0])
                except ValueError:
                    self.value[1] = 1
                    self.value[2] += 1

        elif index == 1:
            self.value[1] += 1
            try:
                datetime.date(self.value[2], self.value[1], self.value[0])
            except ValueError:
                self.value[0] = 1
                self.value[1] += 1
                try:
                    datetime.date(self.value[2], self.value[1], self.value[0])
                except ValueError:
                    self.value[1] = 1
                    self.value[2] += 1

        elif index == 2:
            self.value[2] += 1

    def changeElementValueMinus(self, index):
        if index == 0:
            pass
        elif index == 1:
            pass
        elif index == 2:
            pass


class StringPickerMenuItem(PickerMenuItem):
    CHARSET = ' abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        PickerMenuItem.__init__(self, name, parent, '')
        self.reset()
        self.init_meth = init_meth
        self.save_meth = save_meth

    def reset(self):
        self.indexes = [0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0]
        self.initialized = False

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.getValue())

    def getValue(self):
        s = ''
        for i in range(0, 16):
            s += self.CHARSET[self.indexes[i]]

        return s.rstrip()

    def getElementCount(self):
        return 16

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                init_str = self.init_meth()
                for i in range(0, 16):
                    if i == len(init_str):
                        break
                    for j in range(0, len(self.CHARSET)):
                        if self.CHARSET[j] == init_str[i]:
                            self.indexes[i] = j

            self.initialized = True
        return self.CHARSET[self.indexes[index]]

    def changeElementValuePlus(self, index):
        self.indexes[index] = (self.indexes[index] + 1) % len(StringPickerMenuItem.CHARSET)

    def changeElementValueMinus(self, index):
        if self.indexes[index] == 0:
            self.indexes[index] = len(StringPickerMenuItem.CHARSET)
        self.indexes[index] -= 1


class ListPickerMenuItem(PickerMenuItem):

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        PickerMenuItem.__init__(self, name, parent, '')
        self.reset()
        self.init_meth = init_meth
        self.save_meth = save_meth
        self.indexList = 0

    def reset(self):
        self.initialized = False
        self.valueList = []

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.valueList[self.indexList])

    def getValue(self):
        return self.valueList[self.indexList]

    def getElementCount(self):
        return 1

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                self.valueList = self.init_meth()
            self.initialized = True
        return self.valueList[self.indexList]

    def changeElementValuePlus(self, index):
        self.indexList = (self.indexList + 1) % len(self.valueList)

    def changeElementValueMinus(self, index):
        if self.indexList == 0:
            self.indexList = len(self.valueList)
        self.indexList -= 1

    def left(self):
        self.changeElementValuePlus(0)
        return self

    def right(self):
        self.changeElementValueMinus(0)
        return self


class IPV4PickerMenuItem(PickerMenuItem):

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        PickerMenuItem.__init__(self, name, parent, '.')
        self.reset()
        self.max = 256
        self.init_meth = init_meth
        self.save_meth = save_meth

    def reset(self):
        self.value = [0,
         0,
         0,
         0]
        self.initialized = False

    def saveValue(self):
        if self.save_meth != None:
            self.save_meth(self.value[0], self.value[1], self.value[2], self.value[3])

    def getValue(self):
        return (self.value[0],
         self.value[1],
         self.value[2],
         self.value[3])

    def getElementCount(self):
        return 4

    def getElementValue(self, index):
        if not self.initialized:
            if self.init_meth != None:
                self.value[0], self.value[1], self.value[2], self.value[3] = self.init_meth()
            self.initialized = True
        return self.value[index]

    def changeElementValuePlus(self, index):
        self.value[index] = (self.value[index] + 1) % self.max

    def changeElementValueMinus(self, index):
        if self.value[index] == 0:
            self.value[index] = self.max
        self.value[index] -= 1


class IPV6PickerMenuItem(StringPickerMenuItem):
    CHARSET = ' 0123456789ABCDEF:'

    def __init__(self, name, init_meth = None, save_meth = None, parent = None):
        StringPickerMenuItem.__init__(self, name, init_meth, save_meth, parent)
        self.indexes = [17,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0]

    def reset(self):
        StringPickerMenuItem.reset(self)
        self.indexes = [17,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0,
         0]

    def changeElementValuePlus(self, index):
        pass

    def changeElementValueMinus(self, index):
        pass
