"""
time: 20231101
"""
import cv2
import numpy
import os
from copy import deepcopy
from shapely.geometry import Polygon

from ftime import fTime
from ffile import fFile, fTxt
from fmark import fXmlMark, fJsonMark
from fmath import fMath
from fimg import fImg


# yolo转voc
def yolo2voc(img_size, box):
    img_h, img_w = img_size
    x, y = box[0] * img_w, box[1] * img_h
    box_w, box_h = box[2] * img_w, box[3] * img_h
    xmin, xmax = x - box_w / 2, x + box_w / 2
    ymin, ymax = y - box_h / 2, y + box_h / 2
    return xmin, ymin, xmax, ymax


# voc转yolo
def voc2yolo(img_size, box):
    x = ((box[0] + box[2]) / 2) / img_size[1]
    y = ((box[1] + box[3]) / 2) / img_size[0]
    w = abs(box[2] - box[0]) / img_size[1]
    h = abs(box[3] - box[1]) / img_size[0]
    return x, y, w, h


def mark2yolo(config, cnt, index, root, img_name, img_suffix):
    """
    config依赖:
    log_path,scan_path
    output_path,mark_suffix,mark_labels,is_draw,draw_color,draw_thickness
    输出目录,标注后缀名,标注标签,是否绘框,绘框颜色,绘框宽度
    """
    img_path = f'{root}/{img_name}{img_suffix}'
    mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
    if os.path.exists(mark_path) is False:
        mark_data = []
    else:
        _, img_size, mark_data = config["mark_funcs"][config["mark_suffix"]]["read"](mark_path)
    if len(mark_data) > 0:
        img = fImg().read(img_path)
        img_size = img.shape[:2]
    yolo_data = ''

    contours = []
    for mark in mark_data:
        if mark[0] not in config["mark_labels"]:
            fTxt().add(config["log_path"], f'[warn]未包含的标签: {index}, {mark_path}, {mark[0]}\n')
            cnt[2] += 1
            continue
        if mark[2] == 'polygon':
            pass
        elif mark[2] in ['rectangle', 0, 1]:
            (x1, y1), (x2, y2) = mark[1]
            yolo = voc2yolo(img_size, (x1, y1, x2, y2))
            index = config["mark_labels"].index(mark[0])
            yolo_data += f'{index} {" ".join([str(_) for _ in yolo])}\n'
            contours.append(fMath().structure_rec(mark[1]))
        else:
            fTxt().add(config["log_path"], f'[error]未受支持的标注类型: {index}, {mark_path}, {mark[2]}\n')
            cnt[3] += 1
            continue

    output_dir = root
    if config["scan_path"] != config["output_path"]:
        output_dir = root.replace(config["scan_path"], config["output_path"])
        if config["is_draw"] is True and len(contours) > 0:  # 绘框且可以绘框
            for _ in contours:
                cv2.drawContours(img, [numpy.array(_, dtype=numpy.int32)], -1,
                                 config["draw_color"], config["draw_thickness"])
            fImg().readin(f'{output_dir}/{img_name}{img_suffix}', img)
        else:
            fFile().copy(img_path, output_dir)
    if len(contours) > 0:
        fTxt().readin(f'{output_dir}/{img_name}.txt', yolo_data)
    cnt[1] -= 1


