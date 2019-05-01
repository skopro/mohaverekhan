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
       from mohaverekhan import utils

logger = utils.get_logger(logger_name='data_importer')

base_api_url = r'http://127.0.0.1:8000/mohaverekhan/api'

words_url = fr'{base_api_url}/words'
word_normals_url = fr'{base_api_url}/word-normals'

texts_url = fr'{base_api_url}/texts'
text_normals_url = fr'{base_api_url}/text-normals'
text_tags_url = fr'{base_api_url}/text-tags'

tag_sets_url = fr'{base_api_url}/tag-sets'
tags_url = fr'{base_api_url}/tags'

tokens_url = fr'{base_api_url}/tokens'
token_tags_url = fr'{base_api_url}/token-tags'

validators_url = fr'{base_api_url}/validators'
normalizers_url = fr'{base_api_url}/normalizers'
taggers_url = fr'{base_api_url}/taggers'
# sentences_url = fr'{base_api_url}/sentences'
# normal_sentences_url = fr'{base_api_url}/normal-sentences'
# tagged_sentences_url = fr'{base_api_url}/tagged-sentences'

# translation_character_url = fr'{base_api_url}/rules/translation-characters'
# correction_pattern_url = fr'{base_api_url}/rules/correction-patterns'

data_dir= fr'/home/bitianist/Dropbox/bachelor_thesis/data'
text_equivalents_path = fr'{data_dir}/seq2seq/text_equivalents.xlsx'
word_equivalents_path = fr'{data_dir}/seq2seq/word_equivalents.xlsx'
bijankhan_data_dir = fr'{data_dir}/pos/bijankhan-online/unannotated'

