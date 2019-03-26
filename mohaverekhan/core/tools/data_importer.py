import requests
import os
import pandas as pd

import multiprocessing
import json
import glob
from joblib import Parallel, delayed
import xml.etree.ElementTree as ET
import errno
import re
if __name__ == '__main__':
    import utils
else:
    from mohaverekhan.core.tools import utils

logger = utils.get_logger(logger_name='data_importer')

base_api_url = r'http://127.0.0.1:8000/mohaverekhan/api'
normalizers_url = fr'{base_api_url}/normalizers'
texts_url = fr'{base_api_url}/texts'
normal_texts_url = fr'{base_api_url}/normal-texts'
tags_url = fr'{base_api_url}/tags'
tag_sets_url = fr'{base_api_url}/tag-sets'
taggers_url = fr'{base_api_url}/taggers'
sentences_url = fr'{base_api_url}/sentences'
tagged_sentences_url = fr'{base_api_url}/tagged-sentences'
translation_character_url = fr'{base_api_url}/rules/translation-characters'
refinement_pattern_url = fr'{base_api_url}/rules/refinement-patterns'

data_dir= fr'/home/bitianist/Dropbox/bachelor_thesis/data'
text_equivalents_path = fr'{data_dir}/seq2seq/text_equivalents.xlsx'
word_equivalents_path = fr'{data_dir}/seq2seq/word_equivalents.xlsx'
bijankhan_data_dir = fr'{data_dir}/pos/bijankhan-online/unannotated'

bijankhan_tag_set_dictionary = [
  {
    "name": "E",
    "persian": "E",
    "color": "#E74C3C"
  },
  {
    "name": "N",
    "persian": "اسم",
    "color": "#3498DB"
  },
  {
    "name": "V",
    "persian": "فعل",
    "color": "#9B59B6"
  },
  {
    "name": "J",
    "persian": "J",
    "color": "#1ABC9C"
  },
  {
    "name": "A",
    "persian": "صفت",
    "color": "#F1C40F"
  },
  {
    "name": "U",
    "persian": "عدد",
    "color": "#E67E22"
  },
  {
    "name": "T",
    "persian": "T",
    "color": "#ECF0F1"
  },
  {
    "name": "Z",
    "persian": "ضمیر",
    "color": "#BDC3C7"
  },
  {
    "name": "O",
    "persian": "علامت",
    "color": "#7F8C8D"
  },
  {
    "name": "L",
    "persian": "L",
    "color": "#34495E"
  },
  {
    "name": "P",
    "persian": "حرف اضافه پسین",
    "color": "#C39BD3"
  },
  {
    "name": "D",
    "persian": "قید",
    "color": "#FBFCFC"
  },
  {
    "name": "C",
    "persian": "C",
    "color": "#0E6655"
  },
  {
    "name": "R",
    "persian": "R",
    "color": "#922B21"
  },
  {
    "name": "I",
    "persian": "حرف ندا",
    "color": "#AED6F1"
  }
]

def make_pretty_json_from_dictionary(dictionary):
    return json.dumps(dictionary, ensure_ascii=False, indent=4,)

def post(url, data_dictionary, log_it=False):
    data = json.dumps(data_dictionary)
    if log_it:
        logger.info(f'>> New request to {url} : {make_pretty_json_from_dictionary(data_dictionary)}')
    response = requests.post(url, data=data.encode('utf-8'), headers={'Content-type': 'application/json; charset=utf-8'})
    if response.status_code != 200 and response.status_code != 201:
        logger.info(f'> Error in request to \n{url}  \n\n{make_pretty_json_from_dictionary(data_dictionary)} \n\nError: \n\n{response.status_code} {response.text}\n\n')
        return response, True
    # if log_it:
    logger.info(f'> Success : {response.status_code} {response.text[:50]}...')
    return response, False


def generate_tag_dictionary(id=None, name=None, persian=None, color=None):
    d = {}
    if id:
        d['id'] = id
    if name:
        d['name'] = name
    if persian:
        d['persian'] = persian
    if color:
        d['color'] = color
    return d


def generate_tag_set_dictionary(name, id=None, tags=None, unknown_tag=None):
    d = {}
    d['name'] = name
    if id:
        d['id'] = id
    if tags:
        d['tags'] = tags
    if unknown_tag:
        d['unknown_tag'] = unknown_tag
    return d


