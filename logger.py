import logging
from logging.handlers import TimedRotatingFileHandler
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

    # Handler dla pliku logów z rotacją (np. codziennie o północy)
    file_handler = TimedRotatingFileHandler(
        'sync_repos.log',  # nazwa pliku logów
        when='midnight',   # obracanie pliku o północy
        interval=1,        # co 1 dzień
        backupCount=7      # przechowywanie 7 kopii zapasowych
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))
    logger.addHandler(file_handler)

    # Handler dla konsoli z kolorami
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
