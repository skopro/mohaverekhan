import logging
import datetime
import os
import time

from pathlib import Path

logger = None
HOME = str(Path.home())
LOG_ROOT_DIR = os.path.join(HOME, 'bitianist', 'logs')
LOG_FORMAT = '[ %(levelname)s ][ %(asctime)s ][ %(process)d %(thread)d ][ %(module)s %(lineno)d ][ %(message)s ]'

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'data')

loggers = {}

def get_logger(**kwargs):
    logger_name = kwargs.get('logger_name', 'main')
    if logger_name in loggers:
        return loggers[logger_name]
    now_date = datetime.datetime.now().date().__str__()
    log_dir = os.path.join(LOG_ROOT_DIR, now_date)
    os.makedirs(log_dir, exist_ok=True)

    log_file_path = os.path.join(log_dir, f'{logger_name}.log')
    print(f'> Getting logger : {log_file_path}')

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    loggers[logger_name] = logger
    return logger
    

def time_usage(logger):
    def decorator(function):
        def wrapper(*args, **kwargs):
            beg_ts = time.time()
            result = function(*args, **kwargs)
            end_ts = time.time()
            logger.info(f"> (Time)({function.__name__})({end_ts - beg_ts:.6f})")
            return result
        return wrapper
    return decorator

def init():
    global logger
    logger = logging.getLogger(__name__)
    # logger = get_logger(logger_name='utils')