def generate_token_dictionary(content, tag=None):
    d = {}
    d['content'] = content
    if tag:
        d['tag'] = tag    
    return d

def generate_normalizer_dictionary(name, model_type=None, 
                                owner=None, model_details=None, id=None):
    d = {}
    d['name'] = name
    if model_type:
        d['model_type'] = model_type
    if owner:
        d['owner'] = owner
    if model_details:
        d['model_details'] = model_details 
    if id:
        d['id'] = id 
    return d


def generate_sentence_dictionary(content, text=None, id=None):
    d = {}
    d['content'] = content
    if text:
        d['text'] = text 
    if id:
        d['id'] = id 
    return d

def generate_text_dictionary(content, id=None):
    d = {}
    d['content'] = content
    if id:
        d['id'] = id 
    return d

def generate_normal_text_dictionary(content, normalizer, 
        text, id=None):
    d = {}
    d['content'] = content
    d['normalizer'] = normalizer
    d['text'] = text
    if id:
        d['id'] = id 
    return d


def generate_tagger_dictionary(name, owner=None, model_type=None,
                             model_details=None, tag_set=None, id=None):
    d = {}
    d['name'] = name
    if model_type:
        d['model_type'] = model_type
    if owner:
        d['owner'] = owner
    if tag_set:
        d['tag_set'] = tag_set 
    if model_details:
        d['model_details'] = model_details 
    if id:
        d['id'] = id 
    return d


def generate_tagged_sentence_dictionary(tokens, tagger, 
        sentence, id=None):
    d = {}
    d['tokens'] = tokens
    d['tagger'] = tagger
    d['sentence'] = sentence
    if id:
        d['id'] = id 
    return d

def generate_translation_character_dictionary(source, destination, owner=None, 
                                                    is_valid=False, description=None,):
    d = {}
    d['source'] = source
    d['destination'] = destination
    d['is_valid'] = is_valid
    if description is not None:
        d['description'] = description   
    if owner is not None:
        d['owner'] = owner    
    return d

def generate_refinement_pattern_dictionary(pattern, replacement, order=9999, owner=None, 
                                                is_valid=False, description=None):
    d = {}
    d['pattern'] = pattern
    d['replacement'] = replacement
    d['order'] = order
    d['is_valid'] = is_valid
    if description is not None:
        d['description'] = description   
    if owner is not None:
        d['owner'] = owner    
    return d

@utils.time_usage(logger)
def import_bijankhan_tag_set():
    bijankhan_tag_set = generate_tag_set_dictionary('bijankhan-tag-set', 
        tags=bijankhan_tag_set_dictionary)

    response, error = post(tag_sets_url, bijankhan_tag_set)
    if error:
        return 0

@utils.time_usage(logger)
def import_taggers():
    model_details = {
        
    }

    bijankhan_tagger = generate_tagger_dictionary(
        'bijankhan-tagger',
        owner='bijankhan',
        tag_set='bijankhan-tag-set',
        model_type='manual',
        model_details=model_details
    )

    response, error = post(taggers_url, bijankhan_tagger)
    if error:
        return 0

    model_details = {
        'name': 'nltk',
        'state': 'not-trained'
    }

    nltk_tagger = generate_tagger_dictionary(
        'nltk-tagger',
        owner='bitianist',
        tag_set='bijankhan-tag-set',
        model_type='stochastic',
        model_details=model_details
    )

    response, error = post(taggers_url, nltk_tagger)
    if error:
        return 0

@utils.time_usage(logger)
def import_normalizers():
    # 1
    model_details = {
       
    }
    bitianist_normalizer = generate_normalizer_dictionary(
        'bitianist-normalizer',
        owner='bitianist',
        model_type='manual',
        model_details=model_details
    )
    response, error = post(normalizers_url, bitianist_normalizer)
    if error:
        return


    # 2
    model_details = {
        'state': 'not-trained'
    }
    refinement_normalizer = generate_tagger_dictionary(
        'refinement-normalizer',
        owner='bitianist',
        model_type='rule-based',
        model_details=model_details
    )
    response, error = post(normalizers_url, refinement_normalizer)
    if error:
        return


    # 3
    model_details = {
        'name': 'seq2seq',
        'state': 'not-trained'
    }
    seq2seq_normalizer = generate_tagger_dictionary(
        'seq2seq-normalizer',
        owner='bitianist',
        model_type='stochastic',
        model_details=model_details
    )
    response, error = post(normalizers_url, seq2seq_normalizer)
    if error:
        return