def yolo2mark(config, cnt, index, root, img_name, img_suffix):
    """
    config依赖:
    log_path,scan_path
    output_path,mark_suffix,mark_labels,is_draw,draw_color,draw_thickness
    输出目录,标注后缀名,标注标签,是否绘框,绘框颜色,绘框宽度
    """
    img_path = f'{root}/{img_name}{img_suffix}'
    yolo_path = f'{root}/{img_name}.txt'
    if os.path.exists(yolo_path) is False:
        yolo_data = []
    else:
        yolo_data = fTxt().read(yolo_path)
        yolo_data = yolo_data.strip().split('\n')
        yolo_data = [_.split(' ') for _ in yolo_data]
    if len(yolo_data) > 0:
        img = fImg().read(img_path)
        img_size = img.shape[:2]
        mark_data = []

    contours = []
    for yolo in yolo_data:
        if 5 <= len(yolo) <= 6:
            label_index = int(yolo[0])
            xmin, ymin, xmax, ymax = yolo2voc(img_size, [float(_) for _ in yolo[1:5]])
            conf = float(yolo[5]) if len(yolo) == 6 else 0
            conf_info = f' {conf}' if conf > 0 else ''
            if label_index < len(config["mark_labels"]):
                label = config["mark_labels"][label_index]
            else:
                label = f'label{label_index}'
                fTxt().add(config["log_path"], f'[warn]未包含的标签: {index}, {yolo_path}\n')
                cnt[2] += 1
            mark_data.append([label, ([(xmin, ymin), (xmax, ymax)]),
                              0 if config["mark_suffix"] == '.xml' else 'rectangle'])
            contours.append([fMath().structure_rec([(xmin, ymin), (xmax, ymax)]), f'{label}{conf_info}'])
        else:
            fTxt().add(config["log_path"], f'[error]未受支持的yolo类型: {index}, {yolo_path}\n')
            cnt[3] += 1

    output_dir = root
    if config["scan_path"] != config["output_path"]:
        output_dir = root.replace(config["scan_path"], config["output_path"])
        if config["is_draw"] is True and len(contours) > 0:  # 绘框且可以绘框
            for _ in contours:
                cv2.drawContours(img, [numpy.array(_[0], dtype=numpy.int32)], -1,
                                 config["draw_color"], config["draw_thickness"])
            fImg().readin(f'{output_dir}/{img_name}{img_suffix}', img)
        else:
            fFile().copy(img_path, output_dir)
    if len(contours) > 0:
        config["mark_funcs"][config["mark_suffix"]]["readin"](
            f'{output_dir}/{img_name}{img_suffix}', img_size, mark_data)
    cnt[1] -= 1


def mask_img(config, cnt, index, root, img_name, img_suffix):
    """
    config依赖:
    log_path,scan_path
    mark_suffix,mask_labels,draw_color
    标注后缀名,mask标签,mask颜色
    """
    img_path = f'{root}/{img_name}{img_suffix}'
    mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
    if os.path.exists(mark_path) is False:
        mark_data = []
    else:
        _, img_size, mark_data = config["mark_funcs"][config["mark_suffix"]]["read"](mark_path)

    contours = []
    for i in range(len(mark_data) - 1, -1, -1):
        if mark_data[i][0] in config["mask_labels"]:
            if mark_data[i][2] == 'polygon':
                contours.append(mark_data[i][1])
            elif mark_data[i][2] in ['rectangle', 0, 1]:
                (x1, y1), (x2, y2) = mark_data[i][1]
                # 标注软件无法标注到0
                x1 = x1 if x1 > 1 else 0
                y1 = y1 if y1 > 1 else 0
                contours.append(fMath().structure_rec([(x1, y1), (x2, y2)]))
            else:
                fTxt().add(config["log_path"], f'[warn]未受支持的标签类型: {index}, {mark_path}, {mark_data[i][2]}\n')
                cnt[2] += 1
                continue
            del mark_data[i]

    if len(contours) > 0:
        img = fImg().read(img_path)
        img_size = img.shape[:2]
        for _ in contours:
            cv2.drawContours(img, [numpy.array(_, dtype=numpy.int32)], -1, config["draw_color"], -1)
        fImg().readin(img_path, img)
        config["mark_funcs"][config["mark_suffix"]]["readin"](img_path, img_size, mark_data)
    cnt[1] -= 1


