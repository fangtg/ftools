"""
time: 20240201
"""
import os
import threading
from ftime import fTime
from flog import fLog
from tqdm import tqdm


class fScan:
    def process(self, config):
        if 'log_switch' not in config: config['log_switch'] = True  # 日志开关
        if 'print_switch' not in config: config['print_switch'] = True  # 打印开关
        if 'log_dir' not in config: config['log_dir'] = config['scan_path']  # 默认日志目录
        config['log_path'] = f'{config["log_dir"]}/{fTime().format()}_{config["method"].__name__}.txt'
        config['logger'] = fLog(config['print_switch'], config['log_switch'], config['log_path'])  # 日志器

        arguments = {'scan_path', 'scan_suffixes', 'workers', 'method', 'method_init', 'is_process_file'}
        config, arguments_init = config['method_init'](config)
        if 'is_process_file' not in config: config['is_process_file'] = True
        lack_argument = (arguments | arguments_init) - set(config.keys())
        assert len(lack_argument) == 0, config['logger'].log(f'[error]缺少参数: {lack_argument}')

        scan_files, config['cnt'] = [], [0, 0, 0]
        for root, dirs, files in os.walk(config['scan_path']):
            for file in files:
                file_name, file_suffix = os.path.splitext(file)
                if file_suffix.lower() in config['scan_suffixes'] or len(config['scan_suffixes']) == 0:
                    scan_files.append([root, file_name, file_suffix])
        if config['is_process_file']:
            for file in tqdm(scan_files) if config['print_switch'] else scan_files:
                config['cnt'][0] += 1
                while True:
                    if config['cnt'][0] <= config['workers']:
                        if config['workers'] > 1:
                            threading.Thread(target=config['method'], args=(config, file)).start()
                        else:
                            config['method'](config, file)
                        break
        else:
            config['method'](config, scan_files)
        while config['cnt'][0] > 0: pass

        output_process = f'process: {len(scan_files)}'
        output_warn = f'warn: {config["cnt"][1]}\t' if config['cnt'][1] > 0 else ''
        output_error = f'error: {config["cnt"][2]}\t' if config['cnt'][2] > 0 else ''
        process_info = f'complete\n{output_process}{output_warn}{output_error}'
        config['logger'].print(f'{process_info}')
        config['logger'].log(f'{process_info}\n')


if __name__ == '__main__':
    pass
