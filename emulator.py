#Embedded file name: /Volumes/Home/development/goprodumper/emulator.py
import threading
import curses

class emulator(threading.Thread):
    LEFT = 0
    UP = 1
    DOWN = 2
    RIGHT = 3
    SELECT = 4
    ON = 5
    OFF = 6

    def __init__(self):
        threading.Thread.__init__(self)
        self.alive = threading.Event()
        self.alive.set()
        self.lastKey = None
        self.lastValueLock = threading.RLock()
        self.screen = curses.initscr()
        curses.cbreak()
        self.screen.keypad(1)
        self.screen.refresh()
        self.backLight = threading.Event()
        self.start()

    def run(self):
        while self.alive.is_set():
            key = self.screen.getch()
            if key == curses.KEY_UP:
                with self.lastValueLock:
                    self.lastValueLock = emulator.UP
            elif key == curses.KEY_DOWN:
                with self.lastValueLock:
                    self.lastValueLock = emulator.DOWN
            elif key == curses.KEY_LEFT:
                with self.lastValueLock:
                    self.lastValueLock = emulator.LEFT
            elif key == curses.KEY_RIGHT:
                with self.lastValueLock:
                    self.lastValueLock = emulator.RIGHT
            elif key == curses.KEY_ENTER:
                with self.lastValueLock:
                    self.lastValueLock = emulator.SELECT
            else:
                with self.lastValueLock:
                    self.lastKey = None

    def buttonPressed(self, button):
        ret_value = False
        with self.lastValueLock:
            if self.lastKey == button:
                self.lastKey = None
                ret_value = True
        return ret_value

    def clear(self):
        self.screen.addstr(0, 0, '                ')
        self.screen.addstr(1, 0, '                ')

    def message(self, message):
        self.clear()
        lines = message.split('\n')
        self.screen.addstr(0, 0, lines[0])
        self.screen.addstr(1, 0, lines[1])

    def stop(self):
        self.alive.clear()
        curses.endwin()

    def backlight(self, value):
        if value == emulator.ON:
            self.backLight.set()
        elif value == emulator.OFF:
            self.backLight.clear()