def remove_specific_overlap(config, cnt, index, root, img_name, img_suffix):
    """
    config依赖:
    log_path,scan_path
    mark_suffix,mark_labels,iou_thres
    标注后缀名,标注标签,iou阈值
    """
    img_path = f'{root}/{img_name}{img_suffix}'
    mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
    if os.path.exists(mark_path) is False:
        mark_data = []
    else:
        _, img_size, mark_data = config["mark_funcs"][config["mark_suffix"]]["read"](mark_path)
    specific_data = list(filter(lambda _: _[0] in config["mark_labels"], mark_data))
    if len(specific_data) > 0:
        specific_region = Polygon()
        for specific in specific_data:
            if specific[2] == 'polygon':
                specific_region = specific_region.union(Polygon(specific[1]))
            elif specific[2] in ['rectangle', 0, 1]:
                specific_region = specific_region.union(Polygon(fMath().structure_rec(specific[1])))
            else:
                fTxt().add(config["log_path"], f'[warn]未受支持的标签类型: {index}, {mark_path}, {specific[2]}\n')
                cnt[2] += 1
                continue
        del_cnt = 0
        specific_area = specific_region.area
        for i in range(len(mark_data) - 1, -1, -1):
            if mark_data[i][0] not in config["mark_labels"]:
                if mark_data[i][2] == 'polygon':
                    mark_region = Polygon(mark_data[i][1])
                elif mark_data[i][2] in ['rectangle', 0, 1]:
                    mark_region = Polygon(fMath().structure_rec(mark_data[i][1]))
                else:
                    fTxt().add(config["log_path"], f'[warn]未受支持的标签类型: {index}, {mark_path}, {mark_data[i][2]}\n')
                    cnt[2] += 1
                    continue
                if mark_region.intersection(specific_region).area / min(mark_region.area,
                                                                        specific_area) > config["iou_thres"]:
                    del mark_data[i]
                    del_cnt += 1
        if del_cnt > 0:
            config["mark_funcs"][config["mark_suffix"]]["readin"](img_path, img_size, mark_data)
    cnt[1] -= 1


def crop_img(config, cnt, index, root, img_name, img_suffix):
    """
    config依赖:
    log_path,scan_path
    output_path,crop_h,crop_w,back
    输出目录,裁剪高度,裁剪宽度,回退长度
    """
    img_path = f'{root}/{img_name}{img_suffix}'
    img = fImg().read(img_path)
    h, w = img.shape[:2]
    crop_h, crop_w, back = config["crop_h"], config["crop_w"], config["back"]
    if crop_h > h or crop_w > w:
        fTxt().add(config["log_path"], f'[error]裁剪设置超过原图: {index}, {img_path}\n')
        cnt[3] += 1
    else:
        xmin, ymin, locx, locy = 0, 0, [0], [0]
        while True:
            xmin = xmin + crop_w - back
            if xmin + crop_w > w:
                xmin = w - crop_w
                if xmin <= locx[-1]:
                    break
            locx.append(xmin)
        while True:
            ymin = ymin + crop_h - back
            if ymin + crop_h > h:
                ymin = h - crop_h
                if ymin <= locy[-1]:
                    break
            locy.append(ymin)
        img_num = len(locx) * len(locy)
        img_index = 1
        for y in locy:
            for x in locx:
                img_crop = img[y:y + crop_h, x:x + crop_w]
                fImg().readin(
                    f'{config["output_path"]}/{img_name}_{str(img_index).rjust(len(str(img_num)), "0")}{img_suffix}',
                    img_crop)
                img_index += 1
    cnt[1] -= 1


def rename_file(config, cnt, index, root, file_name, file_suffix):
    """
    config依赖:
    log_path,scan_path
    output_path,mark_suffix,prefix,start_index,file_num
    输出目录,标注后缀名,重命名前缀,起始序号,文件数
    """
    output_dir = root.replace(config["scan_path"], config["output_path"])
    file_path = f'{root}/{file_name}{file_suffix}'
    new_file_name = f'{config["prefix"]}{str(index + config["start_index"] - 1).rjust(config["file_num"], "0")}'
    new_file_path = f'{output_dir}/{new_file_name}{file_suffix}'
    fFile().move(file_path, new_file_path)
    if 'mark_suffix' in config:
        mark_path = f'{root}/{file_name}{config["mark_suffix"]}'
        if os.path.exists(mark_path) is True:
            if config["mark_suffix"] == '.xml':
                new_mark_path = f'{output_dir}{new_file_name}{config["mark_suffix"]}'
                fFile().move(mark_path, new_mark_path)
            elif config["mark_suffix"] == '.json':
                _, img_size, mark_data = fJsonMark().read(mark_path)
                fJsonMark().readin(new_file_path, img_size, mark_data)
    cnt[1] -= 1


