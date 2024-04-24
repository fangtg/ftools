import os
import json
import shutil


class fFile:
    def __init__(self, encoding='utf-8', is_check_folder=True):
        self.encoding = encoding
        self.is_check_folder = is_check_folder

    def read(self, file_path):
        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as file:
            return file.read()

    def readin(self, file_path, content):
        if self.is_check_folder: os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=self.encoding) as file:
            file.write(content)

    def copy(self, file_path, target_path, is_move=False, is_cover=False):
        file_base = os.path.basename(file_path)
        if os.path.splitext(target_path)[-1] == '':
            target_dir_path, target_file_base = target_path, file_base
        else:
            target_dir_path, target_file_base = os.path.split(target_path)
        target_path = f'{target_dir_path}/{target_file_base}'
        if self.is_check_folder: os.makedirs(target_dir_path, exist_ok=True)
        is_exists = os.path.exists(target_path)
        if not is_cover and is_exists:
            return False
        else:
            if is_exists: os.remove(target_path)
            if is_move:
                shutil.move(file_path, target_dir_path)
            else:
                shutil.copy(file_path, target_dir_path)
            if target_file_base != file_base: os.rename(f'{target_dir_path}/{file_base}', target_path)
            return True

    def scan(self, scan_path, file_suffixes=None):
        if type(file_suffixes) == str: file_suffixes = [file_suffixes]
        file_paths = list()
        for root, dirs, files in os.walk(scan_path):
            for file in files:
                if file_suffixes is None or os.path.splitext(file)[-1].lower() in file_suffixes:
                    file_paths.append(f'{root}/{file}')
        return file_paths


class fTxt(fFile):
    def __init__(self, encoding='utf-8', is_check_folder=True):
        super().__init__(encoding=encoding, is_check_folder=is_check_folder)

    def add(self, file_path, content):
        if self.is_check_folder: os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a', encoding=self.encoding) as file:
            file.write(content)


class fJson(fFile):
    def __init__(self, encoding='utf-8', is_check_folder=True, indent=None):
        super().__init__(encoding=encoding, is_check_folder=is_check_folder)
        self.indent = indent

    def read(self, file_path):
        with open(file_path, 'r', encoding=self.encoding) as file:
            return json.load(file)

    def readin(self, file_path, content):
        if self.is_check_folder: os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=self.encoding) as file:
            json.dump(content, file, indent=self.indent, ensure_ascii=False)

    def str2dict(self, content):
        return json.loads(content)


class fXml(fFile):
    def __init__(self, encoding='utf-8', is_check_folder=True):
        super().__init__(encoding=encoding, is_check_folder=is_check_folder)

    def read(self, file_path):
        import xmltodict
        return xmltodict.parse(super().read(file_path), encoding=self.encoding)

    def readin(self, file_path, content):
        import xmltodict
        xml_data = xmltodict.unparse(content, pretty=True)
        super().readin(file_path, xml_data)


if __name__ == '__main__':
    pass
