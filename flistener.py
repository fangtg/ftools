from pynput import keyboard, mouse


class fListener:
    def __init__(self):
        self.listener = None

    def stop(self):
        self.listener.stop()

    def suppress(self):
        self.listener.suppress_event()


class fKeyboardListener(fListener):
    def __init__(self, response):
        super().__init__()
        self.listener = keyboard.Listener(win32_event_filter=response)
        self.listener.start()


class fMouseListener(fListener):
    def __init__(self, response):
        super().__init__()
        self.listener = mouse.Listener(win32_event_filter=response)
        self.listener.start()


if __name__ == '__main__':
    pass
