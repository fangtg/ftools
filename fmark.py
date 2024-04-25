import os
import xml.etree.ElementTree as ET

from ffile import fTxt, fJson


class fMark:
    def __init__(self, is_round=False, is_check_folder=True, allow_empty=False, conf_sep=':'):
        self.is_round = is_round
        self.is_check_folder = is_check_folder
        self.allow_empty = allow_empty
        self.conf_sep = conf_sep

    def read(self, mark_path):
        pass

    def readin(self, img_path, img_size, data):
        pass

    def structure(self, box):
        pass


class fXmlMark(fMark):
    def __init__(self, is_round=True, is_check_folder=True, allow_empty=False, conf_sep=':'):
        super().__init__(is_round=is_round, is_check_folder=is_check_folder, allow_empty=allow_empty, conf_sep=conf_sep)

    def read(self, xml_path):
        if os.path.exists(xml_path) is False: return '', (0, 0), list()
        tree = ET.parse(xml_path)  # speed limit
        root = tree.getroot()
        xml_data = list()
        img_path = root.find('path').text if root.find('path') is not None else ''
        img_size = (int(root.find('size').find('height').text)
                    if root.find('size') is not None and root.find('size').find('height') is not None else 0,
                    int(root.find('size').find('width').text)
                    if root.find('size') is not None and root.find('size').find('width') is not None else 0)
        for obj in root.iter('object'):
            name = obj.find('name').text.split(self.conf_sep) if obj.find('name') is not None else ['']
            label = name[0]
            conf = float(name[1]) if len(name) == 2 else -1
            difficult = int(obj.find('difficult').text) if obj.find('difficult') is not None else 0
            bbox = obj.find('bndbox')
            x1 = float(bbox.find('xmin').text) if bbox is not None and bbox.find('xmin') is not None else 0
            y1 = float(bbox.find('ymin').text) if bbox is not None and bbox.find('ymin') is not None else 0
            x2 = float(bbox.find('xmax').text) if bbox is not None and bbox.find('xmax') is not None else 0
            y2 = float(bbox.find('ymax').text) if bbox is not None and bbox.find('ymax') is not None else 0
            if self.is_round:
                x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)
            xml_data.append([label, [[x1, y1], [x2, y2]], difficult, conf])
        return img_path, img_size, xml_data

    def readin(self, img_path, img_size, objects, img_suffix='.bmp'):
        if os.path.splitext(img_path)[1].lower() == '.xml': img_path = f'{os.path.splitext(img_path)[0]}{img_suffix}'
        img_dir, img_base = os.path.split(img_path)
        img_folder = os.path.basename(img_dir)
        xml_path = f'{os.path.splitext(img_path)[0]}.xml'
        if len(objects) == 0:
            if not self.allow_empty:
                if os.path.exists(xml_path): os.remove(xml_path)
                return
        object_data = [self.structure(mark) for mark in objects]
        # num(objects) == 1
        if len(object_data) == 1:
            object_data = object_data[0]
        xml_data = {
            'annotation': {
                'folder': img_folder, 'filename': img_base, 'path': img_path,
                'source': {'database': 'Unknown'},
                'size': {'width': img_size[1], 'height': img_size[0], 'depth': 3},
                'segmented': 0,
                'object': object_data
            }
        }
        import xmltodict
        xml_data = xmltodict.unparse(xml_data, pretty=True)  # speed limit
        xml_data = xml_data[xml_data.find('\n') + len('\n'):]
        fTxt(is_check_folder=self.is_check_folder).readin(xml_path, xml_data)

    def structure(self, box):
        """
        :param box: 标注框信息, [label, [[xmin, ymin], [xmax, ymax]], difficult, conf]
        :return: xml格式标注框
        """
        (x1, y1), (x2, y2) = box[1]
        if self.is_round:
            x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)
        object = {
            'name': f'{box[0]}{self.conf_sep}{box[3]}' if len(box) == 4 and box[3] != -1 else box[0],
            'pose': 'Unspecified', 'truncated': 0, 'difficult': box[2],
            'bndbox': {
                'xmin': min(x1, x2), 'ymin': min(y1, y2),
                'xmax': max(x1, x2), 'ymax': max(y1, y2)
            }
        }
        return object


class fJsonMark(fMark):
    def __init__(self, is_round=False, is_check_folder=True, allow_empty=False, conf_sep=':', indent=4):
        super().__init__(is_round=is_round, is_check_folder=is_check_folder, allow_empty=allow_empty, conf_sep=conf_sep)
        self.indent = indent

    def read(self, json_path):
        if os.path.exists(json_path) is False: return '', (0, 0), list()
        json_data = fJson().read(json_path)  # speed limit
        img_base = json_data['imagePath'] if 'imagePath' in json_data else ''
        img_size = (json_data['imageHeight'], json_data['imageWidth']) \
            if 'imageHeight' in json_data and 'imageWidth' in json_data else (0, 0)
        shapes = [
            [
                str(mark['label']).split(self.conf_sep)[0], mark['points'],
                mark['shape_type'] if 'shape_type' in mark else 'Polygon',
                float(str(mark['label']).split(self.conf_sep)[1]) if len(str(mark['label']).split(':')) == 2 else -1.0
            ]
            for mark in json_data['shapes']
        ]
        return img_base, img_size, shapes

    def readin(self, img_path, img_size, shapes, version='5.1.1', img_suffix='.bmp'):
        if os.path.splitext(img_path)[1].lower() == '.json': img_path = f'{os.path.splitext(img_path)[0]}{img_suffix}'
        img_base = os.path.basename(img_path)
        json_path = f'{os.path.splitext(img_path)[0]}.json'
        if len(shapes) == 0:
            if not self.allow_empty:
                if os.path.exists(json_path): os.remove(json_path)
                return
        json_data = {
            'version': version, 'flags': {}, 'shapes': [self.structure(mark) for mark in shapes],
            'imagePath': img_base, 'imageData': None,
            'imageHeight': img_size[0], 'imageWidth': img_size[1],
        }
        fJson(is_check_folder=self.is_check_folder, indent=4).readin(json_path, json_data)  # speed limit

    def structure(self, box):
        """
        :param box: 标注信息, [label, [[x1, y1], [x2, y2], ... , [x∞, y∞]], shape_type, conf]
        shape_type: polygon, rectangle, circle, line, point, linestrip
        :return: json格式标注框
        """
        shape = {
            'label': f'{box[0]}{self.conf_sep}{box[3]}' if len(box) == 4 and box[3] != -1 else str(box[0]),
            'points': box[1], 'group_id': None,
            'shape_type': box[2] if box[2] not in [0, 1] else 'rectangle',
            'flags': {}
        }
        return shape


if __name__ == '__main__':
    pass
