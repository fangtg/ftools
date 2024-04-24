"""
time: 20231215
"""
from ffile import fFile
from fscan import fScan


def encode(content, mi, mi_num_len):
    output, unmi = [], []
    for i, c in enumerate(content):
        if c in mi:
            if len(unmi) > 0:
                output.extend(unmi[::-1])
                unmi.clear()
            output.append(str(mi.index(c)).rjust(mi_num_len, '0'))
        else:
            unmi.append(c)
    return ''.join(output)[::-1]


def decode(content, mi, mi_num_len):
    output, unmi, gather = [], [], ''
    for i, c in enumerate(content):
        if c.isdigit():
            if len(unmi) > 0:
                output.extend(unmi[::-1])
                unmi.clear()
            gather += c
            if len(gather) == mi_num_len:
                output.append(mi[int(gather[::-1])])
                gather = ''
            else:
                continue
        else:
            if len(gather) > 0:
                return False
            unmi.append(c)
    return ''.join(output)[::-1]


def coding_init(config):
    config['is_process_file'] = True
    return config, {'scan_path', 'output_path', 'second_method', 'mi'}


def coding(config, cnt, root, file_name, file_suffix):
    file_path = f'{root}/{file_name}{file_suffix}'
    file_data = fFile().read(file_path)
    mi_num_len = len(str(len(config['mi'])))  # 密本数量长度
    output_data = config['second_method'](file_data, config['mi'], mi_num_len)
    new_file_base = config['second_method'](f'{file_name}{file_suffix}', config['mi'], mi_num_len)
    fFile().readin(f'{root.replace(config["scan_path"], config["output_path"])}/{new_file_base}', output_data)
    cnt[0] -= 1


if __name__ == '__main__':
    config = dict()

    config['scan_path'] = r'E:\edesktop\workroom\project\helper\win_'
    # config['scan_suffixes'] = ['.py']
    config['scan_suffixes'] = []
    config['workers'] = 32
    config['method'] = coding
    config['method_init'] = coding_init
    # config['second_method'] = encode
    config['second_method'] = decode
    config['output_path'] = r'E:\edesktop\workroom\project\helper\win'
    config['mi'] = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g',
        'h', 'i', 'j', 'k', 'l', 'm', 'n',
        'o', 'p', 'q', 'r', 's', 't',
        'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G',
        'H', 'I', 'J', 'K', 'L', 'M', 'N',
        'O', 'P', 'Q', 'R', 'S', 'T',
        'U', 'V', 'W', 'X', 'Y', 'Z',
        '\n', '\t', ' ',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',
        '[', ']', '{', '}', '\\', '|', ';', ':', '\'', '"',
        ',', '.', '<', '>', '/', '?'
    ]
    config['mi'].sort()

    # # 自动转码
    # fScan().scan_process(config)

    # 手动解密
    with open(r'../yanrui2/09186148970847586658970787276853960797477687087367486687', 'r', encoding='utf-8') as file:
        content = file.read()
    content = decode(content, config["mi"], len(str(len(config["mi"]))))
    with open(r'../yanrui2/maskCombinedAugmentations.py', 'w', encoding='utf-8') as file:
        file.write(content)
