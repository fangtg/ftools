class fShape:
    # 读取矩形框
    def read_rectangle(self, box):
        if len(box) == 4:
            x1, y1, x2, y2 = box
        else:
            (x1, y1), (x2, y2) = box
        return x1, y1, x2, y2

    # 两点矩形框转四点矩形框
    def convert_rectangle(self, box):
        x1, y1, x2, y2 = self.read_rectangle(box)
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


if __name__ == '__main__':
    pass