def divide_files(config, file_list):
    """
    config依赖:
    scan_path
    divide,layering
    划分比例,是否分层
    """
    if config["layering"] is False:  # 比例划分
        divide_entirety(config, file_list, deepcopy(config["divide"]))
    else:  # 分层划分转为分层比例划分
        layering_length = sum(config["divide"])  # 分层长度
        layering_divide = [_/layering_length for _ in config["divide"]]  # 分层划分比例
        layering_num = len(file_list) // layering_length  # 完整分层数
        layering_last = len(file_list) % layering_length  # 不完整层图片数
        for i in range(layering_num):
            layering_list = file_list[i*layering_length:(i+1)*layering_length]
            divide_entirety(config, layering_list, deepcopy(layering_divide))
        if layering_last > 0:
            layering_list = file_list[-layering_last:]
            divide_entirety(config, layering_list, deepcopy(layering_divide))


def divide_entirety(config, file_list, divide):
    """
    config依赖:
    log_path,scan_path
    output_path,mark_suffix
    输出目录,标注后缀名
    """
    if sum(divide) > 1:
        fTxt().add(config["log_path"], f'[error]划分比例错误: {divide}\n')
        return
    numpy.random.shuffle(file_list)
    for i in range(len(divide)):
        divide[i] = round(divide[i] * len(file_list))  # 每比例文件数
        for file_path in file_list[sum(divide[:i]):sum(divide[:i + 1])]:
            output_dir = os.path.dirname(file_path).replace(config['scan_path'], f'{config["output_path"]}/divide{i}')
            fFile().copy(file_path, output_dir)
            if 'mark_suffix' in config:
                mark_path = f'{os.path.splitext(file_path)[0]}{config["mark_suffix"]}'
                if os.path.exists(mark_path):
                    fFile().copy(mark_path, output_dir)


# 模型评估
def evaluateModel(mark_folder_path: str, detect_folder_path: str, output_folder_path: str, mark_suffix: str):
    cnt_process, cnt_error = 0, 0

    for root, dirs, files in os.walk(mark_folder_path):
        for file in files:
            file_name, file_suffix = os.path.splitext(file)
            file_suffix = file_suffix.lower()
            if file_suffix == mark_suffix:
                cnt_process += 1
                fTime().printInfo(f'process img: {cnt_process}')
                print(file_name)

                file_path = f'{root}/{file}'
                img_path, img_size, mark_data = fXmlMark().read(file_path)
                detect_path = f'{root.replace(mark_folder_path, detect_folder_path)}/{file}'
                if os.path.exists(detect_path) is False:
                    for i, _ in enumerate(mark_data):
                        mark_data[i][0] += '_undetected'
                    fXmlMark().readin(f'{root.replace(mark_folder_path, output_folder_path)}/{file_name}.jpg', img_size,
                                      mark_data)
                    continue
                _, _, detect_data = fXmlMark().read(detect_path)
                sorted(mark_data, key=lambda x: x[1][0])
                sorted(detect_data, key=lambda x: x[1][0])

                for i in range(len(mark_data) - 1, -1, -1):
                    mark = mark_data[i]
                    (xa1, ya1), (xa2, ya2) = mark[1]
                    sa = (xa2 - xa1) * (ya2 - ya1)
                    mark_ismap = False
                    for j in range(len(detect_data) - 1, -1, -1):
                        detect = detect_data[j]
                        (xb1, yb1), (xb2, yb2) = detect[1]
                        # if xb1 > xa2 or xb2 < xa1:
                        #     break
                        sb = (xb2 - xb1) * (yb2 - yb1)
                        x1, y1, x2, y2 = max(xa1, xb1), max(ya1, yb1), min(xa2, xb2), min(ya2, yb2)
                        w, h = max(0, x2 - x1), max(0, y2 - y1)
                        iou = w * h / max(sa, sb)
                        if iou > 0.6 or (sa > 0 and w * h / min(sa, sb)) > 0.9:
                            # 重检
                            if mark_ismap is True:
                                if mark[0] != detect[0]:
                                    detect_data[j][0] = f'{mark[0]}_{detect[0]}_wrong'
                                detect_data[j][0] += '_repeat'
                                mark_data.append(detect_data[j])
                            else:
                                # 错检
                                if mark[0] != detect[0]:
                                    detect_data[j][0] = f'{mark[0]}_{detect[0]}_wrong'
                                    mark_data.append(detect_data[j])
                                else:
                                    # 偏移
                                    if iou < 0.6:
                                        detect_data[j][0] += '_move'
                                        mark_data.append(detect_data[j])
                            del detect_data[j]
                            mark_ismap = True
                    # 漏检
                    if mark_ismap is False:
                        mark_data[i][0] += '_undetected'
                # 过检
                for j in range(len(detect_data)):
                    detect_data[j][0] += '_overdetected'
                mark_data.extend(detect_data)

                output_file_folder_path = root.replace(mark_folder_path, output_folder_path)
                os.makedirs(output_file_folder_path, exist_ok=True)
                # fXmlMark().readin(img_path, img_size, mark_data, f'{output_file_folder_path}/{file}')
                # fXmlMark().readin(img_path, img_size, mark_data)
                fXmlMark().readin(f'{root.replace(mark_folder_path, output_folder_path)}/{file_name}.jpg', img_size,
                                  mark_data)