@utils.time_usage(logger)
def import_text_equivalents():
    df = pd.read_excel(text_equivalents_path, sheet_name='main')
    text_content, normal_text_content = '', ''
    text = None
    logger.info(f'>> Reading text_equivalents : {df.columns}')
    normalizer = 'bitianist-normalizer'
    # manual_normalizer = generate_normalizer_dictionary('manual-normalizer')
    i = 0
    for i in df.index:

        text_content = df['متن غیر رسمی'][i]
        if text_content.__str__() == 'nan' or text_content.__str__().isspace():
            break

        normal_text_content = df['متن رسمی'][i]
        if normal_text_content.__str__() == 'nan' or normal_text_content.__str__().isspace():
            break

        text = generate_text_dictionary(text_content)
        normal_text = generate_normal_text_dictionary(normal_text_content, normalizer, text)
        response, error = post(normal_texts_url, normal_text)
        if error:
            break
        if i % 25 == 0:
            logger.info(f'> Item {i} imported.')
    logger.info(f'> Items count : {i}')

@utils.time_usage(logger)
def import_word_equivalents():
    df = pd.read_excel(word_equivalents_path, sheet_name='main')
    text_content, normal_text_content = '', ''
    text = None
    logger.info(f'>> Reading word_equivalents : {df.columns}')
    ctr = 0
    normalizer = 'bitianist-normalizer'
    text_content_set = set()
    for i in df.index:

        text_content = df['کلمه غیر رسمی'][i].__str__().strip()
        if text_content in text_content_set:
            continue
        else:
            text_content_set.add(text_content)

        if text_content == 'nan' or text_content.isspace():
            break

        normal_text_content = df['کلمه رسمی'][i].__str__().strip()
        if normal_text_content == 'nan' or normal_text_content.isspace():
            break

        text = generate_text_dictionary(text_content)
        normal_text = generate_normal_text_dictionary(normal_text_content, normalizer, text)
        response, error = post(normal_texts_url, normal_text)
        if error:
            break
        ctr += 1
        if ctr % 25 == 0:
            logger.info(f'> Item {ctr} imported.')
    logger.info(f'> Items count : {ctr}')

# def import_bijankhan_xml_file(xml_file):
#     logger = utils.get_logger(logger_name='data-importer')
#     xml_string, token_content, tag_name, sentence_content, text_content = '', '', '', '', ''
#     tag, token, sentence, text = None, None, None, None
#     sentence_tokens, text_sentences = [], []
#     sentence_breaker_pattern = re.compile(r'[!\.\?⸮؟]')
#     try:
#         with open(xml_file, mode="r", encoding="utf-8") as xf:
#             file_name = os.path.basename(xml_file)
#             logger.info(f'> Importing xml file "{file_name}"')
#             xml_string = xf.read()
#             tree = ET.ElementTree(ET.fromstring(xml_string))
#             root = tree.getroot()
#             text_sentences = []
#             text_content = ''
#             for tagged_token_xml in root.findall('*'):
#                 token_content = tagged_token_xml.find('w').text
#                 sentence_content += token_content + ' '
#                 tag_name = tagged_token_xml.find('tag').text[0]
#                 tag = generate_tag_dictionary(tag_name)
#                 token = generate_token_dictionary(token_content, tag)
#                 sentence_tokens.append(token)
#                 if len(token_content) == 1 and sentence_breaker_pattern.search(token_content):
#                     sentence = generate_sentence_dictionary(sentence_content, sentence_tokens)
#                     text_sentences.append(sentence)
#                     text_content += sentence_content
#                     sentence_content = ''
#                     sentence_tokens = []
                
#             manual_tagger = generate_manual_tagger_dictionary(text_sentences)
#             text = generate_text_dictionary(text_content, manual_tagger)
#             response, error = post(text_url, text)
#             if error:
#                 return 0
#             logger.info(f'> File {file_name} finished. {len(text_sentences)} sentences added.')
#             return len(text_sentences)
#     except IOError as exc:
#         if exc.errno != errno.EISDIR:
#             logger.exception(exc)

