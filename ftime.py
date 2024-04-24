import datetime


class fTime:
    def __init__(self):
        self.now = datetime.datetime.now()

    def year(self, string=False):
        return str(self.now.year) if string else self.now.year

    def month(self, string=False):
        return f'{self.now.month:0>2}' if string else self.now.month

    def day(self, string=False):
        return f'{self.now.day:0>2}' if string else self.now.day

    def hour(self, string=False):
        return f'{self.now.hour:0>2}' if string else self.now.hour

    def minute(self, string=False):
        return f'{self.now.minute:0>2}' if string else self.now.minute

    def second(self, string=False):
        return f'{self.now.second:0>2}' if string else self.now.second

    def microsecond(self, string=False):
        return f'{self.now.microsecond:0>6}' if string else self.now.microsecond

    def date(self):
        return f'{self.year()}{self.month(True)}{self.day(True)}'

    def time(self):
        return f'{self.hour(True)}{self.minute(True)}{self.second(True)}'

    def format(self):
        return f'{self.date()}-{self.time()}-{self.microsecond(True)}'


if __name__ == '__main__':
    pass
