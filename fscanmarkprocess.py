"""
time: 20240130
"""
import os
import pprint
import threading
from ffile import fFile
from fmath import fMath
from fshape import fShape
from fimg import fImg
from fscan import fScan

import cv2
import numpy
from shapely.geometry import Polygon
from copy import deepcopy
from collections import defaultdict
from tqdm import tqdm


class fScanMarkProcess(fScan):
    def yolo2voc(self, box, img_size):
        img_h, img_w = img_size
        x, y = box[0] * img_w, box[1] * img_h
        box_w, box_h = box[2] * img_w, box[3] * img_h
        xmin, xmax = x - box_w / 2, x + box_w / 2
        ymin, ymax = y - box_h / 2, y + box_h / 2
        return xmin, ymin, xmax, ymax

    def voc2yolo(self, box, img_size):
        x1, y1, x2, y2 = fShape().read_rectangle(box)
        x = ((x1 + x2) / 2) / img_size[1]
        y = ((y1 + y2) / 2) / img_size[0]
        w = abs(x2 - x1) / img_size[1]
        h = abs(y2 - y1) / img_size[0]
        return x, y, w, h

    # ----------------------------------------
    # 文件操作

    # 标注转yolo
    def mark2yolo_init(self, config):
        if 'is_draw' not in config: config['is_draw'] = False
        if 'draw_color' not in config: config['draw_color'] = (0, 0, 0)
        if 'draw_thickness' not in config: config['draw_thickness'] = 1
        if 'font_scale' not in config: config['font_scale'] = 1
        if 'is_gap_space' not in config: config['is_gap_space'] = False
        return config, {'scan_path', 'output_path', 'logger',
                        'mark_suffix', 'mark_funcs', 'mark_labels',
                        'is_draw', 'draw_color', 'draw_thickness', 'font_scale', 'is_gap_space'}

    def mark2yolo(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1] if os.path.exists(
            mark_path) else []
        img = fImg().read(img_path) if len(mark_data) > 0 else None
        img_size = img.shape[:2] if img is not None else (0, 0)

        yolo_data, contours = '', []
        for shape in mark_data:
            if shape[0] not in config['mark_labels']:
                config['logger'].log(f'[warn]未包含的标签: {mark_path}, {shape[0]}\n')
                config['cnt'][1] += 1
                continue
            if shape[2] in ['rectangle', 0, 1]:
                x1, y1, x2, y2 = fShape().read_rectangle(shape[1])
                yolo = self.voc2yolo(shape[1], img_size)
                label_index = config['mark_labels'].index(shape[0])
                yolo_data += f'{label_index} {" ".join([str(value) for value in yolo])}\n'
                contours.append([fShape().convert_rectangle(shape[1]), shape[0], (round(x1), round(y1))])
            elif shape[2] in ['polygon']:
                pass
            elif shape[2] in ['point']:
                x, y = shape[1][0]
                x_ = f'{x / img_size[1]:.5f}'
                y_ = f'{y / img_size[0]:.5f}'
                conf = shape[-1] if len(shape) == 4 else -1
                status = 2 if conf == -1 else 1 if conf == 1 else 0
                yolo_data += f'{x_} {y_} {status}\n'
                contours.append([[[x, y]], shape[0], (round(x), round(y))])
            else:
                config['logger'].log(f'[error]未受支持的标注类型: {mark_path}, {shape[2]}\n')
                config['cnt'][2] += 1
                continue

        output_dir = root
        if config['scan_path'] != config['output_path']:  # 只有输出目录与遍历目录不同才可绘框
            output_dir = root.replace(config['scan_path'], config['output_path'])
            if config['is_draw'] and len(contours) > 0:  # 绘框且可以绘框
                for contour in contours:
                    cv2.drawContours(img, [numpy.array(contour[0], dtype=numpy.int32)], -1,
                                     config['draw_color'], config['draw_thickness'])
                    cv2.putText(img, contour[1], contour[2], cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=config['font_scale'], thickness=config['draw_thickness'],
                                color=config['draw_color'])
                fImg().readin(f'{output_dir}/{img_name}{img_suffix}', img)
            else:
                fFile().copy(img_path, output_dir)
        if len(contours) > 0:
            yolo_data = yolo_data.replace('\n', ' ') if config['is_gap_space'] else yolo_data
            fFile().readin(f'{output_dir}/{img_name}.txt', yolo_data)
        config['cnt'][0] -= 1

    # yolo转标注
    def yolo2mark_init(self, config):
        if 'is_draw' not in config: config['is_draw'] = False
        if 'draw_color' not in config: config['draw_color'] = (0, 0, 0)
        if 'draw_thickness' not in config: config['draw_thickness'] = 1
        if 'font_scale' not in config: config['font_scale'] = 1
        return config, {'scan_path', 'output_path', 'logger',
                        'mark_suffix', 'mark_funcs', 'mark_labels', 'mark_type',
                        'is_draw', 'draw_color', 'draw_thickness', 'font_scale'}

    def yolo2mark(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        yolo_path = f'{root}/{img_name}.txt'
        if os.path.exists(yolo_path):
            yolo_data = fFile().read(yolo_path)
            yolo_data = yolo_data.strip().split('\n')
            yolo_data = [line.split(' ') for line in yolo_data]
        else:
            yolo_data = []
        if len(yolo_data) > 0:
            img = fImg().read(img_path)
            img_size = img.shape[:2]
        else:
            img, img_size = None, (0, 0)

        mark_data, contours = [], []
        shape_type = ['point', 0, 'polygon']
        for yolo in yolo_data:
            label_index = int(yolo[0])
            if config['mark_type'] == 'detect':
                x1, y1, x2, y2 = self.yolo2voc([float(_) for _ in yolo[1:5]], img_size)
                points = [[x1, y1], [x2, y2]]
                conf = float(yolo[5]) if len(yolo) > 5 else 0.0
            elif config['mark_type'] == 'obb':
                points = [[float(yolo[i * 2 + 1]), float(yolo[i * 2 + 2])] for i in range(4)]
                conf = float(yolo[9]) if len(yolo) > 9 else 0.0
            elif config['mark_type'] == 'segment':
                points = [[float(yolo[i * 2 + 1]) * img_size[1], float(yolo[i * 2 + 2]) * img_size[0]] for i in
                          range((len(yolo) - 1) // 2)]
                conf = float(yolo[-1]) if len(yolo) % 2 == 0 else 0.0
                # conf = 0.0
            if label_index < len(config['mark_labels']):
                label = config['mark_labels'][label_index]
            else:
                label = f'label_{label_index}'
                config['logger'].log(f'[warn]未包含的标签: {yolo_path}, {label_index}\n')
                config['cnt'][1] += 1
            mark_data.append([label, points, shape_type[min(len(points), 3) - 1], conf])
            # conf_text = f' {conf}' if conf > 0 else ''
            # if config['is_draw']:
            #     if len(points) == 2:
            #         points = fshape.convert_rectangle(points)
            #     (x1, y1), (x2, y2) = fmath.cal_min_enclosing_rec(points)
            #     if config['mark_type'] == 'segment': x1, y1 = (x1 + x2) / 2, (y1 + y2) / 2
            #     contours.append([points, f'{label}{conf_text}', (round(x1), round(y1))])
        output_dir = root
        if config['scan_path'] != config['output_path']:  # 只有输出目录与遍历目录不同才可绘框
            output_dir = root.replace(config['scan_path'], config['output_path'])
            if config['is_draw'] and len(mark_data) > 0:  # 绘框且可以绘框
                for contour in contours:
                    cv2.drawContours(img, [numpy.array(contour[0], dtype=numpy.int32)], -1,
                                     config['draw_color'], config['draw_thickness'])
                    cv2.putText(img, contour[1], contour[2], cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=config['font_scale'], thickness=config['draw_thickness'],
                                color=config['draw_color'])
                fImg().readin(f'{output_dir}/{img_name}{img_suffix}', img)
            else:
                fFile().copy(img_path, output_dir)
        if len(mark_data) > 0:
            config['mark_funcs'][config['mark_suffix']]['readin'](f'{output_dir}/{img_name}{img_suffix}', img_size,
                                                                  mark_data)
        config['cnt'][0] -= 1

    # mask图片
    def mask_img_init(self, config):
        if 'draw_color' not in config: config['draw_color'] = (0, 0, 0)
        return config, {'logger',
                        'mark_suffix', 'mark_funcs', 'mask_labels', 'draw_color'}

    def mask_img(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1] if os.path.exists(
            mark_path) else []

        contours = []
        for i in range(len(mark_data) - 1, -1, -1):
            if mark_data[i][0] in config['mask_labels']:
                if mark_data[i][2] == 'polygon':
                    contours.append(mark_data[i][1])
                elif mark_data[i][2] in ['rectangle', 0, 1]:
                    x1, y1, x2, y2 = fShape().read_rectangle(mark_data[i][1])
                    # 标注软件无法标注到0
                    if x1 <= 1: x1 = 0
                    if y1 <= 1: y1 = 0
                    contours.append(fShape().convert_rectangle(mark_data[i][1]))
                else:
                    config['logger'].log(f'[warn]未受支持的标签类型: {mark_path}, {mark_data[i][2]}\n')
                    config['cnt'][1] += 1
                    continue
                del mark_data[i]

        if len(contours) > 0:
            img = fImg().read(img_path)
            img_size = img.shape[:2]
            for contour in contours:
                cv2.drawContours(img, [numpy.array(contour, dtype=numpy.int32)], -1, config['draw_color'], -1)
            fImg().readin(img_path, img)
            config['mark_funcs'][config['mark_suffix']]['readin'](img_path, img_size, mark_data)
        config['cnt'][0] -= 1

    # 移除重叠框
    def remove_specific_overlap_init(self, config):
        if 'iou_thres' not in config: config['iou_thres'] = 0  # 重合iou阈值
        return config, {'logger',
                        'mark_suffix', 'mark_funcs', 'mark_labels', 'iou_thres'}

    def remove_specific_overlap(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        _, img_size, mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path) \
            if os.path.exists(mark_path) else (None, (0, 0), [])
        specific_data = list(filter(lambda mark: mark[0] in config['mark_labels'], mark_data))
        if len(specific_data) > 0:
            specific_region = Polygon()
            for specific in specific_data:
                if specific[2] == 'polygon':
                    specific_region = specific_region.union(Polygon(specific[1]))
                elif specific[2] in ['rectangle', 0, 1]:
                    specific_region = specific_region.union(Polygon(fMath().structure_rec(specific[1])))
                else:
                    config['logger'].log(f'[warn]未受支持的标签类型: {mark_path}, {specific[2]}\n')
                    config['cnt'][1] += 1
                    continue
            del_cnt = 0
            specific_area = specific_region.area
            for i in range(len(mark_data) - 1, -1, -1):
                if mark_data[i][0] not in config['mark_labels']:
                    if mark_data[i][2] == 'polygon':
                        mark_region = Polygon(mark_data[i][1])
                    elif mark_data[i][2] in ['rectangle', 0, 1]:
                        mark_region = Polygon(fMath().structure_rec(mark_data[i][1]))
                    else:
                        config['logger'].log(f'[warn]未受支持的标签类型: {mark_path}, {mark_data[i][2]}\n')
                        config['cnt'][1] += 1
                        continue
                    if mark_region.intersection(specific_region).area / min(mark_region.area, specific_area) > config[
                        'iou_thres']:
                        del mark_data[i]
                        del_cnt += 1
            if del_cnt > 0:
                config['mark_funcs'][config['mark_suffix']]['readin'](img_path, img_size, mark_data)
        config['cnt'][0] -= 1

    # 图片与标注按标签分类
    def split_mark_init(self, config):
        return config, {'output_path', 'mark_suffix', 'mark_funcs'}

    def split_img(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        if os.path.exists(mark_path):
            _, _, mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)
        else:
            mark_data = []
            mark_path = None
        labels = list(set([mark[0] for mark in mark_data]))
        if len(labels) == 0:
            target_dir = f'{config["output_path"]}/empty'
            os.remove(mark_path) if mark_path is not None else None
        else:
            target_dir = f'{config["output_path"]}/{labels[0] if len(labels) == 1 else "dupli"}'
            if os.path.exists(f'{target_dir}/{img_name}{config["mark_suffix"]}') is False:
                fFile().copy(mark_path, target_dir, is_move=True)
        if os.path.exists(f'{target_dir}/{img_name}{img_suffix}') is False:
            fFile().copy(img_path, target_dir, is_move=True)
        config['cnt'][0] -= 1

    # 按是否标注区分
    def split_with_is_marked_init(self, config):
        return config, {'scan_path', 'output_path', 'mark_suffix', 'mark_funcs', 'is_marked'}

    def split_with_is_marked(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        if os.path.exists(mark_path):
            mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1]
            os.remove(mark_path) if len(mark_data) == 0 else None
        else:
            mark_data = []
        if (len(mark_data) > 0) is config['is_marked']:
            if config['is_marked']:
                fFile().copy(mark_path, root.replace(config['scan_path'], config['output_path']), is_move=True)
            fFile().copy(img_path, root.replace(config['scan_path'], config['output_path']), is_move=True)
        config['cnt'][0] -= 1

    # 按是否含有code区分
    def split_with_is_has_code_init(self, config):
        return config, {'scan_path', 'output_path', 'mark_suffix', 'mark_funcs', 'is_has_code', 'is_only_has_code'}

    def split_with_is_has_code(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1] if os.path.exists(
            mark_path) else []
        codes = set([mark[0] for mark in mark_data])
        specific_codes = set(config['mark_labels'])
        if (len(codes & specific_codes) > 0) is config['is_has_code']:
            if config['is_only_has_code'] is False or (len(codes | specific_codes) == len(codes)) is config[
                'is_only_has_code']:
                fFile().copy(img_path, root.replace(config['scan_path'], config['output_path']), is_move=True)
                fFile().copy(mark_path, root.replace(config['scan_path'], config['output_path']), is_move=True)
        config['cnt'][0] -= 1

    # 裁剪标注区域
    def crop_mark_init(self, config):
        return config, {'output_path', 'mark_suffix', 'mark_funcs'}

    def crop_mark(self, config, file):
        root, img_name, img_suffix = file
        img_path = f'{root}/{img_name}{img_suffix}'
        mark_path = f'{root}/{img_name}{config["mark_suffix"]}'
        mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1] if os.path.exists(
            mark_path) else []
        img = fImg().read(img_path) if len(mark_data) > 0 else None
        for shape in mark_data:
            if shape[2] in ['rectangle', 0, 1]:
                x1, y1, x2, y2 = fShape().read_rectangle(shape[1])
                crop_img = img[y1:y2, x1:x2]
                crop_img_path = f'{config["output_path"]}/{img_name}_{shape[0]}{img_suffix}'
                fImg().readin(crop_img_path, crop_img)
            elif shape[2] in ['polygon']:
                x = [point[0] for point in shape[1]]
                y = [point[1] for point in shape[1]]
                x1, y1, x2, y2 = min(x), min(y), max(x), max(y)
                crop_img = img[y1:y2, x1:x2]
                crop_img_path = f'{config["output_path"]}/{img_name}_{shape[0]}{img_suffix}'
                fImg().readin(crop_img_path, crop_img)
                crop_mark_data = [[shape[0], [[point[0] - x1, point[1] - y1] for point in shape[1]], 'polygon']]
                config['mark_funcs'][config['mark_suffix']]['readin'](crop_img_path, crop_img.shape[:2], crop_mark_data)
            else:
                continue
        config['cnt'][0] -= 1

    # ----------------------------------------
    # 列表操作

    # 标签计数
    def count_labels_init(self, config):
        config['is_process_file'] = False
        if 'is_count_file' not in config: config['is_count_file'] = False
        if 'is_count_with_conf' not in config: config['is_count_with_conf'] = False
        return config, {'logger', 'mark_suffix', 'mark_funcs', 'is_count_file', 'is_count_with_conf'}

    def count_labels(self, config, scan_files):
        labels_cnt = defaultdict(lambda: 0)
        for file in tqdm(scan_files) if config['print_switch'] else scan_files:
            config['cnt'][0] += 1
            while True:
                if config['cnt'][0] <= config['workers']:
                    threading.Thread(target=self.count_labels_scan,
                                     args=(config, config['cnt'], f'{file[0]}/{file[1]}{file[2]}', labels_cnt)).start()
                    break
        while config['cnt'] > 0:
            pass
        if 'replace_labels' in config:
            for key, value in config['replace_labels'].items():
                labels_cnt[value] = labels_cnt.pop(key) if key in labels_cnt else 0
        labels = list(labels_cnt.keys())
        labels.sort()
        labels_cnt = pprint.pformat(dict(labels_cnt), sort_dicts=True)
        config['logger'].print(f'{len(labels)}: {labels}')
        config['logger'].print(labels_cnt)
        config['logger'].log(f'{labels}\n')
        config['logger'].log(f'{labels_cnt}\n')

    # 文件标签计数
    def count_labels_scan(self, config, cnt, mark_path, labels_cnt):
        mark_data = config['mark_funcs'][config['mark_suffix']]['read'](mark_path)[-1]
        labels = [f'{mark[0]}{f":{mark[3]}" if config["is_count_with_conf"] and mark[3] >= 0 else ""}' for mark in
                  mark_data]
        labels = set(labels) if config['is_count_file'] else labels
        for label in labels:
            labels_cnt[label] += 1
        cnt[0] -= 1

    # 匹配图片与标注
    def match_img_mark_init(self, config):
        config['is_process_file'] = False
        config['is_move_mark'] = config['is_move_mark'] if 'is_move_mark' in config else True  # 移动标注向图片对齐
        return config, {'scan_path', 'mark_suffix', 'is_move_mark'}

    def match_img_mark(self, config, scan_files):
        dicta, dcitb = defaultdict(lambda: list()), defaultdict(lambda: list())
        for file in scan_files:
            if (file[2].lower() == config['mark_suffix']) if config['is_move_mark'] else (
                    file[2].lower() != config['mark_suffix']):
                dcitb[file[1]].append([file[0], file[2]])
            else:
                dicta[file[1]].append([file[0], file[2]])
        for name_b, pairs_b in tqdm(dcitb.items()) if config['print_switch'] else dcitb.items():
            config['cnt'][0] += 1
            while True:
                if config['cnt'][0] <= config['workers']:
                    threading.Thread(target=self.match_img_mark_scan,
                                     args=(config, config['cnt'], dicta, name_b, pairs_b)).start()
                    break

    # 文件匹配
    def match_img_mark_scan(self, config, cnt, dicta, name_b, pairs_b):
        # 若同名标注存在多个或无同名图片或同名图片存在多个,不匹配
        is_match = False if len(pairs_b) > 1 or name_b not in dicta or len(dicta[name_b]) > 1 else True
        for pair in pairs_b:
            path_b = f'{pair[0]}/{name_b}{pair[1]}'
            target_dir_path = dicta[name_b][0][0] if is_match \
                else pair[0].replace(config['scan_path'], f'{config["scan_path"]}_dismatch')
            fFile().copy(path_b, target_dir_path, is_move=True)
        cnt[0] -= 1

    # 划分数据集
    def divide_files_init(self, config):
        config['is_process_file'] = False
        return config, {'scan_path', 'output_path', 'logger',
                        'mark_suffix', 'divide', 'layering'}

    def divide_files(self, config, scan_files):
        if config["layering"] is False:  # 比例划分
            self.divide_entirety(config, config['cnt'], scan_files, deepcopy(config["divide"]))
        else:  # 分层划分转为分层比例划分
            layering_length = sum(config["divide"])  # 分层长度
            layering_divide = [_ / layering_length for _ in config["divide"]]  # 分层划分比例
            layering_num = len(scan_files) // layering_length  # 完整分层数
            layering_last = len(scan_files) % layering_length  # 不完整层图片数
            for i in range(layering_num):
                layering_list = scan_files[i * layering_length:(i + 1) * layering_length]
                self.divide_entirety(config, config['cnt'], layering_list, deepcopy(layering_divide))
            if layering_last > 0:
                layering_list = scan_files[-layering_last:]
                self.divide_entirety(config, config['cnt'], layering_list, deepcopy(layering_divide))

    # 按比例划分数据集
    def divide_entirety(self, config, cnt, file_list, divide):
        if sum(divide) > 1:
            config['logger'].log(f'[error]划分比例错误: {divide}\n')
            return
        numpy.random.shuffle(file_list)
        for i in range(len(divide)):
            divide[i] = round(divide[i] * len(file_list))  # 每比例文件数
            divide_list = file_list[sum(divide[:i]):sum(divide[:i + 1])]
            for file_path in tqdm(divide_list) if config['print_switch'] else divide_list:
                cnt[0] += 1
                while True:
                    if cnt[0] <= config['workers']:
                        threading.Thread(target=self.divide_entirety_scan, args=(config, cnt, i, file_path)).start()
                        break

    def divide_entirety_scan(self, config, cnt, i, file_path):
        img_dir, img_name, img_suffix = file_path
        output_dir = img_dir.replace(config['scan_path'], f'{config["output_path"]}/divide{i}')
        fFile().copy(f'{img_dir}/{img_name}{img_suffix}', output_dir)
        if 'mark_suffix' in config:
            mark_path = f'{img_dir}/{img_name}{config["mark_suffix"]}'
            if os.path.exists(mark_path):
                fFile().copy(mark_path, output_dir)
        cnt[0] -= 1


if __name__ == "__main__":
    pass