# @utils.time_usage(logger)
def read_bijankhan_xml_file(xml_file):
    tagged_sentences = []
    logger = utils.get_logger(logger_name='data_importer')
    xml_string, token_content, tag_name, sentence_content = '', '', '', ''
    tag, token, sentence, tagged_sentence = None, None, None, None
    sentence_tokens = []
    sentence_breaker_pattern = re.compile(r'[!\.\?⸮؟]')
    # sentences_count = 0
    try:
        with open(xml_file, mode="r", encoding="utf-8") as xf:
            file_name = os.path.basename(xml_file)
            # logger.info(f'> Importing xml file "{file_name}"')
            xml_string = xf.read()
            tree = ET.ElementTree(ET.fromstring(xml_string))
            root = tree.getroot()
            for tagged_token_xml in root.findall('*'):
                token_content = tagged_token_xml.find('w').text.strip().replace(' ', '‌')
                sentence_content += token_content + ' '
                tag_name = tagged_token_xml.find('tag').text[0]
                tag = generate_tag_dictionary(name=tag_name)
                token = generate_token_dictionary(token_content, tag)
                sentence_tokens.append(token)
                if len(token_content) == 1 and sentence_breaker_pattern.search(token_content):
                    sentence = generate_sentence_dictionary(sentence_content)
                    tagged_sentence = generate_tagged_sentence_dictionary(
                                tokens=sentence_tokens,
                                tagger='bijankhan-tagger', 
                                sentence=sentence)
                    tagged_sentences.append(tagged_sentence)
                    # sentences_count += 1
                    sentence_content = ''
                    sentence_tokens = []
                    # if sentences_count % 25 == 0:
                        # logger.info(f'> File {file_name} now has {sentences_count} imported sentence ...')

            logger.info(f'> File {file_name} has {len(tagged_sentences)} sentences.')
            return tagged_sentences
    except IOError as exc:
        if exc.errno != errno.EISDIR:
            logger.exception(exc)

# @utils.time_usage(logger)
def send_bijankhan_tagged_sentence(tagged_sentence):
    response, error = post(tagged_sentences_url, tagged_sentence)
    if error:
        return

@utils.time_usage(logger)
def import_bijankhan_data():
    # global tagged_sentences, tagged_tokens, token_set, word_set, tag_example_dic
    logger.info(f'>> Reading bijankhan data')
    files = glob.glob(fr'{bijankhan_data_dir}/*.xml')
    tagged_sentences, tagged_sentences_list = [], []
    # files = files[0:1]
    # num_cores = multiprocessing.cpu_count()
    # logger.info(f'> Number of cup cores : {num_cores}')
    # tagged_sentences.extend(
    tagged_sentences_list = Parallel(n_jobs=-1, verbose=20)(delayed(read_bijankhan_xml_file)(xml_file) for xml_file in files)
    # )
    for current_tagged_sentences in tagged_sentences_list:
        tagged_sentences.extend(current_tagged_sentences)
    logger.info(f'>> Total {len(tagged_sentences)} sentences added.')
    
    Parallel(n_jobs=24, verbose=20, backend='threading')(delayed(send_bijankhan_tagged_sentence)(tagged_sentence) for tagged_sentence in tagged_sentences)
    
    logger.info(f'>> {len(tagged_sentences)} sentences imported.')


def import_tags():
    """ 
    https://htmlcolorcodes.com/
    """
    tags = (
        ('E', 'E', '#E74C3C'),
        ('N', 'اسم', '#3498DB'),
        ('V', 'فعل', '#9B59B6'),

        ('J', 'J', '#1ABC9C'),
        ('A', 'صفت', '#F1C40F'),
        ('U', 'عدد', '#E67E22'),
        
        ('T', 'T', '#ECF0F1'),
        ('Z', 'ضمیر', '#BDC3C7'),
        ('O', 'علامت', '#7F8C8D'),
        
        ('L', 'L', '#34495E'),
        ('P', 'حرف اضافه پسین', '#C39BD3'),
        ('D', 'قید', '#FBFCFC'),
        
        ('C', 'C', '#0E6655'),
        ('R', 'R', '#922B21'),
        ('I', 'حرف ندا', '#AED6F1'),

    )
    for tag_data in tags:
        tag = generate_tag_dictionary(tag_data[0])
        response, error = post(tag_url, tag)
        if error:
            continue

