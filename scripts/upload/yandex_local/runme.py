""" Simply runs data import """


import sys
from scripts.upload.yandex_local.uploader import Uploader


if __name__ == '__main__':
    # Find arg with config file path
    config_file_path = None
    for arg in sys.argv:
        if arg.startswith('-config='):
            config_file_path = arg[8:]
            break

    if config_file_path:
        uploader = Uploader(config_file_path)
        uploader.run()
    else:
        print('You must provide -config=path_to_conf_file argument.')
        exit(1)
