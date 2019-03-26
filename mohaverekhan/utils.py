import logging
import datetime
import os
import time
# import glob
# import xml.etree.ElementTree as ET
# import errno

from pathlib import Path

# # default_words = os.path.join(data_path, 'words.dat')
# # default_stopwords = os.path.join(data_path, 'stopwords.dat')
# # default_verbs = os.path.join(data_path, 'verbs.dat')
# # informal_words = os.path.join(data_path, 'iwords.dat')
# # informal_verbs = os.path.join(data_path, 'iverbs.dat')

# logging.basicConfig(filename= os.path.join(LOG_DIR, 'main.txt'),level=logging.DEBUG,
#         format = )
HOME = str(Path.home())
LOG_ROOT_DIR = os.path.join(HOME, 'bitianist', 'logs')
LOG_FORMAT = '[ %(levelname)s ][ %(asctime)s ][ %(process)d %(thread)d ][ %(module)s %(lineno)d ][ %(message)s ]'

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'data')
# tagged_sentence_list, tagged_token_list = [], []
# token_set, word_set = set(), set()
# tag_example_dic = {}

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
    

# def add_example_to_tag(tag, word):
#     global tag_example_dic
#     if tag not in tag_example_dic:
#         tag_example_dic[tag] = [word]
#     else:
#         tag_example_list = tag_example_dic[tag]
#         if len(tag_example_list) < 50 and word not in tag_example_list:
#             tag_example_list.append(word)
#             tag_example_dic[tag] = tag_example_list
    
# def read_all_tokens():
#     global tagged_sentence_list, tagged_token_list, token_set, word_set, tag_example_dic
#     data_dir = r'/home/bitianist/Dropbox/bachelor_thesis/data/pos/bijankhan-online/unannotated'
#     logger.info(f'>> Read data from {data_dir}')
#     files = glob.glob(fr'{data_dir}/*.xml')
#     xml_string, token, tag = '', '', ''
#     tagged_sentence_count = 0
#     for xml_file in files:
#         try:
#             with open(xml_file, mode="r", encoding="utf-8") as xf:
#                 logger.info(f'>> reading file "{os.path.basename(xml_file)}"')
#                 xml_string = xf.read()
#                 tree = ET.ElementTree(ET.fromstring(xml_string))
#                 root = tree.getroot()
#                 tagged_sentence = []
#                 for tagged_token_xml in root.findall('*'):
#                     token = tagged_token_xml.find('w').text
#                     tag = tagged_token_xml.find('tag').text[0]
#                     token_set.add(token)
#                     if tag != 'O' or tag != 'U':
#                         word_set.add(token)
#                     tagged_token_list.append((token, tag))
#                     add_example_to_tag(tag, token)
#                     tagged_sentence.append(tagged_token_list[-1])
#                     if token == '.':
#                         tagged_sentence_list.append(tagged_sentence)
#                         tagged_sentence = []
                    
#                 logger.info(f'> {len(tagged_sentence_list) - tagged_sentence_count} sentences added.')
#                 tagged_sentence_count = len(tagged_sentence_list)
#         except IOError as exc:
#             if exc.errno != errno.EISDIR:
#                 logger.exception(exc)

#     logger.info(f'>> Tag example dic ({len(tag_example_dic)} tags)')
#     for tag, examples in tag_example_dic.items():
#         logger.info(f'{tag} : {examples}')

#     logger.info(f'>> Tagged sentence list example ({len(tagged_sentence_list)} tagged_sentences)')
#     for i in range(0, len(tagged_sentence_list), int(len(tagged_sentence_list)/20)):
#         logger.info(f'tagged_sentence_list[{i}] : {tagged_sentence_list[i]}')

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
    logger = get_logger(logger_name='utils')
    pass
#     # read_all_tokens()