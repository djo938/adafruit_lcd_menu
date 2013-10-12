#Embedded file name: /Volumes/Home/development/goprodumper/menu_process.py
import threading
import time
from lcd_menu import LcdEventQueue, Lcd_menu_item, SimpleProcessMenuItem, Lcd_item

class MenuProcess(threading.Thread):

    def __init__(self, screenQueue = None, pausable = True):
        threading.Thread.__init__(self)
        self.screenQueue = screenQueue
        self.informationIndex = 0
        self.informationLock = threading.RLock()
        self.informationEnabled = threading.Event()
        self.alive = threading.Event()
        self.alive.set()
        self.forceStop = False
        self.normalEnd = False
        self.pausable = pausable
        if pausable:
            self.pause = threading.Event()
            self.pause.set()
        self.lastValueLock = threading.RLock()
        self.lastValue = []
        for i in range(0, self.getInformationIndexCount()):
            self.lastValue.append('no value')

    def run(self):
        self.init_process()
        while self.alive.is_set():
            if self.pausable:
                self.pause.wait()
            self.increment_process()

        self.ending_process()
        self._normalEnding()
        self.normalEnd = True

    def join(self, timeout = None):
        self.alive.clear()
        threading.Thread.join(self, timeout)

    def _normalEnding(self):
        self.alive.clear()

    def stop(self):
        self.forceStop = True
        self.alive.clear()

    def isRunning(self):
        return self.alive.isSet()

    def isFinnished(self):
        return self.normalEnd

    def isPauseAllowed(self):
        return self.pausable

    def isPauseEnabled(self):
        if self.pausable:
            return not self.pause.is_set()
        return False

    def ppause(self):
        if self.pausable:
            self.pause.clear()

    def presume(self):
        if self.pausable:
            self.pause.set()

    def enablePublication(self):
        self.informationEnabled.set()

    def getLastValue(self):
        with self.informationLock:
            return str(self.lastValue[self.informationIndex])

    def disablePublication(self):
        self.informationEnabled.clear()

    def setInformationIndex(self, index):
        if index < 0 or index >= self.getInformationIndexCount():
            return
        with self.informationLock:
            self.informationIndex = index

    def publishInformation(self, index, value):
        if index < 0 or index >= self.getInformationIndexCount():
            return
        with self.informationLock:
            if self.screenQueue != None and self.informationEnabled.is_set() and self.informationIndex == index:
                self.screenQueue.invokeLater((LcdEventQueue.REFRESH_FIRST_LINE, str(value), None))
            self.lastValue[index] = value

    def getInformationIndexCount(self):
        pass

    def getInformationTitles(self):
        pass

    def init_process(self):
        pass

    def increment_process(self):
        pass

    def ending_process(self):
        pass


class TestProcess(MenuProcess):

    def __init__(self, screenQueue, pausable):
        MenuProcess.__init__(self, screenQueue, pausable)
        self.limit = 1000.0
        self.percent = 0

    def getInformationIndexCount(self):
        return 3

    def getInformationTitles(self):
        return ('percent', 'load', 'status')

    def init_process(self):
        self.counter = 0
        self.publishInformation(2, 'processing')

    def increment_process(self):
        self.counter += 1
        time.sleep(0.5)
        new_percent = int(self.counter / self.limit * 100)
        if self.percent < new_percent:
            self.percent = new_percent
            self.publishInformation(0, str(self.percent) + '/100')
        self.publishInformation(1, str(self.counter) + '/' + str(int(self.limit)))

    def ending_process(self):
        self.publishInformation(2, 'ended')


class StartStop_process_item(SimpleProcessMenuItem):

    def __init__(self, process_object, parent = None):
        SimpleProcessMenuItem.__init__(self, 'Start', self.fun, True, False, False, parent)
        self.running = False
        self.process_object = process_object

    def fun(self):
        if self.running:
            self.process_object.stop()
            self.name = 'Start'
        else:
            self.process_object.start()
            self.name = 'Stop'
        self.running = not self.running


class PauseResume_process_item(SimpleProcessMenuItem):

    def __init__(self, process_object, parent = None):
        SimpleProcessMenuItem.__init__(self, 'Pause', self.fun, True, False, False, parent)
        self.pause = False
        self.process_object = process_object

    def fun(self):
        if self.pause:
            self.process_object.presume()
            self.name = 'Pause'
        else:
            self.process_object.ppause()
            self.name = 'Resume'
        self.pause = not self.pause


class Content_process_item(Lcd_item):

    def __init__(self, index, name, process_object, parent = None):
        self.parent = parent
        self.index = index
        self.name = name
        self.process_object = process_object

    def getParent(self):
        return self.parent

    def setParent(self, parent):
        self.parent = parent

    def executeOnPush(self):
        return self.getParent()

    def executeOnSelect(self):
        self.process_object.setInformationIndex(self.index)
        self.process_object.enablePublication()
        self.getParent().setContent((self.process_object.getLastValue(),))

    def executeOnDeselect(self):
        self.process_object.disablePublication()
        self.getParent().restoreInitialContent()

    def getName(self):
        return self.name


class Lcd_process_item(Lcd_menu_item):
    """menu qui permet d'executer un process lourd"""

    def __init__(self, Name, process_object, parent = None):
        Lcd_menu_item.__init__(self, Name, True, parent)
        self.process_object = process_object
        self.addChild(StartStop_process_item(process_object))
        if self.process_object.isPauseAllowed():
            self.addChild(PauseResume_process_item(process_object))
        index = 0
        for information in self.process_object.getInformationTitles():
            self.addChild(Content_process_item(index, information, process_object))
            index += 1


if __name__ == '__main__':
    pass
