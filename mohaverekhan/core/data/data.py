import os
import sys, codecs
from mohaverekhan.core.tools import utils

logger = utils.get_logger(logger_name='data')
logger.info('-------------------------------------------------------------------')

DATA_PATH = os.path.dirname(__file__)

# def read_dictionary_from_file(dictionary_file_name):
#     dictionary_file_path = os.path.join(DATA_PATH, dictionary_file_name)
#     logger.info(f'>> Reading dictionary ({dictionary_file_path})')
#     with codecs.open(dictionary_file_path, encoding='utf-8') as dictionary_file:
#         items = [line.strip('\n').split('|')[1:3] for line in dictionary_file]
#         # items = [line.split('|')[0:2] for line in dictionary_file]
#         logger.info(f'>> Items : {items}')
#         dictionary = {item[0]:item[1] for item in items}
#         logger.info(f'>> Dictionary : {dictionary}')
#         return dictionary

TRANSLATION_CHARACTERS = {}
REFINEMENT_PATTERNS = []

# HAZM_TRANSLATION_CHARACTERS = read_dictionary_from_file('hazm_translation_characters.dat')
# logger.info(f'>> HAZM_TRANSLATION_CHARACTERS : {HAZM_TRANSLATION_CHARACTERS}')

# REFI
# HAZM_REFINEMENT_PATTERNS = read_dictionary_from_file('hazm_refinement_patterns.dat').items()
# print(f'>> HAZM_REFINEMENT_PATTERNS : {HAZM_REFINEMENT_PATTERNS}')