# 输出模型评估中有问题的部分
def outputEvaluatePart(evaluate_folder_path: str,
                       output_folder_path: str,
                       mark_labels: list, mark_suffix: str, img_suffixs: list):
    cnt_process, cnt_error = 0, 0

    for root, dirs, files in os.walk(evaluate_folder_path):
        for file in files:
            file_name, file_suffix = os.path.splitext(file)
            file_suffix = file_suffix.lower()
            if file_suffix == mark_suffix:
                cnt_process += 1
                fTime().printInfo(f'process img: {cnt_process}')

                # 读取eva并匹配图片
                file_path = f'{root}/{file}'
                _, _, eva_data = fXmlMark().read(file_path)
                sorted(eva_data, key=lambda x: x[1][0])
                for suffix in img_suffixs:
                    img_full = f'{file_name}{suffix}'
                    img_path = f'{root}/{img_full}'
                    if os.path.exists(img_path) is True:
                        break
                else:
                    cnt_error += 1
                    fTime().printInfo(f'[error]can not find img: {file}')
                    continue

                img = cv2.imdecode(numpy.fromfile(img_path, dtype=numpy.uint8), -1)
                img_size = img.shape[:2]

                for a in eva_data:
                    if a[0] in mark_labels:
                        continue
                    xa1, ya1, xa2, ya2 = a[1]
                    expand_len = 100
                    x1, y1, x2, y2 = xa1 - expand_len, ya1 - expand_len, xa2 + expand_len, ya2 + expand_len
                    img = captureOutofRange((x1, y1, x2, y2), img, img_size)
                    contours1 = [[xa1 - x1, ya1 - y1], [xa2 - x1, ya1 - y1], [xa2 - x1, ya2 - y1], [xa1 - x1, ya2 - y1]]
                    contours2 = []
                    for b in eva_data:
                        xb1, yb1, xb2, yb2 = b[1]
                        if x1 < xb1 < x2 and x1 < xb2 < x2 and y1 < yb1 < y2 and y1 < yb2 < y2:
                            contours2.append([[xb1 - x1, yb1 - y1], [xb2 - x1, yb1 - y1], [xb2 - x1, yb2 - y1],
                                              [xb1 - x1, yb2 - y1]])
                    for _ in contours1:
                        _ = numpy.array(_, dtype=numpy.int32)
                        cv2.drawContours(img, [_], -1, (255, 255, 0), 3)
                    for _ in contours2:
                        _ = numpy.array(_, dtype=numpy.int32)
                        cv2.drawContours(img, [_], -1, (0, 255, 0), 3)
                    output_file_folder_path = f'{output_folder_path}/{a[0]}'
                    img_crop_path = f'{output_file_folder_path}/{file_name}_{a[0]}_{a[1][0]}_{a[1][1]}.jpg'
                    cv2.imencode(os.path.splitext(img_crop_path)[1], img)[1].tofile(img_crop_path)


