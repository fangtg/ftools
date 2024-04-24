import math


class fMath:
    # 两点距离
    def distance(self, p1, p2):
        (x1, y1), (x2, y2) = p1, p2
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    # 三点形成的夹角
    def angle(self, p1, p2, p3):
        side_1 = self.distance(p2, p3)
        side_2 = self.distance(p1, p3)
        side_3 = self.distance(p1, p2)
        angle_1 = math.degrees(math.acos((side_1 ** 2 - side_2 ** 2 - side_3 ** 2) / (-2 * side_2 * side_3)))
        angle_2 = math.degrees(math.acos((side_2 ** 2 - side_1 ** 2 - side_3 ** 2) / (-2 * side_1 * side_3)))
        angle_3 = math.degrees(math.acos((side_3 ** 2 - side_1 ** 2 - side_2 ** 2) / (-2 * side_1 * side_2)))
        return angle_1, angle_2, angle_3

    def iou(self, box1, box2):
        (x11, y11), (x12, y12) = box1
        (x21, y21), (x22, y22) = box2
        if max(x11, x21) < min(x12, x22) and max(y11, y21) < min(y12, y22):
            s1 = (x12 - x11) * (y12 - y11)
            s2 = (x22 - x21) * (y22 - y21)
            s = (min(x12, x22) - max(x11, x21)) * (min(y12, y22) - max(y11, y21))
            iou = s / min(s1, s2)
        else:
            iou = 0
        return iou


if __name__ == '__main__':
    pass
