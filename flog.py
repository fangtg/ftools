"""
time: 20240129
"""
from ffile import fTxt


class fLog:
    def __init__(self, print_switch=True, log_switch=True, log_path=None):
        self.print_switch = print_switch
        if log_path:
            self.log_path = log_path
            self.log_switch = log_switch
        else:
            self.log_switch = False

    def print(self, content, end='\n'):
        if self.print_switch: print(content, end=end)

    def log(self, content, log_path=None, encoding='utf-8'):
        if self.log_switch and log_path: fTxt().add(log_path, content, encoding=encoding)


if __name__ == '__main__':
    pass