# cv2截取超出边界图片
def captureOutofRange(box, img, img_size=None):
    if img_size is None:
        img_size = img.shape[:2]
    h, w = img_size
    x1, y1, x2, y2 = box
    box_h, box_w = y2 - y1, x2 - x1
    x1, x_move = (0, 0 - x1) if x1 < 0 else (x1, 0)
    y1, y_move = (0, 0 - y1) if y1 < 0 else (y1, 0)
    x2 = w if x2 > w else x2
    y2 = h if y2 > h else y2
    print((x1, y1, x2, y2), (w, h), (box_w, box_h), (x_move, y_move))
    background = numpy.zeros((box_h, box_w, 3), numpy.uint8)
    background[:] = [255, 255, 255]
    background[y_move:y2 - y1 + y_move, x_move:x2 - x1 + x_move] = img[y1:y2, x1:x2]
    return background


# 截取特定code区域图片另存
def captureSpecificRegion(img_folder_path: str, output_folder_path: str, mark_suffix: str, img_suffixs: list,
                          mask_labels: list):
    cnt_process, cnt_error = 0, 0

    for root, dirs, files in os.walk(img_folder_path):
        for file in files:
            file_name, file_suffix = os.path.splitext(file)
            file_suffix = file_suffix.lower()
            if file_suffix in img_suffixs:
                cnt_process += 1
                fTime().printInfo(f'process img: {cnt_process}')

                # 读取图片与标注
                output_file_folder_path = root.replace(img_folder_path, output_folder_path)
                if os.path.exists(output_file_folder_path) is False:
                    os.makedirs(output_file_folder_path, exist_ok=True)
                file_path = f'{root}/{file}'
                mark_path = f'{root}/{file_name}{mark_suffix}'
                if os.path.exists(mark_path) is True:
                    if mark_suffix == '.json':
                        _, _, mark_data = fJsonMark().read(mark_path)
                    elif mark_suffix == '.xml':
                        _, _, mark_data = fXmlMark().read(mark_path)
                else:
                    mark_data = []

                img = cv2.imdecode(numpy.fromfile(file_path, dtype=numpy.uint8), -1)

                for _ in mark_data:
                    if _[0] in mask_labels:
                        x1, y1, x2, y2 = _[1]
                        capture = img[y1 - 1:y2 - 1, x1 - 1:x2 - 1]
                        capture_path = f'{output_file_folder_path}/{file_name}_{x1}-{y1}-{x2}-{y2}{file_suffix}'
                        cv2.imencode(os.path.splitext(capture_path)[1], capture)[1].tofile(capture_path)

                for i in range(len(mark_data) - 1, -1, -1):
                    _ = mark_data[i]
                    if _[0] in mask_labels:
                        if _[2] == 'polygon':
                            contours.append(_[1])
                        elif _[2] in ['rectangle', 0, 1]:
                            if _[2] == 'rectangle':
                                x1, y1 = _[1][0]
                                x2, y2 = _[1][1]


if __name__ == "__main__":
    pass

    # evaluateModel(r'D:\data\DIP\train20231005\val_mark',
    #               r'D:\data\DIP\train20231005\val_detect',
    #               r'D:\data\DIP\train20231005\val',
    #               '.xml')

    # marks2Yolos(r'D:\data\WHTM\13534\train\20231013\data', r'D:\data\WHTM\13534\train\20231013\data', '.xml',
    # ['.jpg', '.png'], ['A01_G', 'A03_G', 'A04_G', 'A05_G', 'A11_G', 'D01_G', 'D03_G', 'D04_G', 'D05_G', 'D11_G',
    # 'G03_G', 'G04_G', 'G05_G', 'G11_G', 'I04_G', 'T02_G', 'T03_G', 'T04_G', 'T05_G', 'T07_G', 'T08_G', 'T11_G',
    # 'T13_G', 'T14_G', 'T16_G', 'T17_G', 'T19_G', 'T21_G', 'T22_G', 'T25_G', 'T27_G', 'difficult'])
