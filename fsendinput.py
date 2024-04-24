import ctypes
import time
from typing import Union

PUL = ctypes.POINTER(ctypes.c_ulong)
sleep_time = 0.02


KEYBOARD_MAPPING = {
    'escape': 0x01,
    'esc': 0x01,
    'f1': 0x3B,
    'f2': 0x3C,
    'f3': 0x3D,
    'f4': 0x3E,
    'f5': 0x3F,
    'f6': 0x40,
    'f7': 0x41,
    'f8': 0x42,
    'f9': 0x43,
    'f10': 0x44,
    'f11': 0x57,
    'f12': 0x58,
    'printscreen': 0xB7,
    'prntscrn': 0xB7,
    'prtsc': 0xB7,
    'prtscr': 0xB7,
    'scrolllock': 0x46,
    'pause': 0xC5,
    '`': 0x29,
    '1': 0x02,
    '2': 0x03,
    '3': 0x04,
    '4': 0x05,
    '5': 0x06,
    '6': 0x07,
    '7': 0x08,
    '8': 0x09,
    '9': 0x0A,
    '0': 0x0B,
    '-': 0x0C,
    '=': 0x0D,
    'backspace': 0x0E,
    'insert': 0xD2 + 1024,
    'home': 0xC7 + 1024,
    'pageup': 0xC9 + 1024,
    'pagedown': 0xD1 + 1024,
    # numpad
    'numlock': 0x45,
    'divide': 0xB5 + 1024,
    'multiply': 0x37,
    'subtract': 0x4A,
    'add': 0x4E,
    'decimal': 0x53,
    'numpadenter': 0x9C + 1024,
    'numpad1': 0x4F,
    'numpad2': 0x50,
    'numpad3': 0x51,
    'numpad4': 0x4B,
    'numpad5': 0x4C,
    'numpad6': 0x4D,
    'numpad7': 0x47,
    'numpad8': 0x48,
    'numpad9': 0x49,
    'numpad0': 0x52,
    # end numpad
    'tab': 0x0F,
    'q': 0x10,
    'w': 0x11,
    'e': 0x12,
    'r': 0x13,
    't': 0x14,
    'y': 0x15,
    'u': 0x16,
    'i': 0x17,
    'o': 0x18,
    'p': 0x19,
    '[': 0x1A,
    ']': 0x1B,
    '\\': 0x2B,
    'del': 0xD3 + 1024,
    'delete': 0xD3 + 1024,
    'end': 0xCF + 1024,
    'capslock': 0x3A,
    'a': 0x1E,
    's': 0x1F,
    'd': 0x20,
    'f': 0x21,
    'g': 0x22,
    'h': 0x23,
    'j': 0x24,
    'k': 0x25,
    'l': 0x26,
    ';': 0x27,
    "'": 0x28,
    'enter': 0x1C,
    'return': 0x1C,
    'shift': 0x2A,
    'shiftleft': 0x2A,
    'z': 0x2C,
    'x': 0x2D,
    'c': 0x2E,
    'v': 0x2F,
    'b': 0x30,
    'n': 0x31,
    'm': 0x32,
    ',': 0x33,
    '.': 0x34,
    '/': 0x35,
    'shiftright': 0x36,
    'ctrl': 0x1D,
    'ctrlleft': 0x1D,
    'win': 0xDB + 1024,
    'winleft': 0xDB + 1024,
    'alt': 0x38,
    'altleft': 0x38,
    ' ': 0x39,
    'space': 0x39,
    'altright': 0xB8 + 1024,
    'winright': 0xDC + 1024,
    'apps': 0xDD + 1024,
    'ctrlright': 0x9D + 1024,
    # arrow key scancodes can be different depending on the hardware,
    # so I think the best solution is to look it up based on the virtual key
    # https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-mapvirtualkeya?redirectedfrom=MSDN
}


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class InputI(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", InputI)]


# 按下按键
def key_down(scan_code: Union[int, str]):
    if type(scan_code) == str:
        scan_code = KEYBOARD_MAPPING[scan_code]
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.ki = KeyBdInput(0, scan_code, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    time.sleep(sleep_time)


# 松开按键
def key_up(scan_code: Union[int, str]):
    if type(scan_code) == str:
        scan_code = KEYBOARD_MAPPING[scan_code]
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.ki = KeyBdInput(0, scan_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    time.sleep(sleep_time)


# 敲击一次按键的完整动作
def press(scan_code: Union[int, str]):
    if type(scan_code) == str:
        scan_code = KEYBOARD_MAPPING[scan_code]
    key_down(scan_code)
    key_up(scan_code)


# 相对位移
def move_rel(dx: int, dy: int):
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(dx, dy, 0, 0x0001, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


# 绝对位移
def move_to(x: int, y: int):
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(x, y, 0, 0x0001 | 0x8000, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


# 按下鼠标
def mouse_down(button: str = 'primary'):
    if button == 'primary' or button == 'left':
        button = 0x0002
    elif button == 'middle':
        button = 0x0008
    elif button == 'secondary' or button == 'right':
        button = 0x0020

    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(0, 0, 0, button, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    time.sleep(sleep_time)


# 松开鼠标
def mouse_up(button: str = 'primary'):
    if button == 'primary' or button == 'left':
        button = 0x0004
    elif button == 'middle':
        button = 0x0010
    elif button == 'secondary' or button == 'right':
        button = 0x0040

    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(0, 0, 0, button, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    time.sleep(sleep_time)


# 敲击一次鼠标的完整动作
def click(button: str = 'primary', x: int = -1, y: int = -1, relative: bool = False):
    if relative is False and x != -1 and y != -1:
        move_to(x, y)
    elif relative is True:
        move_rel(x, y)
    mouse_down(button)
    mouse_up(button)


# 鼠标滚轮控制
def mouse_wheel(wheel: int = -1):
    extra = ctypes.c_ulong(0)
    ii_ = InputI()
    ii_.mi = MouseInput(0, 0, wheel, 0x0800, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    time.sleep(sleep_time)


if __name__ == '__main__':
    pass
