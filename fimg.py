import os
import cv2
import numpy
from PIL import Image

from fshape import fShape


class fImg:
    def read(self, img_path, is_gray=False, is_cv2=True):
        if os.path.exists(img_path):
            if is_cv2:
                img = cv2.imdecode(numpy.fromfile(img_path, dtype=numpy.uint8),
                                   cv2.IMREAD_GRAYSCALE if is_gray else cv2.IMREAD_COLOR)
            else:
                img = Image.open(img_path)
        else:
            img = None
        return img

    def readin(self, img_path, img, is_check_folder=True, is_cv2=True):
        if is_check_folder: os.makedirs(os.path.dirname(img_path), exist_ok=True)
        if is_cv2:
            cv2.imencode(os.path.splitext(img_path)[1], img)[1].tofile(img_path)
        else:
            img.save(img_path)

    def resize_img(self, img, size, is_cv2=True):
        if img:
            if is_cv2:
                img = cv2.resize(img, size)
            else:
                pass  # 待补充PIL.Image resize
        return img

    # OpenCV与PIL.Image格式互换
    def convert(self, img):
        if type(img) == numpy.ndarray:
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            img = cv2.cvtColor(numpy.asarray(img), cv2.COLOR_RGB2BGR)
        return img

    # 泊松融合
    def poisson_blending(self, img, background, img_points=None, position=None, blending_type=cv2.MIXED_CLONE):
        if img_points is None:
            img_h, img_w = img.shape[:2]
            img_points = fShape().convert_rectangle((0, 0, img_w, img_h))
        if position is None:
            background_h, background_w = background.shape[:2]
            position = (background_w // 2, background_h // 2)
        img_mask = numpy.zeros(img.shape, img.dtype)
        cv2.fillPoly(img_mask, [numpy.array(img_points, numpy.int32)], (255, 255, 255))
        img_blending = cv2.seamlessClone(img, background, img_mask, position, blending_type)
        return img_blending

    # 图片相似度-灰度直方图
    def similarity(self, img1, img2):
        hist1 = cv2.calcHist([img1], [0], None, [256], [0.0, 255.0])
        hist2 = cv2.calcHist([img2], [0], None, [256], [0.0, 255.0])
        degree = 0
        for i in range(len(hist1)):
            if hist1[i] != hist2[i]:
                degree += 1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i])
            else:
                degree += 1
        degree /= len(hist1)
        return degree

    # 图片相似度-三直方图
    def classify_hist_with_split(self, img1, img2, size=None):
        if size is not None:
            img1 = self.resize_img(img1, size)
            img2 = self.resize_img(img2, size)
        sub_img1 = cv2.split(img1)
        sub_img2 = cv2.split(img2)
        sub_data = 0
        for im1, im2 in zip(sub_img1, sub_img2):
            sub_data += self.similarity(im1, im2)
        sub_data /= 3
        return sub_data


if __name__ == '__main__':
    pass