def import_translation_characters():
    translation_characters = (
        # (r' ', r' ', 'space character 160 -> 32', 'hazm', 'true'),
        # (r'ك', r'ک', '', 'hazm', 'true'),
        # (r'ي', r'ی', '', 'hazm', 'true'),
        # (r'“', r'\"', '', 'hazm', 'true'),
        # (r'”', r'\"', '', 'hazm', 'true'),
        # (r'0', r'۰', '', 'hazm', 'true'),
        # (r'1', r'۱', '', 'hazm', 'true'),
        # (r'2', r'۲', '', 'hazm', 'true'),
        # (r'3', r'۳', '', 'hazm', 'true'),
        # (r'4', r'۴', '', 'hazm', 'true'),
        # (r'5', r'۵', '', 'hazm', 'true'),
        # (r'6', r'۶', '', 'hazm', 'true'),
        # (r'7', r'۷', '', 'hazm', 'true'),
        # (r'8', r'۸', '', 'hazm', 'true'),
        # (r'9', r'۹', '', 'hazm', 'true'),
        # (r'%', r'٪', '', 'hazm', 'true'),
        (r'?', r'؟', '', 'hazm', 'true'),
    )
    url = 'http://127.0.0.1:8000/mohaverekhan/api/rules/translation_character/'
    for translation_character in translation_characters:
        data = f'''
{{
    "source": "{translation_character[0]}",
    "destination": "{translation_character[1]}",
    "description": "{translation_character[2]}",
    "owner": "{translation_character[3]}",
    "is_valid": {translation_character[4]}
}}'''
        response, error = post(url, data)
        if error:
            continue
        # response = requests.post(url, data=data.encode('utf-8'), headers={'Content-type': 'application/json; charset=utf-8'})
        # if response.status_code != 200 and response.status_code != 201:
        #     logger.info(f'> Error : {response.status_code} {response.text}')
        #     response.raise_for_status()
        #     break
        # logger.info(f'{response.status_code} : {response.text}')

def import_refinement_patterns():
    punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
    refinement_patterns = (
        (r'\.{4,}', r'.', 'replace more than 3 dots with 1 dot', 0, 'bitianist', 'true'),
        (r'( \.{2})|(\.{2} )', r' . ', 'replace exactly 2 dots with 1 dot', 0, 'bitianist', 'true'),
        (r' ?\.\.\.', r' …', 'replace 3 dots', 0, 'hazm', 'true'),
        (r'(.)\1{1,}', r'\1', 'remove repetitions', 0, 'bitianist', 'true'),
        (r'[ـ\r]', r'', 'remove keshide', 0, 'hazm', 'true'),
        (r'[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652]', r'', 'remove FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN', 0, 'hazm', 'true'),
        (r'"([^\n"]+)"', r'«\1»', 'replace quotation with gyoome', 0, 'hazm', 'true'),
        (rf'([{punctuations}])', r' \1 ', 'add extra space before and after of punctuations', 0, 'bitianist', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
        (r'\n+', r'\n', 'remove extra newlines', 0, 'bitianist', 'true'),
        (r'([^ ]ه) ی ', r'\1‌ی ', 'before ی - replace space with non-joiner ', 0, 'hazm', 'true'),
        (r'(^| )(ن?می) ', r'\1\2‌', 'after می،نمی - replace space with non-joiner ', 0, 'hazm', 'true'),
        (rf'(?<=[^\n\d {punctuations}]{2}) (تر(ین?)?|گری?|های?)(?=[ \n{punctuations}]|$)', r'‌\1', 'before تر, تری, ترین, گر, گری, ها, های - replace space with non-joiner', 0, 'hazm', 'true'),
        (rf'([^ ]ه) (ا(م|یم|ش|ند|ی|ید|ت))(?=[ \n{punctuations}]|$)', r'\1‌\2', 'before ام, ایم, اش, اند, ای, اید, ات - replace space with non-joiner', 0, 'hazm', 'true'),  
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
    )
    for refinement_pattern_data in refinement_patterns:
        refinement_pattern = generate_refinement_pattern_dictionary(
            pattern=refinement_pattern_data[0],
            replacement=refinement_pattern_data[1],
            description=refinement_pattern_data[2],
            order=refinement_pattern_data[3],
            owner=refinement_pattern_data[4],
            is_valid=refinement_pattern_data[5]
        )
     
        response, error = post(refinement_pattern_url, refinement_pattern)
        if error:
            return


def main():
    try:
        # import_bijankhan_tag_set()
        # import_normalizers()
        # import_taggers()
        # import_text_equivalents()
        # import_word_equivalents()
        import_bijankhan_data()


        # import_tags()
        # import_translation_characters()
        # import_refinement_patterns()
    except Exception as e:
        logger.exception(e)

if __name__ == "__main__": main()
