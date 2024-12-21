import logging
from colorlog import ColoredFormatter

def setup_logger():
    # Konfiguracja colorlog
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s:%(levelname)s:%(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Konfiguracja loggera
    logger = logging.getLogger('git_sync')
    logger.setLevel(logging.INFO)

    # Handler dla pliku logów
    file_handler = logging.FileHandler('sync_repos.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
    logger.addHandler(file_handler)

    # Handler dla konsoli z kolorami
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