bijankhan_tag_set_dictionary = [
  {
    "name": "E",
    "persian": "حرف اضافه",
    "color": "#BCFF05"
  },
  {
    "name": "N",
    "persian": "اسم",
    "color": "#FBFCFC"
  },
  {
    "name": "V",
    "persian": "فعل",
    "color": "#33B4FF"
  },
  {
    "name": "J",
    "persian": "حرف ربط",
    "color": "#1ABC9C"
  },
  {
    "name": "A",
    "persian": "صفت",
    "color": "#FFF82E"
  },
  {
    "name": "U",
    "persian": "عدد",
    "color": "#C7FFFB"
  },
  {
    "name": "T",
    "persian": "قید مقدار",
    "color": "#BCCEF1"
  },
  {
    "name": "Z",
    "persian": "ضمیر",
    "color": "#FF82FF"
  },
  {
    "name": "O",
    "persian": "علامت",
    "color": "#FFA14F"
  },
  {
    "name": "L",
    "persian": "واحد",
    "color": "#FF1F96"
  },
  {
    "name": "P",
    "persian": "حرف اضافه پسین",
    "color": "#16DB00"
  },
  {
    "name": "D",
    "persian": "قید",
    "color": "#FF5442"
  },
  {
    "name": "C",
    "persian": "متصل‌شونده",
    "color": "#20EBC4"
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

mohaverekhan_tag_set_dictionary = bijankhan_tag_set_dictionary + [
  {
    "name": "X",
    "persian": "ایموجی",
    "color": "#00B3FF"
  },
  {
    "name": "S",
    "persian": "شناسه",
    "color": "#00B3FF"
  },
  {
    "name": "K",
    "persian": "لینک",
    "color": "#00B3FF"
  },
  {
    "name": "M",
    "persian": "ایمیل",
    "color": "#00B3FF"
  },
  {
    "name": "G",
    "persian": "تگ",
    "color": "#00B3FF"
  },
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

def put(url, data_dictionary, log_it=False):
    data = json.dumps(data_dictionary)
    if log_it:
        logger.info(f'>> New request to {url} : {make_pretty_json_from_dictionary(data_dictionary)}')
    response = requests.put(url, data=data.encode('utf-8'), headers={'Content-type': 'application/json; charset=utf-8'})
    if response.status_code != 200 and response.status_code != 201:
        logger.info(f'> Error in request to \n{url}  \n\n{make_pretty_json_from_dictionary(data_dictionary)} \n\nError: \n\n{response.status_code} {response.text}\n\n')
        return response, True
    # if log_it:
    logger.info(f'> Success : {response.status_code} {response.text[:50]}...')
    return response, False



def generate_normalizer_dictionary(name, show_name, is_automatic=False, 
                                owner=None, model_details=None, id=None):
    d = {}
    d['name'] = name
    d['show_name'] = show_name
    d['is_automatic'] = is_automatic
    if owner:
        d['owner'] = owner
    if model_details:
        d['model_details'] = model_details 
    if id:
        d['id'] = id 
    return d


def generate_tagger_dictionary(name, show_name, is_automatic=False, owner=None,
                             model_details=None, tag_set=None, id=None):
    d = {}
    d['name'] = name
    d['show_name'] = show_name
    d['is_automatic'] = is_automatic
    if owner:
        d['owner'] = owner
    if tag_set:
        d['tag_set'] = tag_set 
    if model_details:
        d['model_details'] = model_details 
    if id:
        d['id'] = id 
    return d



def generate_validator_dictionary(name, show_name, owner=None, id=None):
    d = {}
    d['name'] = name
    d['show_name'] = show_name
    if owner:
        d['owner'] = owner
    if id:
        d['id'] = id 
    return d




def generate_tag_set_dictionary(name, id=None, tags=None):
    d = {}
    d['name'] = name
    if id:
        d['id'] = id
    if tags:
        d['tags'] = tags
    return d



def generate_tag_dictionary(id=None, name=None, persian=None, color=None, tag_set=None):
    d = {}
    if id:
        d['id'] = id
    if name:
        d['name'] = name
    if persian:
        d['persian'] = persian
    if color:
        d['color'] = color
    if tag_set:
        d['tag_set'] = tag_set
    return d






def generate_text_dictionary(content, id=None):
    d = {}
    d['content'] = content
    if id:
        d['id'] = id 
    return d

def generate_text_normal_dictionary(content, normalizer, 
        text, id=None):
    d = {}
    d['content'] = content
    d['normalizer'] = normalizer
    d['text'] = text
    if id:
        d['id'] = id 
    return d

def generate_text_tag_dictionary(tagged_tokens, tagger, 
        text, id=None):
    d = {}
    d['tagged_tokens'] = tagged_tokens
    d['tagger'] = tagger
    d['text'] = text
    if id:
        d['id'] = id 
    return d





def generate_word_dictionary(content, id=None):
    d = {}
    d['content'] = content
    if id:
        d['id'] = id 
    return d

def generate_word_normal_dictionary(content, normalizer, 
        word, id=None):
    d = {}
    d['content'] = content
    d['normalizer'] = normalizer
    d['word'] = word
    if id:
        d['id'] = id 
    return d



def generate_tagged_token_dictionary(token, tag=None):
    d = {}
    d['token'] = token
    if tag:
        d['tag'] = tag    
    return d


@utils.time_usage(logger)
def import_tag_sets():
    # 0
    bijankhan_tag_set = generate_tag_set_dictionary('bijankhan-tag-set', 
        tags=bijankhan_tag_set_dictionary)

    response, error = post(tag_sets_url, bijankhan_tag_set)
    if error:
        return 0

    # 1
    mohaverekhan_tag_set = generate_tag_set_dictionary('mohaverekhan-tag-set', 
        tags=mohaverekhan_tag_set_dictionary)

    response, error = post(tag_sets_url, mohaverekhan_tag_set)
    if error:
        return 0

@utils.time_usage(logger)
def import_validators():
    mohaverekhan_validator = generate_validator_dictionary(
        'mohaverekhan-validator',
        show_name='اعتبارسنج محاوره‌خوان',
        owner='mohaverekhan'
    )

    response, error = post(validators_url, mohaverekhan_validator)
    if error:
        return 0

@utils.time_usage(logger)
def import_normalizers():
    # # 1
    # model_details = {
    #    'type': 'manual'
    # }
    # mohaverekhan_manual_normalizer = generate_normalizer_dictionary(
    #     'mohaverekhan-manual-normalizer',
    #     show_name='نرمال‌کننده دستی محاوره‌خوان',
    #     owner='mohaverekhan',
    #     is_automatic=False,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, mohaverekhan_manual_normalizer)
    # if error:
    #     return


    # # 2
    # model_details = {
    #     'type': 'rule-based',
    #     'state': 'ready'
    # }
    # mohaverekhan_correction_normalizer = generate_tagger_dictionary(
    #     'mohaverekhan-correction-normalizer',
    #     show_name='نرمال‌کننده پالایش',
    #     owner='mohaverekhan',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, mohaverekhan_correction_normalizer)
    # if error:
    #     return


    # # 3
    # model_details = {
    #     'type': 'stochastic',
    #     'module': 'seq2seq',
    #     'state': 'not-ready'
    # }
    # mohaverekhan_seq2seq_normalizer = generate_tagger_dictionary(
    #     'mohaverekhan-seq2seq-normalizer',
    #     show_name='نرمال‌کننده توالی‌به‌توالی',
    #     owner='mohaverekhan',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, mohaverekhan_seq2seq_normalizer)
    # if error:
    #     return

    # # 4
    # model_details = {
    #     'type': 'rule-based',
    #     'state': 'ready'
    # }
    # mohaverekhan_replacement_normalizer = generate_tagger_dictionary(
    #     'mohaverekhan-replacement-normalizer',
    #     show_name='نرمال‌کننده جایگزینی',
    #     owner='mohaverekhan',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, mohaverekhan_replacement_normalizer)
    # if error:
    #     return

    # 5
    model_details = {
        'type': 'rule-based',
        'state': 'ready'
    }
    mohaverekhan_basic_normalizer = generate_tagger_dictionary(
        'mohaverekhan-basic-normalizer',
        show_name='نرمال‌کننده بنیادی',
        owner='mohaverekhan',
        is_automatic=True,
        model_details=model_details
    )
    response, error = post(normalizers_url, mohaverekhan_basic_normalizer)
    if error:
        return
    

@utils.time_usage(logger)
def import_taggers():
    # # 0
    # model_details = {
    #    'type': 'manual'
    # }

    # bijankhan_manual_tagger = generate_tagger_dictionary(
    #     'bijankhan-manual-tagger',
    #     show_name='برچسب‌زن دستی بی‌جن‌خان',
    #     owner='bijankhan',
    #     tag_set='bijankhan-tag-set',
    #     is_automatic=False,
    #     model_details=model_details
    # )

    # response, error = post(taggers_url, bijankhan_manual_tagger)
    # if error:
    #     return 0



    # # 2
    # model_details = {
    #    'type': 'manual',
    #    'description': "For new words"
    # }

    # mohaverekhan_manual_tagger = generate_tagger_dictionary(
    #     'mohaverekhan-manual-tagger',
    #     show_name='برچسب‌زن دستی محاوره‌خوان',
    #     owner='mohaverekhan',
    #     tag_set='mohaverekhan-tag-set',
    #     is_automatic=False,
    #     model_details=model_details
    # )

    # response, error = post(taggers_url, mohaverekhan_manual_tagger)
    # if error:
    #     return 0

    # # 3
    # model_details = {
    #     'module': 'nltk',
    #     'type': 'hybrid',
    #     'state': 'not-ready',
    # }

    # mohaverekhan_correction_tagger = generate_tagger_dictionary(
    #     'mohaverekhan-correction-tagger',
    #     show_name='برچسب‌زن پالایش',
    #     owner='mohaverekhan',
    #     tag_set='mohaverekhan-tag-set',
    #     is_automatic=True,
    #     model_details=model_details
    # )

    # response, error = post(taggers_url, mohaverekhan_correction_tagger)
    # if error:
    #     return 0

    
    # 4
    model_details = {
        'module': 'nltk',
        'type': 'hybrid',
        'state': 'not-ready',
    }

    mohaverekhan_seq2seq_tagger = generate_tagger_dictionary(
        'mohaverekhan-seq2seq-tagger',
        show_name='برچسب‌زن توالی‌به‌توالی',
        owner='mohaverekhan',
        tag_set='mohaverekhan-tag-set',
        is_automatic=True,
        model_details=model_details
    )

    response, error = post(taggers_url, mohaverekhan_seq2seq_tagger)
    if error:
        return 0



@utils.time_usage(logger)
def import_text_equivalents():
    df = pd.read_excel(text_equivalents_path, sheet_name='main')
    text_content, text_normal_content = '', ''
    text = None
    logger.info(f'>> Reading text_equivalents : {df.columns}')
    normalizer = 'mohaverekhan-manual-normalizer'
    # manual_normalizer = generate_normalizer_dictionary('manual-normalizer')
    i = 0
    for i in df.index:
        if i < 1101:
            continue
        text_content = df['متن غیر رسمی'][i]
        if text_content.__str__() == 'nan' or text_content.__str__().isspace():
            break

        text_normal_content = df['متن رسمی'][i]
        if text_normal_content.__str__() == 'nan' or text_normal_content.__str__().isspace():
            break

        text = generate_text_dictionary(text_content)
        text_normal = generate_text_normal_dictionary(text_normal_content, normalizer, text)
        response, error = post(text_normals_url, text_normal)
        if error:
            break
        if i % 25 == 0:
            logger.info(f'> Item {i} imported.')
    logger.info(f'> Items count : {i - 1}')

@utils.time_usage(logger)
def import_word_equivalents():
    df = pd.read_excel(word_equivalents_path, sheet_name='main')
    word_content, word_normal_content = '', ''
    word = None
    logger.info(f'>> Reading word_equivalents : {df.columns}')
    ctr = 1
    normalizer = 'mohaverekhan-manual-normalizer'
    word_content_set = set()
    for i in df.index:
        if i < 5066:
            continue
        word_content = df['کلمه غیر رسمی'][i].__str__().strip()
        if word_content in word_content_set:
            continue
        else:
            word_content_set.add(word_content)

        if word_content == 'nan' or word_content.isspace():
            break

        word_normal_content = df['کلمه رسمی'][i].__str__().strip()
        if word_normal_content == 'nan' or word_normal_content.isspace():
            break

        word = generate_word_dictionary(word_content)
        word_normal = generate_word_normal_dictionary(word_normal_content, normalizer, word)
        response, error = post(word_normals_url, word_normal)
        if error:
            break
        ctr += 1
        if ctr % 25 == 0:
            logger.info(f'> Item {ctr} imported.')
    logger.info(f'> Items count : {ctr - 1 }')


# @utils.time_usage(logger)
def read_bijankhan_xml_file(xml_file):
    text_tag = None
    logger = utils.get_logger(logger_name='data_importer')
    token_content, tag_name, text_content = '', '', ''
    tag, tagged_token = None, None
    text_tag_tagged_tokens = []
    # texts_count = 0
    try:
        with open(xml_file, mode="r", encoding="utf-8") as xf:
            file_name = os.path.basename(xml_file)
            # logger.info(f'> Importing xml file "{file_name}"')
            xml_string = xf.read()
            tree = ET.ElementTree(ET.fromstring(xml_string))
            root = tree.getroot()
            for tagged_token_xml in root.findall('*'):
                token_content = tagged_token_xml.find('w').text.strip().replace(' ', '‌')
                text_content += token_content + ' '
                tag_name = tagged_token_xml.find('tag').text[0]
                tag = generate_tag_dictionary(name=tag_name)
                tagged_token = generate_tagged_token_dictionary(token_content, tag)
                text_tag_tagged_tokens.append(tagged_token)

            text = generate_text_dictionary(text_content)
            text_tag = generate_text_tag_dictionary(
                        tagged_tokens=text_tag_tagged_tokens,
                        tagger='bijankhan-manual-tagger', 
                        text=text)

            logger.info(f'> File {file_name} reading finished.')
            return text_tag
    except IOError as exc:
        if exc.errno != errno.EISDIR:
            logger.exception(exc)

# @utils.time_usage(logger)
def send_bijankhan_text_tag(text_tag):
    response, error = post(text_tags_url, text_tag)
    if error:
        return

@utils.time_usage(logger)
def import_bijankhan_data():
    logger.info(f'>> Reading bijankhan data')
    files = glob.glob(fr'{bijankhan_data_dir}/*.xml')
    # text_tags = []
    # files = files[0:2]

    text_tags = Parallel(n_jobs=-1, verbose=20)(delayed(read_bijankhan_xml_file)(xml_file) for xml_file in files)
    logger.info(f'>> Total {len(text_tags)} texts read.')
    
    Parallel(n_jobs=24, verbose=20, backend='threading')(delayed(send_bijankhan_text_tag)(text_tag) for text_tag in text_tags)
    logger.info(f'>> Total {len(text_tags)} texts imported.')

def import_mohaverekhan_text_tag(text_tag_id=None):
    tagger = 'mohaverekhan-manual-tagger'

    # 1
    text_content = 'شلوغی فرهنگ‌سرا آیدی انقدر اوورد اووردن منو میدون خونه جوون زمونه نون مسلمون کتابخونه دندون'
    text_content += ' نشون پاستا پنه تاچ تنظیمات می‌تونید سی‌پی‌یو‌ سی‌پی‌یو‌‌ها گرافیک اومدن می‌خان واس ٪ ال‌سی‌دی ال‌سی‌دی‌ها سوپریم'

    tagged_tokens = [
        generate_tagged_token_dictionary('شلوغی', generate_tag_dictionary(name='A')),
        generate_tagged_token_dictionary('فرهنگ‌سرا', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('آیدی', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('انقدر', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('اوورد', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('اووردن', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('منو', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('میدون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('خونه', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('جوون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('زمونه', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('نون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('مسلمون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('کتابخونه', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('دندون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('نشون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('پاستا', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('پنه', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('تاچ', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('تنظیمات', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('می‌تونید', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('سی‌پی‌یو‌', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('سی‌پی‌یو‌‌ها', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('گرافیک', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('اومدن', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌خان', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('واس', generate_tag_dictionary(name='E')),
        generate_tagged_token_dictionary('٪', generate_tag_dictionary(name='O')),
        generate_tagged_token_dictionary('ال‌سی‌دی', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ال‌سی‌دی‌ها', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('سوپریم', generate_tag_dictionary(name='N')),

    ]

    text_content += ' kb m kg g cm mm'
    tagged_tokens += [
        generate_tagged_token_dictionary('kb', generate_tag_dictionary(name='L')),
        generate_tagged_token_dictionary('m', generate_tag_dictionary(name='L')),
        generate_tagged_token_dictionary('kg', generate_tag_dictionary(name='L')),
        generate_tagged_token_dictionary('g', generate_tag_dictionary(name='L')),
        generate_tagged_token_dictionary('cm', generate_tag_dictionary(name='L')),
        generate_tagged_token_dictionary('mm', generate_tag_dictionary(name='L')),

    ]


    text_content += ' کلیدها درایو درایوها درایور درایورها می‌تون بازه کننده سیستم‌عامل مولتی‌تاچ ان‌ویدیا تاچ‌پد مث'
    tagged_tokens += [
        generate_tagged_token_dictionary('کلیدها', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('درایو', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('درایوها', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('درایور', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('درایورها', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('می‌تون', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('بازه', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('کننده', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('سیستم‌عامل', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('مولتی‌تاچ', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ان‌ویدیا', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('تاچ‌پد', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('مث', generate_tag_dictionary(name='D')),
    ]

    text_content += ' اصلن عمرا عمرن واقعن ش میشی وارد میشی کتاب ه فیلم ه عکس ه رستوران ه'
    tagged_tokens += [
        generate_tagged_token_dictionary('اصلن', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('عمرا', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('عمرن', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('واقعن', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('ش', generate_tag_dictionary(name='C')),
        generate_tagged_token_dictionary('میشی', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('وارد', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('میشی', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('کتاب', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='C')),
        generate_tagged_token_dictionary('فیلم', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='C')),
        generate_tagged_token_dictionary('عکس', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='C')),
        generate_tagged_token_dictionary('رستوران', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='C')),
    ]

    text_content += ' شیشلیک حتمنی خوبن عالین ایسوس ببند نبند تونست می‌زنه بزنه می‌میره می‌تونه می‌زنن نمی‌زنن می‌ارزه نمی‌ارزه سامسونگ'
    tagged_tokens += [
        generate_tagged_token_dictionary('شیشلیک', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('حتمنی', generate_tag_dictionary(name='D')),
        generate_tagged_token_dictionary('خوبن', generate_tag_dictionary(name='A')),
        generate_tagged_token_dictionary('عالین', generate_tag_dictionary(name='A')),
        generate_tagged_token_dictionary('ایسوس', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('ببند', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('نبند', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('تونست', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌زنه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('بزنه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌میره', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌تونه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌زنن', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('نمی‌زنن', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('می‌ارزه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('نمی‌ارزه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('سامسونگ', generate_tag_dictionary(name='N')),
    ]

    text_content += ' بمونه نمونه قلیون نخواستن'
    tagged_tokens += [
        generate_tagged_token_dictionary('بمونه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('نمونه', generate_tag_dictionary(name='V')),
        generate_tagged_token_dictionary('قلیون', generate_tag_dictionary(name='N')),
        generate_tagged_token_dictionary('نخواستن', generate_tag_dictionary(name='V')),
    ]


    logger.info(f'> text_content : \n{text_content}\n')
    logger.info(f'> tagged_tokens : \n{tagged_tokens}\n')
    text = generate_text_dictionary(text_content)
    text_tag = generate_text_tag_dictionary(
                tagged_tokens=tagged_tokens,
                tagger=tagger,
                text=text)

    response, error = None, None
    if text_tag_id:
        response, error = put(f'{text_tags_url}/{text_tag_id}', text_tag, True)
    else:
        response, error = post(text_tags_url, text_tag)
        logger.info(response)
    if error:
        return

def import_mohaverekhan_evaluate_text_tag(text_tag_id=None):
    tagger = 'mohaverekhan-manual-tagger'

    text_content = '''
حدود يک هفته است که به دستم رسيده. لپتاپ فوق العاده ايه. کيفيت ساخت خيلي خوبه و از جنس پلاستيک با کيفيته . ال سي دي خيلي عاليه اصلا فکر نميکردم تو اين بازه قيمتي با چنين ال سي دي اي رو به رو بشم. يکي از مزاياي ديگه اين لپ تاپ وجود دو گرافيکي يکي گرافيک اينتل و يکي هم گرافيک ان ويديا که در زمان انجام کارهاي گرافيکي سنگين خودکار به گرافيک ان ويديا سوييچ ميشه که اين مورد تاثير زيادي روي زمان شارژ دهي اين لپتاپ داره. کيفيت صداي خروجي هم مناسب و راضي کنندست. در ضمن چيزي که تو مشخصات ذکر نشده اينه که تاچ پد ايناز نوع مولتي تاچه که به راحتي کار در سيستم عامل ويندوز 8 کمک ميکنه. همراه دستگاه سيستم عاملي وجود نداره اما درايور هاي موجود مخصوص ويندوز 8 هست. کيفيت کيبورد و نرمي کليد ها هم خيلي خوبه. فکر نميکردم لپتاپ ها سامسونگ تا اين حد با کيفيت باشه. تو اين بازه قيمتي فقط اين لپتاپ و بخريد چون واقعا ارزش خريد داره
بریـــــــد به رستورانhttps://chilivery.com/tehran/restaurant1/ .... غذاش خیییلی عااااالیه😍😍😍
از نظر قیمت میارزه ك برئ ولی واقعا خفست
مث این، جای دیگه ای ندیدم مشتریاش انقدر زیاد باشه.
کیفیت پیتزاهاش اصلن خوب نیست... از شلوغیه میدون تجریش داره پول درمیاره.
بازم ازش خرید میکنم، بهتریییییییییییییییییین منطقست.
اگه یبار بری اونجا مشتریش میشی.
برای ارسال رزومه به آدرس job@gmail.com میل بزنید.
کتابه رو تو فرهنگ سرا پیداش کردم. کتاباشونم واقعن عالیه
در صورت مشکل به آیدی @bitianist پیام بدهید.
حاضرم شرط ببندم همونو ورداشتن تزئین کردن و برای ما اووردن!!!!
آخه واقعا درسته اینکار؟؟؟ چرا خب درست نمیکنن؟؟
محیطی دلباز و شادی داره دوتا سالن بزرگ هم داره شیشلیک و ماهیچه و گوشتش هم خیلی خوبه من غذاهای دیگشو تا حالا تست نکردم
همه چی عالیغذا عالی بود و برخورد پرسنل فوق العاده مودبانه بوددستشویی خوبعالی و توالت فوق العاده تمیز و عالیپذیرایی عالیخلاصه مدیریت عالی فقط امیدوارم خراب نشه چون واقعاً حیفه
نمره برخورد با مشتری تقریبا صفر مناسبشونه، غذا هم خیلی خیلی شور بود، سیب زمینیش خوب بود، و من به اون رنگ نون برگراشون خیلی خوش بین نیستم. تمام!
تازه افتتاح شدهمحیط شیک با فضای باز خیلی زیباکیفیت غذاش که خیلی عالی بودبا بهترین رستوران های تهران برابری میکنهبرخورد پرسنل هم خیلی گرم و صمیمی بوداگه به همین روال پیش برن و کیفیت غذاشونم همینطور بمونه خیلی عالیه
برخورد پرسنل عالی...کیفیت غذا عالی...قیمت خوب...حتمنی سر بزنید
2 تا قلیون با 6 تا چایی لیوانی، 130 هزار تومن!!قلیون بدون سرویس !هیچ چیز خاصی هم نداره فقط سالن داخلی اش یه کم خوشگل تزیین شده.
ما رفتیم ملورین و به نظرم چیزبرگر و همبرگر سوپریمشون فوق العاده بووووووود طعم گوشت عالی بود نون خوش طعم و یه سس تار تار خوش مزه بعد از مدت ها همبرگری خوردم که دوست داشتم 😍😍البته به نظرم منوی کافه هم خوب بوود مخصوصا کاپوچینو و کیک موکا ممنووووووووووون🙏🏻🙏🏻
غذا، فضا، برخورد با مشتری همه چی عالی، ما عاشق سالادای سزارشیم با پیتزا و ...ضمناً شبها خیلی شلوغ میشه
متاسفانه لیست قیمت با اینکه تا تیر 92 به روز شده با قیمت واقعی تفاوت فاحش داشت. سرویس 15 % با 6 % ارزش افزوده بود .(21 %) . قیمت ها و منو خیلی فرق داشتن. رستوران خوبیه به همه دوستان توصیه میکنم.
چرا جدیدا اخر همه فیلما بی نتیجه تموم میشه الان تهش چی شد
خیلی قشنگه مشکلات نسل جدید و عشق و عاشقیهارو خوب نشون داده که با یه نخواستن همه چی تموم میشه
ما در تاریخ 97/6/5 در قالب جمع دوستانه و همکاران قدیمی برای شام به این رستوران رفتیم .انصافا همه چی عالی بود .کیفیت غذاها خوب بود و از همه مهمتر صبر و حوصله کارکنان بود . چون ما عده مون زیاد بود و میخواستیم که صورتحسابها جدا باشه که همینطور هم شد . حجم غداها به نسبت قیمت خیلی خوبه . برای مثال پاستا پنه یک غذای دونفره هست .سالاد ها رو هم امتحان کنید عالین .
با سلام اطلاعات مربوط به cache اشتباه وارد شده است. 3m نمي باشد و 1024kb است. موفق باشيد
به نظر من از نظر بدنه شکي در اين مدل نيست چون جنسش از کربن يا همون فولاد که در اينجا از نوع سبک آن استفاده شده البته سري k ايسوس از آلومينيوم استفاده شده که خيلي زيباست و در عين حال که کم استقامت دارد. از نظر سخت افزاري عين k هست به جز صفحه نمايش بزرگتر و استحکام بالا در اين مدل. و زيبايي و باتري قويتر در مدل k .
دوستان تو نقد نوشته شده بود که قابليت زوم دو انگشتي و... نداره تاچش در حالي که اگه به قسمت تنظيمات ماوس بريد ميتونيد تمامي امکانات تاچش رو فعال کنيد.
اين دستگاه جزء اولين و شايد تنها سريه که تا الان از نسل چهارم سي پي يوهاي اينتل استفاده ميکنه 
من اين لپ تاپ رو دارم از نظر سخت افزار حرف نداره و براي وب گردي و کار هاي اداري و بازي هاي متوسط مناسب هست هنگام بازي کردن با بازي هاي سنگين هيچ کاهش سرعتي ديده نمي شه ولي سي پي يو بشدت داغ ميشه اين لپ تاب براي اون هايي که سخت افزار عالي همراه با صفحه نمايش بزرگ و کار هاي روزمره با قيمت مناسب ميخان توصيه ميکنم حتما اين لپ تاپو بخرين
با توجه به اين مشخصات بهتر بود از باطري بهتري استفاده ميشد
يک سالي هست که اين لپ تاپ رو خريدم در کل ازش راضي ام، ملاک اصليم واسه انتخابش وزنش بود. البته مشخصات خوبي هم نسبت به قيمتش تو مدل هاي هم رده خودش داشت
از هر نظر لپ تاپ بي نظيريه من بعد از مدت ها تحقيق خريدمش سرعتش عاليه بدنه هم اصلا زياد گرم نميشه در کل واقعا ارزش خريد داره
سلام به همگي مشکلات: - من روش ويندوز سون نصب کردم، رفتم 1.6 گيگ درايور سون دان کردم ولي کارت گرافيکيشو نشناخت ولي ويندوز 8 ريختم مشکلي نداشت.(البته شايد مشکل از کامل نبودن درايور ها باشه) - صفحه نمايش انقدر هم که گفته ميشه بد نيست ولي بايد قيد کار کردن با لپ تاپ زير نور آفتاب بزنيد مزايا: بقيه امکاناتش!
لپ تاپ بي نقص و عالي هست من مدل GT70 عادي رو دارم حرف نداره تا حالا نشده که به هر دليلي از خريدش پشيمون باشم چند تا ويژگي که موقع خريد لپ تاپ نياز هست که بهشون توجه کنيد: 1.گرافيک و cpu لپ تاپ رو نمي توني عوض کني 2.اگه دنبال لپ تاپ گيم هستي ضخامت اصلا واست مهم نباشه چون لپ تاپ در هر صورت نياز داره که خنک شه. 3.کيبورد اين مدل خيلي خوشگله!! 4.اگه کمتر ميخواي هزينه کني مدل GX683 رو بخر چون موقع کار کردن با اين دو لپ تاپ هيچ تفاوتي در هنگام پردازش نميبيني. 5. يه ميز فن هم براش بخر. من از مارک Deep Cool که خريدم کامل راضي هستم و اون رو به شما هم توصيه ميکنم.
من الان چند ماهه يکيشو از ديجي کالاخريدم وزن مناسب در مقابل پرتابل بالاي اون واقعا منو راضي نگه داشته البته دير بالااومدن اونم زياد به چشم نمياد خيلي ازش راضيم
    '''
    # 1
    normal_text_content = '''
حدود یک هفته است که به‌دست م رسیده . لپ‌تاپ فوق‌العاده‌ایه . کیفیت ساخت خیلی خوب ه و از جنس پلاستیک با کیفیت ه . ال‌سی‌دی خیلی عالیه اصلا فکر نمی‌کردم تو این بازه قیمتی با چنین ال‌سی‌دی ای رو‌به‌رو بشم . یکی از مزایای دیگه این لپ‌تاپ وجود دو گرافیکی یکی گرافیک اینتل و یکی هم گرافیک ان ویدیا که در‌زمان انجام کارهای گرافیکی سنگین خودکار به گرافیک ان ویدیا سوییچ می‌شه که این مورد تاثیر زیادی روی زمان شارژ دهی این لپ‌تاپ داره . کیفیت صدای خروجی هم مناسب و راضی‌کننده است . در ضمن چیزی که تو مشخصات ذکر نشده این ه که تاچ پد این از نوع مولتی تاچ ه که به‌راحتی کار در سیستم عامل ویندوز ۸ کمک می‌کنه . همراه دستگاه سیستم عاملی وجود نداره اما درایور های موجود مخصوص ویندوز ۸ هست . کیفیت کیبورد و نرمی کلیدها هم خیلی خوب ه . فکر نمی‌کردم لپ‌تاپها سامسونگ تا این حد با کیفیت باشه . تو این بازه قیمتی فقط این لپ‌تاپ و بخرید چون واقعا ارزش خرید داره
برید به رستوران https://chilivery.com/tehran/restaurant۱/ . غذا ش خیلی عالیه 😍😍😍
از‌نظر قیمت میارزه ک بری ولی واقعا خفه است
مث این ، جای دیگه ای ندیدم مشتریا ش انقدر زیاد باشه .
کیفیت پیتزاها ش اصلن خوب نیست … از شلوغی میدون تجریش داره پول درمیاره .
باز م از ش خرید می‌کنم ، بهترین منطقه است .
اگه یه باربری اونجا مشتری ش میشی .
برای ارسال رزومه به آدرس job@gmail.com میل بزنید .
کتاب ه رو تو فرهنگ‌سرا پیدا ش کردم . کتابا شون م واقعن عالیه
در‌صورت مشکل به آیدی @bitianist پیام بدهید .
حاضر م شرط ببندم همون و ورداشتن تزیین کردن و برای ما اووردن !
آخه واقعا درسته این کار ؟ چرا خب درست نمی‌کنن ؟
محیطی دلباز و شادی داره دو تا سالن بزرگ هم داره شیشلیک و ماهیچه و گوشت ش هم خیلی خوب ه من غذاهای دیگه ش و تا حالا تست نکردم
همه چی عالی غذا عالی بود و برخورد پرسنل فوق‌العاده مودبانه بود دستشویی خوب عالی و توالت فوق‌العاده تمیز و عالی پذیرایی عالی خلاصه مدیریت عالی فقط امیدوار م خراب نشه چون واقعا حیف ه
نمره برخورد با مشتری تقریبا صفر مناسب شون ه ، غذا هم خیلی خیلی شور بود ، سیب‌زمینی ش خوب بود ، و من به اون رنگ نون برگرا شون خیلی خوش‌بین نیستم . تمام !
تازه افتتاح شده محیط شیک با فضای باز خیلی زیبا کیفیت غذا ش که خیلی عالی بود با بهترین رستورانهای تهران برابری می‌کنه برخورد پرسنل هم خیلی گرم و صمیمی بود اگه به همین روال پیش برن و کیفیت غذا شون م همین طور بمونه خیلی عالیه
برخورد پرسنل عالی … کیفیت غذا عالی … قیمت خوب … حتمنی سر بزنید
۲ تا قلیون با ۶ تا چایی لیوانی ، ۱۳۰ هزار تومن ! قلیون بدون سرویس ! هیچ چیز خاصی هم نداره فقط سالن داخلی اش یه کم خوشگل تزیین شده .
ما رفتیم ملورین و به نظر م چیزبرگر و همبرگر سوپریم شون فوق‌العاده بود طعم گوشت عالی بود نون خوش‌طعم و یه سس تار تار خوشمزه بعد‌از مدتها همبرگری خوردم که دوست داشتم 😍😍 البته به نظر م منو ی کافه هم خوب بود مخصوصا کاپوچینو و کیک موکا ممنون 🙏🏻🙏🏻
غذا ، فضا ، برخورد با مشتری همه چی عالی ، ما عاشق سالادای سزار شیم با پیتزا و … ضمنا شبها خیلی شلوغ می‌شه
متاسفانه لیست قیمت با اینکه تا تیر ۹۲ به‌روز شده با قیمت واقعی تفاوت فاحش داشت . سرویس ۱۵ ٪ با ۶ ٪ ارزش افزوده بود . ( ۲۱ ٪ ) . قیمتها و منو خیلی فرق داشتن . رستوران خوبی به همه دوستان توصیه می‌کنم .
چرا جدیدا اخر همه فیلما بی‌نتیجه تموم می‌شه الان ته ش چی شد
خیلی قشنگ ه مشکلات نسل جدید و عشق و عاشقی‌ها رو خوب نشون داده که با یه نخواستن همه چی تموم می‌شه
ما در تاریخ ۹۷/۶/۵ در‌قالب جمع دوستانه و همکاران قدیمی برای شام به این رستوران رفتیم . انصافا همه چی عالی بود . کیفیت غذاها خوب بود و از همه مهمتر صبر و حوصله کارکنان بود . چون ما عده مون زیاد بود و می‌خواستیم که صورتحسابها جدا باشه که همین طور هم شد . حجم غداها به نسبت قیمت خیلی خوب ه . برای مثال پاستا پنه یک غذای دونفره هست . سالادها رو هم امتحان کنید عالین .
با سلام اطلاعات مربوط به cache اشتباه واردشده است . ۳ m نمی‌باشد و ۱۰۲۴ kb است . موفق باشید
به نظر من از‌نظر بدنه شکی در این مدل نیست چون جنس ش از کربن یا همون فولاد که در اینجا از نوع سبک آن استفاده‌شده البته سری k ایسوس از آلومینیوم استفاده‌شده که خیلی زیبا ست و در‌عین‌حال که کم استقامت دارد . از‌نظر سخت‌افزاری عین k هست به‌جز صفحه نمایش بزرگتر و استحکام بالا در این مدل . و زیبایی و باتری قویتر در مدل k .
دوستان تو نقد نوشته‌شده بود که قابلیت زوم دو انگشت ی و … نداره تاچ ش در‌حالی‌که اگه به قسمت تنظیمات ماوس برید می‌تونید تمامی امکانات تاچ ش رو فعال کنید .
این دستگاه جزء اولین و شاید تنها سریه که تا الان از نسل چهارم سی‌پی‌یو‌های اینتل استفاده می‌کنه
من این لپ‌تاپ رو دارم از‌نظر سخت‌افزار حرف نداره و برای وب گردی و کارهای اداری و بازی‌های متوسط مناسب هست هنگام بازی کردن با بازی‌های سنگین هیچ کاهش سرعتی دیده نمی‌شه ولی سی‌پی یو بشدت داغ می‌شه این لپ تاب برای اون هایی که سخت‌افزار عالی همراه‌با صفحه نمایش بزرگ و کارهای روزمره با قیمت مناسب می‌خان توصیه می‌کنم حتما این لپ تاپو بخرین
با‌توجه‌به این مشخصات بهتر بود از باطری بهتری استفاده می‌شد
یک سالی هست که این لپ‌تاپ رو خریدم در کل از ش راضی ام ، ملاک اصلی م واس ه انتخاب ش وزن ش بود . البته مشخصات خوبی هم نسبت به قیمت ش تو مدلهای هم رده خود ش داشت
از هر نظر لپ‌تاپ بی‌نظیری من بعد‌از مدتها تحقیق خریدم ش سرعت ش عالیه بدنه هم اصلا زیاد گرم نمی‌شه در کل واقعا ارزش خرید داره
سلام به همگی مشکلات : - من روش ویندوز سون نصب کردم ، رفتم ۱ .۶ گیگ درایور سون دان کردم ولی کارت گرافیکی ش و نشناخت ولی ویندوز ۸ ریختم مشکلی نداشت .( البته شاید مشکل از کامل نبودن درایورها باشه ) - صفحه نمایش انقدر هم که گفته می‌شه بد نیست ولی باید قید کار کردن با لپ‌تاپ زیر نور آفتاب بزنید مزایا : بقیه امکانات ش !
لپ‌تاپ بی‌نقص و عالی هست من مدل GT۷۰ عادی رو دارم حرف نداره تا حالا نشده که به هر دلیلی از خرید ش پشیمون باشم چند تا ویژگی که موقع خرید لپ‌تاپ نیاز هست که به شون توجه کنید : ۱ . گرافیک و cpu لپ‌تاپ رو نمی‌تونی عوض کنی ۲ . اگه دنبال لپ‌تاپ گیم هستی ضخامت اصلا واس ت مهم نباش ه چون لپ‌تاپ در هر صورت نیاز داره که خنک شه . ۳ . کیبورد این مدل خیلی خوشگل ه ! ۴ . اگه کمتر می‌خوای هزینه کنی مدل GX۶۸۳ رو بخر چون موقع کار کردن با این دو لپ‌تاپ هیچ تفاوتی در هنگام پردازش نمی‌بینی . ۵ . یه میز فن هم برا ش بخر . من از مارک Deep Cool که خریدم کامل راضی هستم و اون رو به شما هم توصیه می‌کنم .
من الان چندماهه یکی ش و از دیجی کالا خریدم وزن مناسب در‌مقابل پرتابل بالای اون واقعا منو راضی نگه داشته البته دیر بالا اومدن اون م زیاد به چشم نمی‌اد خیلی از ش راضی م
'''.strip()

    tags_string = '''
D U N V J E C V O N A O N N D A C J E N N E N C O N D A D N V Z T N N E L N I A V O T E N Z T N N U A U N N J U J N N J E N N A A A E N N N V J T N N A E N N V T N V O N N A J A J D V O E N N J Z N N V Z C J N N Z E N N C J D N E N N U N V O A N N C N V J N N A A N U V O N N J A N J D A C O N V N N E T N E N V O Z T N N D T N J V J D N N V O 
V E N K O N C D A X O 
E N V C V J D A V O 
N Z O N Z I V N C D A V O O 
N N C N A V O E A N N V N V O O 
D C E C N V O A N V O O 
J U N D N C A O O 
E N N E N M N V O O 
N R N Z N A C V O N C C N A O 
E N E N S N V O O 
A C N V Z J V N V J E Z V O O 
D D A T N O D D A V O O 
A A J N V U L N A J V A J N J N C J D A C Z N Z C J E D N V O 
T N A N A V J N N A A V N A A J N A A J A N A A N A D A C A V J D N C O 
N N E N D U A C C O N J D D N V O N C A V O J Z E T N N A C D A V O A O O 
D N V N A E N D D A N N C J D A V E A N N N V N N J D A J A V J E T N D N J N N C C Z N N D A O 
N N A O N N A O N A O N N V O 
U E N E U E N N O U U N O N E N O T N A J V D N A C U A A N V O O 
Z V A J E N C N J N N C A V N N A V N A J U N N N A E N Z V J N V X D E N C N C N J D V D N J N N A X O 
N O N O N E N T N A O Z A N N V E N J O J N D A V O 
D N N E J E N U A V E N A N A V O N U O E U O N V V O O U O O O N J N D N V O N A E T N N V O O 
D D N T D A A V D N C Z V O 
D A C N N A J N J N N A N V J E U V T N A V O 
Z E N U E N A J N A E N E T N V O D T N A V O N N A V J E Z A N J N N V O J Z N N A V J V J N A V J T N J V O N N E N N D A C O E N N N U N A V O N N J N V U O O 
E N N A E N A A V O U L V J U L V O A V O 
E N Z E N N E T N V J N C E N J T N J E D E N N Z A D N N A E N A J D A C J J J A N V O E A D N V E N N A J N D E T N O J N J N A E N N O O 
N Z N A V J N N U N C J O V N C J J E N N N V V T N N C P A V O O 
T N N U J D D N J E D E N U N N N V O 
Z T N N V E N N V J E N N J N A J N A A V N N V E N A T N A V V J N N D A V T N N E T N J N A E N N A J N A E N A V N V D T N J A O 
E T N A V E N A N V O 
A V J T N N V E T E C A C O N A C E C N C N C V O D N A J N E N C Z N J N Z C V O 
E T N N A Z E N N V C N C A N J D A A V E T D N N V O 
R E T N O O Z N N N N V O V U N N N N N V J N A C J V J N U V N V O D D N E A V N V O O N N D J J V V A V J V N N E N A N N V N O N N C O O 
N A J A V Z N N A N V N V J D V J E T N E N C A V T L N J N N N N V J E N N V O U O N J N N N V N V U O J N N N V N D E C A V C J N E T N N V J A N O U O N T N D A C O U O J A V N V N N N N D N N E T U N T N E N N V O U O U N N J E C N O Z E N N N J V A A V J T N E Z J N V O O 
Z D A Z C J E N N V N A E N E T D N A N V D D A V Z C A E N V D E C A C
    '''.strip()

    correct_tagged_tokens_string = '''
حدود_D  یک_U  هفته_N  است_V  که_J  به‌دست_E  م_C  رسیده_V  ._O  لپ‌تاپ_N  فوق‌العاده‌ایه_A  ._O  کیفیت_N  ساخت_N  خیلی_D  خوب_A  ه_C  و_J  از_E  جنس_N  پلاستیک_N  با_E  کیفیت_N  ه_C  ._O  ال‌سی‌دی_N  خیلی_D  عالیه_A  اصلا_D فکر_N  نمی‌کردم_V  تو_Z_E  این_T  بازه_N  قیمتی_N  با_E  چنین_L  ال‌سی‌دی_N  ای_I_C  رو‌به‌رو_A  بشم_V  ._O  یکی_T  از_E  مزایای_N  دیگه_Z  این_T  لپ‌تاپ_N  وجود_N  دو_U  گرافیکی_A_N  یکی_U  گرافیک_N  اینتل_N  و_J  یکی_U  هم_J  گرافیک_N ان‌ویدیا_N  که_J  در‌زمان_E  انجام_N  کارهای_N  گرافیکی_A  سنگین_A  خودکار_A  به_E  گرافیک_N  ان‌ویدیا_N  سوییچ_N  می‌شه_V  که_J  این_T  مورد_N  تاثیر_N  زیادی_A  روی_E  زمان_N  شارژ_N  دهی_V  این_T  لپ‌تاپ_N  داره_V  ._O  کیفیت_N صدای_N  خروجی_A  هم_J  مناسب_A  و_J  راضی‌کننده_D_A  است_V  ._O  در_E_R  ضمن_N_R  چیزی_N  که_J  تو_Z_E  مشخصات_N  ذکر_N  نشده_V  این_Z  ه_C  که_J  تاچ‌پد_N  این_Z  از_E  نوع_N  مولتی‌تاچ_N  ه_C  که_J  به‌راحتی_D  کار_N  در_E سیستم‌عامل_N  ویندوز_N  ۸_U  کمک_N  می‌کنه_V  ._O  همراه_A  دستگاه_N  سیستم‌عامل_N  ی_C  وجود_N  نداره_V  اما_J  درایورها_N  ی_C  موجود_A  مخصوص_A  ویندوز_N  ۸_U  هست_V  ._O  کیفیت_N  کیبورد_N  و_J  نرمی_A  کلیدها_N  هم_J خیلی_D  خوب_A  ه_C  ._O  فکر_N  نمی‌کردم_V  لپ‌تاپها_N  سامسونگ_N  تا_E  این_T  حد_N  با_E  کیفیت_N  باشه_V  ._O  تو_Z_E  این_T  بازه_N  قیمتی_N  فقط_D  این_T  لپ‌تاپ_N  و_J_P  بخرید_V  چون_J  واقعا_D  ارزش_N  خرید_N  داره_V  
برید_V  به_E  رستوران_N  https://chilivery.com/tehran/restaurant۱/_K  ._O  غذا_N  ش_C  خیلی_D  عالیه_A  😍😍😍_X  
از‌نظر_E  قیمت_N  میارزه_V  ک_C_J  بری_V  ولی_J  واقعا_D  خفه_A  است_V  
مث_D  این_Z  ،_O  جای_N  دیگه_Z  ای_I_C  ندیدم_V  مشتریا_N  ش_C  انقدر_D  زیاد_A  باشه_V  ._O  
کیفیت_N  پیتزاها_N  ش_C  اصلن_D  خوب_A  نیست_V  …_O  از_E  شلوغی_A  میدون_N  تجریش_N  داره_V  پول_N  درمیاره_V  ._O  
باز_D  م_C  از_E  ش_C  خرید_N  می‌کنم_V  ،_O  بهترین_A  منطقه_N  است_V  ._O  
اگه_J  یه_U  بار_N  بری_N  اونجا_D  مشتری_N  ش_C  میشی_V  ._O  
برای_E  ارسال_N  رزومه_N  به_E  آدرس_N  job@gmail.com_M  میل_N  بزنید_V  ._O  
کتاب_N  ه_C  رو_N_P  تو_Z_E  فرهنگ‌سرا_N  پیدا_A  ش_C  کردم_V  ._O  کتابا_N  شون_C  م_C  واقعن_D  عالیه_A  
در‌صورت_E  مشکل_N  به_E  آیدی_N  @bitianist_S  پیام_N  بدهید_V  ._O  
حاضر_A  م_C  شرط_N  ببندم_V  همون_Z  و_J_P  ورداشتن_V  تزیین_N  کردن_V  و_J  برای_E  ما_Z  اووردن_V  !_O  
آخه_D  واقعا_D  درسته_A  این_T  کار_N  ؟_O  چرا_D  خب_D  درست_A  نمی‌کنن_V  ؟_O  
محیطی_A  دلباز_A  و_J  شادی_N_A  داره_V  دو_U  تا_L  سالن_N  بزرگ_A  هم_J  داره_V  شیشلیک_N  و_J  ماهیچه_N  و_J  گوشت_N  ش_C  هم_J  خیلی_D  خوب_A  ه_C  من_Z  غذاهای_N  دیگه_Z  ش_C  و_J_P  تا_E  حالا_D  تست_N  نکردم_V  
همه_T  چی_N  عالی_A  غذا_N  عالی_A  بود_V  و_J  برخورد_N  پرسنل_N  فوق‌العاده_A  مودبانه_A  بود_V  دستشویی_N  خوب_A  عالی_A  و_J  توالت_N  فوق‌العاده_A  تمیز_A  و_J  عالی_A  پذیرایی_N  عالی_A  خلاصه_A_D  مدیریت_N  عالی_A  فقط_D امیدوار_A  م_C  خراب_A  نشه_V  چون_J  واقعا_D  حیف_N  ه_C  
نمره_N  برخورد_N  با_E  مشتری_N  تقریبا_D  صفر_U  مناسب_A  شون_C  ه_C  ،_O  غذا_N  هم_J  خیلی_D  خیلی_D  شور_N  بود_V  ،_O  سیب‌زمینی_N  ش_C  خوب_A  بود_V  ،_O  و_J  من_Z  به_E  اون_T  رنگ_N  نون_N  برگرا_A  شون_C  خیلی_D خوش‌بین_A  نیستم_V  ._O  تمام_A  !_O  
تازه_D  افتتاح_N  شده_V  محیط_N  شیک_A  با_E  فضای_N  باز_D  خیلی_D  زیبا_A  کیفیت_N  غذا_N  ش_C  که_J  خیلی_D  عالی_A  بود_V  با_E  بهترین_A  رستورانهای_N  تهران_N  برابری_N  می‌کنه_V  برخورد_N  پرسنل_N  هم_J  خیلی_D  گرم_A  و_J صمیمی_A  بود_V  اگه_J  به_E  همین_T  روال_N  پیش_D  برن_N  و_J  کیفیت_N  غذا_N  شون_C  م_C  همین_Z  طور_N  بمونه_N  خیلی_D  عالیه_A  
برخورد_N  پرسنل_N  عالی_A  …_O  کیفیت_N  غذا_N  عالی_A  …_O  قیمت_N  خوب_A  …_O  حتمنی_D  سر_N  بزنید_V  
۲_U  تا_E  قلیون_N  با_E  ۶_U  تا_E  چایی_N  لیوانی_N  ،_O  ۱۳۰_U  هزار_U  تومن_N  !_O  قلیون_N  بدون_E  سرویس_N  !_O  هیچ_T  چیز_N  خاصی_A  هم_J  نداره_V  فقط_D  سالن_N  داخلی_A  اش_C  یه_U  کم_A  خوشگل_A  تزیین_N  شده_V  ._O  
ما_Z  رفتیم_V  ملورین_A  و_J  به_E  نظر_N  م_C  چیزبرگر_N  و_J  همبرگر_N  سوپریم_N  شون_C  فوق‌العاده_A  بود_V  طعم_N  گوشت_N  عالی_A  بود_V  نون_N  خوش‌طعم_A  و_J  یه_U  سس_N  تار_N  تار_N  خوش_A  مزه_N  بعد‌از_E  مدتها_N همبرگری_Z  خوردم_V  که_J  دوست_N  داشتم_V  😍😍_X  البته_D  به_E  نظر_N  م_C  منو_N  ی_C  کافه_N  هم_J  خوب_D  بود_V  مخصوصا_D  کاپوچینو_N  و_J  کیک_N  موکا_N  ممنون_A  🙏🏻🙏🏻_X  
غذا_N  ،_O  فضا_N  ،_O  برخورد_N  با_E  مشتری_N  همه_T  چی_N  عالی_A  ،_O  ما_Z  عاشق_A  سالادای_N  سزار_N  شیم_V  با_E  پیتزا_N  و_J  …_O  ضمنا_J  شبها_N  خیلی_D  شلوغ_A  می‌شه_V  
متاسفانه_D  لیست_N  قیمت_N  با_E  اینکه_J  تا_E  تیر_N  ۹۲_U  به‌روز_A  شده_V  با_E  قیمت_N  واقعی_A  تفاوت_N  فاحش_A  داشت_V  ._O  سرویس_N  ۱۵_U  ٪_O  با_E  ۶_U  ٪_O  ارزش_N  افزوده_V  بود_V  ._O  (_O  ۲۱_U  ٪_O  )_O  ._O قیمتها_N  و_J  منو_N  خیلی_D  فرق_N  داشتن_V  ._O  رستوران_N  خوبی_A  به_E  همه_T  دوستان_N  توصیه_N  می‌کنم_V  ._O  
چرا_D  جدیدا_D  اخر_N  همه_T  فیلما_D  بی‌نتیجه_A  تموم_A  می‌شه_V  الان_D  ته_N  ش_C  چی_Z  شد_V  
خیلی_D  قشنگ_A  ه_C  مشکلات_N  نسل_N  جدید_A  و_J  عشق_N  و_J  عاشقی‌ها_N  رو_N  خوب_A  نشون_N  داده_V  که_J  با_E  یه_U  نخواستن_V  همه_T  چی_N  تموم_A  می‌شه_V  
ما_Z  در_E  تاریخ_N  ۹۷/۶/۵_U  در‌قالب_E  جمع_N  دوستانه_A  و_J  همکاران_N  قدیمی_A  برای_E  شام_N  به_E  این_T  رستوران_N  رفتیم_V  ._O  انصافا_D  همه_T  چی_N  عالی_A  بود_V  ._O  کیفیت_N  غذاها_N  خوب_A  بود_V  و_J  از_E  همه_Z مهمتر_A  صبر_N  و_J  حوصله_N  کارکنان_N  بود_V  ._O  چون_J  ما_Z  عده_N  مون_N  زیاد_A  بود_V  و_J  می‌خواستیم_V  که_J  صورتحسابها_N  جدا_A  باشه_V  که_J  همین_T  طور_N  هم_J  شد_V  ._O  حجم_N  غداها_N  به_E  نسبت_N  قیمت_N خیلی_D  خوب_A  ه_C  ._O  برای_E  مثال_N  پاستا_N  پنه_N  یک_U  غذای_N  دونفره_A  هست_V  ._O  سالادها_N  رو_N  هم_J  امتحان_N  کنید_V  عالین_A  ._O  
با_E  سلام_N  اطلاعات_N  مربوط_A  به_E  cache_N  اشتباه_A  وارد_N  شده‌است_V  ._O  ۳_U  m_L  نمی‌باشد_V  و_J  ۱۰۲۴_U  kb_L  است_V  ._O  موفق_A  باشید_V  
به_E  نظر_N  من_Z  از‌نظر_E  بدنه_N  شکی_N  در_E  این_T  مدل_N  نیست_V  چون_J  جنس_N  ش_C  از_E  کربن_N  یا_J  همون_T  فولاد_N  که_J  در_E  اینجا_D  از_E  نوع_N  سبک_N  آن_Z  استفاده‌شده_A  البته_D  سری_N  k_N  ایسوس_N  از_E آلومینیوم_N  استفاده‌شده_A  که_J  خیلی_D  زیبا_A  ست_C  و_J  در‌عین‌حال_J  که_J  کم_A  استقامت_N  دارد_V  ._O  از‌نظر_E  سخت‌افزاری_A  عین_D  k_N  هست_V  به‌جز_E  صفحه_N  نمایش_N  بزرگتر_A  و_J  استحکام_N  بالا_D  در_E  این_T  مدل_N ._O  و_J  زیبایی_N  و_J  باتری_N  قویتر_A  در_E  مدل_N  k_N  ._O  
دوستان_N  تو_Z_E  نقد_N  نوشته‌شده_A  بود_V  که_J  قابلیت_N  زوم_N  دو_U  انگشت_N  ی_C  و_J  …_O  نداره_V  تاچ_N  ش_C  در‌حالی‌که_J  اگه_J  به_E  قسمت_N  تنظیمات_N  ماوس_N  برید_V  می‌تونید_V  تمامی_T  امکانات_N  تاچ_N  ش_C  رو_P فعال_A  کنید_V  ._O  
این_T  دستگاه_N  جزء_N  اولین_U  و_J  شاید_D  تنها_D  سریه_N  که_J  تا_E  الان_D  از_E  نسل_N  چهارم_U  سی‌پی‌یو‌های_N  اینتل_N  استفاده_N  می‌کنه_V  
من_Z  این_T  لپ‌تاپ_N  رو_N  دارم_V  از‌نظر_E  سخت‌افزار_N  حرف_N  نداره_V  و_J  برای_E  وب_N  گردی_N  و_J  کارهای_N  اداری_A  و_J  بازی‌های_N  متوسط_A  مناسب_A  هست_V  هنگام_N  بازی_N  کردن_V  با_E  بازی‌های_N  سنگین_A  هیچ_T کاهش_N  سرعتی_A  دیده_V  نمی‌شه_V  ولی_J  سی‌پی_N  یو_N  بشدت_D  داغ_A  می‌شه_V  این_T  لپ_N  تاب_N  برای_E  اون_T  هایی_N  که_J  سخت‌افزار_N  عالی_A  همراه‌با_E  صفحه_N  نمایش_N  بزرگ_A  و_J  کارهای_N  روزمره_A  با_E  قیمت_N مناسب_A  می‌خان_V  توصیه_N  می‌کنم_V  حتما_D  این_T  لپ‌تاپ_N  و_J_P  بخرین_A  
با‌توجه‌به_E  این_T  مشخصات_N  بهتر_A  بود_V  از_E  باطری_N  بهتری_A  استفاده_N  می‌شد_V  
یک‌سالی_A  هست_V  که_J  این_T  لپ‌تاپ_N  رو_N  خریدم_V  در_E  کل_T  از_E  ش_C  راضی_A  ام_C  ،_O  ملاک_N  اصلی_A  م_C  واس_E  ه_C  انتخاب_N  ش_C  وزن_N  ش_C  بود_V  ._O  البته_D  مشخصات_N  خوبی_A  هم_J  نسبت_N  به_E قیمت_N  ش_C  تو_Z_E  مدلهای_N  هم_J  رده_N  خود_Z  ش_C  داشت_V  
از_E  هر_T  نظر_N  لپ‌تاپ_N  بی‌نظیری_A  من_Z  بعد‌از_E  مدتها_N  تحقیق_N  خریدم_V  ش_C  سرعت_N  ش_C  عالیه_A  بدنه_N  هم_J  اصلا_D  زیاد_A  گرم_A  نمی‌شه_V  در_E  کل_T  واقعا_D  ارزش_N  خرید_N  داره_V  
سلام_N  به_E  همگی_T  مشکلات_N  :_O  -_O  من_Z  روش_N  ویندوز_N  سون_N  نصب_N  کردم_V  ،_O  رفتم_V  ۱_U  .۶_N  گیگ_N  درایور_N  سون_N  دان_N  کردم_V  ولی_J  کارت_N  گرافیکی_A  ش_C  و_J_P  نشناخت_V  ولی_J  ویندوز_N  ۸_U ریختم_V  مشکلی_N  نداشت_V  .(_O  البته_D  شاید_D  مشکل_N  از_E  کامل_A  نبودن_V  درایورها_N  باشه_V  )_O  -_O  صفحه_N  نمایش_N  انقدر_D  هم_J  که_J  گفته_V  می‌شه_V  بد_A  نیست_V  ولی_J  باید_V  قید_N  کار_N  کردن_V  با_E  لپ‌تاپ_N زیر_A  نور_N  آفتاب_N  بزنید_V  مزایا_N  :_O  بقیه_N  امکانات_N  ش_C  !_O  
لپ‌تاپ_N  بی‌نقص_A  و_J  عالی_A  هست_V  من_Z  مدل_N  GT۷۰_N  عادی_A  رو_N  دارم_V  حرف_N  نداره_V  تا_J  حالا_D  نشده_V  که_J  به_E  هر_T  دلیلی_N  از_E  خرید_N  ش_C  پشیمون_A  باشم_V  چند_T  تا_L  ویژگی_N  که_J  موقع_N خرید_N  لپ‌تاپ_N  نیاز_N  هست_V  که_J  به_E  شون_N  توجه_N  کنید_V  :_O  ۱_U  ._O  گرافیک_N  و_J  cpu_N  لپ‌تاپ_N  رو_N  نمی‌تونی_V  عوض_N  کنی_V  ۲_U  ._O  اگه_J  دنبال_N  لپ‌تاپ_N  گیم_N  هستی_V  ضخامت_N  اصلا_D  واس_E  ت_C مهم_A  نباش_V  ه_C  چون_J  لپ‌تاپ_N  در_E  هر_T  صورت_N  نیاز_N  داره_V  که_J  خنک_A  شه_N  ._O  ۳_U  ._O  کیبورد_N  این_T  مدل_N  خیلی_D  خوشگل_A  ه_C  !_O  ۴_U  ._O  اگه_J  کمتر_A  می‌خوای_V  هزینه_N  کنی_V  مدل_N  GX۶۸۳_N رو_N  بخر_N  چون_D  موقع_N  کار_N  کردن_V  با_E  این_T  دو_U  لپ‌تاپ_N  هیچ_T  تفاوتی_N  در_E  هنگام_N  پردازش_N  نمی‌بینی_V  ._O  ۵_U  ._O  یه_U  میز_N  فن_N  هم_J  برا_E  ش_C  بخر_N  ._O  من_Z  از_E  مارک_N  Deep_N_R  Cool_N_R که_J  خریدم_V  کامل_A  راضی_A  هستم_V  و_J  اون_T  رو_N  به_E  شما_Z  هم_J  توصیه_N  می‌کنم_V  ._O  
من_Z  الان_D  چند_T  ماهه_N  یکی_Z  ش_C  و_J_P  از_E  دیجی_N  کالا_N  خریدم_V  وزن_N  مناسب_A  در‌مقابل_E  پرتابل_N  بالای_E  اون_T  واقعا_D  منو_N  راضی_A  نگه_N  داشته_V  البته_D  دیر_D  بالا_A  اومدن_V  اون_Z  م_C  زیاد_A  به_E  چشم_N نمی‌اد_V  خیلی_D  از_E  ش_C  راضی_A  م_C 
'''

    # normal_text_content = normal_text_content.replace('\n', ' \\n ')
    # normal_text_content = re.sub(' +', ' ', normal_text_content).strip()
    # token_contents_tuple = normal_text_content.split(' ')

    # tags_string = tags_string.replace('\n', ' ')
    # tags_string = re.sub(' +', ' ', tags_string).strip()
    # tags_string_tuple = tags_string.split(' ')


    # logger.info(f'token_contents_tuple {len(token_contents_tuple)} : \n{token_contents_tuple}\n')
    # logger.info(f'tags_string_tuple {len(tags_string_tuple)} : \n{tags_string_tuple}\n')

    # tagged_tokens = zip(token_contents_tuple, tags_string_tuple)
    tagged_tokens = []
    parts = None
    token_content, tag_name = '', ''
    correct_tagged_tokens_string = correct_tagged_tokens_string.strip().replace('\n', ' \\n_O ').strip()
    for tagged_token in correct_tagged_tokens_string.split():
        parts = tagged_token.split('_')
        token_content = parts[0]
        tag_name = parts[1]
        if len(parts) == 3:
            tag_name = parts[2]
        logger.info(f'> Current tagged_token : {(token_content, tag_name)}')
        tagged_tokens.append((token_content, tag_name))

    # new_line = '\n'
    # logger.info(f'> tagged_tokens : \n {new_line.join([tagged_token.__str__() for tagged_token in tagged_tokens])}\n')
    tagged_tokens = [generate_tagged_token_dictionary(tagged_token[0], generate_tag_dictionary(name=tagged_token[1])) for tagged_token in tagged_tokens]
    text = generate_text_dictionary(text_content)
    text_tag = generate_text_tag_dictionary(
                tagged_tokens=tagged_tokens,
                tagger=tagger,
                text=text)

    logger.info(f'text_tag : \n{text_tag}')
    response, error = None, None
    if text_tag_id:
        response, error = put(f'{text_tags_url}/{text_tag_id}', text_tag)
    else:
        response, error = post(text_tags_url, text_tag)
        logger.info(response)
    if error:
        return

def create_sample_text_tag():
    tagged_tokens = [generate_tagged_token_dictionary(tagged_token[0], generate_tag_dictionary(name=tagged_token[1])) for tagged_token in tagged_tokens]
    text = generate_text_dictionary(text_content)
    text_tag = generate_text_tag_dictionary(
                tagged_tokens=tagged_tokens,
                tagger=tagger,
                text=text)

def main():
    try:
        # import_tag_sets()
        # import_validators()
        # import_normalizers()
        # import_taggers()

        
        # import_bijankhan_data()
        # import_text_equivalents()
        # import_word_equivalents()

        import_mohaverekhan_text_tag('252e9ff9-d8c1-4e9b-832c-8aa27cbb0504')
        # import_mohaverekhan_text_tag()
        # import_mohaverekhan_evaluate_text_tag()
        # create_sample_text_tag()

        # import_tags()
        # import_translation_characters()
        # import_correction_patterns()
    except Exception as e:
        logger.exception(e)

if __name__ == "__main__": main()

