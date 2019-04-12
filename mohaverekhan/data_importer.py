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
# refinement_pattern_url = fr'{base_api_url}/rules/refinement-patterns'

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

bitianist_tag_set_dictionary = bijankhan_tag_set_dictionary + [
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
    bitianist_tag_set = generate_tag_set_dictionary('bitianist-tag-set', 
        tags=bitianist_tag_set_dictionary)

    response, error = post(tag_sets_url, bitianist_tag_set)
    if error:
        return 0

@utils.time_usage(logger)
def import_validators():
    bitianist_validator = generate_validator_dictionary(
        'bitianist-validator',
        show_name='اعتبارسنج بیتیانیست',
        owner='bitianist'
    )

    response, error = post(validators_url, bitianist_validator)
    if error:
        return 0

@utils.time_usage(logger)
def import_normalizers():
    # # 1
    # model_details = {
    #    'type': 'manual'
    # }
    # bitianist_bitianist_normalizer = generate_normalizer_dictionary(
    #     'bitianist-manual-normalizer',
    #     show_name='نرمال‌کننده دستی بیتیانیست',
    #     owner='bitianist',
    #     is_automatic=False,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, bitianist_bitianist_normalizer)
    # if error:
    #     return


    # # 2
    # model_details = {
    #     'type': 'rule-based',
    #     'state': 'ready'
    # }
    # bitianist_refinement_normalizer = generate_tagger_dictionary(
    #     'bitianist-refinement-normalizer',
    #     show_name='نرمال‌کننده پالایش',
    #     owner='bitianist',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, bitianist_refinement_normalizer)
    # if error:
    #     return


    # # 3
    # model_details = {
    #     'type': 'stochastic',
    #     'module': 'seq2seq',
    #     'state': 'not-ready'
    # }
    # bitianist_seq2seq_normalizer = generate_tagger_dictionary(
    #     'bitianist-seq2seq-normalizer',
    #     show_name='نرمال‌کننده توالی‌به‌توالی',
    #     owner='bitianist',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, bitianist_seq2seq_normalizer)
    # if error:
    #     return

    # # 4
    # model_details = {
    #     'type': 'rule-based',
    #     'state': 'ready'
    # }
    # bitianist_replacement_normalizer = generate_tagger_dictionary(
    #     'bitianist-replacement-normalizer',
    #     show_name='نرمال‌کننده جایگزینی',
    #     owner='bitianist',
    #     is_automatic=True,
    #     model_details=model_details
    # )
    # response, error = post(normalizers_url, bitianist_replacement_normalizer)
    # if error:
    #     return

    # 5
    model_details = {
        'type': 'rule-based',
        'state': 'ready'
    }
    bitianist_basic_normalizer = generate_tagger_dictionary(
        'bitianist-basic-normalizer',
        show_name='نرمال‌کننده بنیادی',
        owner='bitianist',
        is_automatic=True,
        model_details=model_details
    )
    response, error = post(normalizers_url, bitianist_basic_normalizer)
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

    # bitianist_manual_tagger = generate_tagger_dictionary(
    #     'bitianist-manual-tagger',
    #     show_name='برچسب‌زن دستی بیتیانیست',
    #     owner='bitianist',
    #     tag_set='bitianist-tag-set',
    #     is_automatic=False,
    #     model_details=model_details
    # )

    # response, error = post(taggers_url, bitianist_manual_tagger)
    # if error:
    #     return 0

    # # 3
    # model_details = {
    #     'module': 'nltk',
    #     'type': 'hybrid',
    #     'state': 'not-ready',
    # }

    # bitianist_refinement_tagger = generate_tagger_dictionary(
    #     'bitianist-refinement-tagger',
    #     show_name='برچسب‌زن پالایش',
    #     owner='bitianist',
    #     tag_set='bitianist-tag-set',
    #     is_automatic=True,
    #     model_details=model_details
    # )

    # response, error = post(taggers_url, bitianist_refinement_tagger)
    # if error:
    #     return 0

    
    # 4
    model_details = {
        'module': 'nltk',
        'type': 'hybrid',
        'state': 'not-ready',
    }

    bitianist_seq2seq_tagger = generate_tagger_dictionary(
        'bitianist-seq2seq-tagger',
        show_name='برچسب‌زن توالی‌به‌توالی',
        owner='bitianist',
        tag_set='bitianist-tag-set',
        is_automatic=True,
        model_details=model_details
    )

    response, error = post(taggers_url, bitianist_seq2seq_tagger)
    if error:
        return 0



@utils.time_usage(logger)
def import_text_equivalents():
    df = pd.read_excel(text_equivalents_path, sheet_name='main')
    text_content, text_normal_content = '', ''
    text = None
    logger.info(f'>> Reading text_equivalents : {df.columns}')
    normalizer = 'bitianist-manual-normalizer'
    # manual_normalizer = generate_normalizer_dictionary('manual-normalizer')
    i = 0
    for i in df.index:

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
    logger.info(f'> Items count : {i+1}')

@utils.time_usage(logger)
def import_word_equivalents():
    df = pd.read_excel(word_equivalents_path, sheet_name='main')
    word_content, word_normal_content = '', ''
    word = None
    logger.info(f'>> Reading word_equivalents : {df.columns}')
    ctr = 1
    normalizer = 'bitianist-manual-normalizer'
    word_content_set = set()
    for i in df.index:

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
    logger.info(f'> Items count : {ctr}')


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

def import_bitianist_text_tag(text_tag_id=None):
    tagger = 'bitianist-manual-tagger'

    # 1
    text_content = 'شلوغی فرهنگ‌سرا آیدی انقدر اوورد اووردن منو میدون خونه جوون زمونه نون مسلمون کتابخونه دندون'
    text_content += ' نشون پاستا پنه تاچ تنظیمات می‌تونید سی‌پی‌یو‌ سی‌پی‌یو‌‌ها گرافیک اومدن می‌خان واس ٪'

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
    logger.info(f'> text_content : \n{text_content}\n')
    logger.info(f'> tagged_tokens : \n{tagged_tokens}\n')
    text = generate_text_dictionary(text_content)
    text_tag = generate_text_tag_dictionary(
                tagged_tokens=tagged_tokens,
                tagger=tagger,
                text=text)

    response, error = None, None
    if text_tag_id:
        response, error = put(f'{text_tags_url}/{text_tag_id}', text_tag)
    else:
        response, error = post(text_tags_url, text_tag)
        logger.info(response)
    if error:
        return

def import_bitianist_evaluate_text_tag(text_tag_id=None):
    tagger = 'bitianist-manual-tagger'

    text_content = '''
بریـــــــد به رستورانhttps://chilivery.com/tehran/restaurant1/ .... غذاش خیییلی عااااالیه😍😍😍
از نظر قیمت میارزه ك برئ ولی واقعا خفست
مث این جای دیگه ای ندیدم مشتریاش انقدر زیاد باشه.
کیفیت پیتزاهاش اصلن خوب نیست... از شلوغیه میدون تجریش داره پول درمیاره.
بازم ازش خرید میکنم، بهتریییییییییییییییییین منطقست.
اگه یه بار بری اونجا مشتریش میشی.
برای ارسال رزومه به آدرس job@gmail.com میل بزنید.
کتابه رو تو فرهنگ سرا پیداش کردم.
در صورت مشکل به آیدی @bitianist پیام بدهید.
حاضرم شرط ببندم همونو ورداشتن تزئین کردن و برای ما اووردن!!!!
آخه واقعا درسته اینکار؟؟؟ چرا خب درست نمیکنن؟؟
    '''
    # 1
    normal_text_content = '''
برید به رستوران https://chilivery.com/tehran/restaurant۱/ . غذا ش خیلی عالیه 😍😍😍
از‌نظر قیمت میارزه ک بری ولی واقعا خفست
مث این جای دیگه‌ای ندیدم مشتری اش انقدر زیاد باشه .
کیفیت پیتزاهاش اصلن خوب نیست … از شلوغ یه میدون تجریش داره پول درمیاره .
باز م از ش خرید می‌کنم ، بهترین منطق ست .
اگه یه بار بری اونجا مشتری ش میشی .
برای ارسال رزومه به آدرس job@gmail.com میل بزنید .
کتابه رو تو فرهنگ‌سرا پیدا ش کردم .
در‌صورت مشکل به آیدی @bitianist پیام بدهید .
حاضر م شرط ببندم همون و ورداشتن تزیین کردن و برای ما اووردن !
آخه واقعا درسته این کار ؟ چرا خب درست نمی‌کنن ؟
'''.strip()

    tags_string = '''
V E N K O N C D A X O 
E N V J V J D V O 
D Z N Z V N C D A V O O 
N N D A V O E A C N N V N V O O 
D C E C N V O A N C O O 
J U N V D N C V O O 
E N N E N M N V O O 
N P N A A C V O O 
E N E N S N V O O 
A V N V Z J V N V J E Z V O O 
D D A T N O D D A V O
    '''.strip()

    '''
برید_V  به_E  رستوران_N  https://chilivery.com/tehran/restaurant۱/_K  ._O  غذا_N  ش_C  خیلی_D  عالیه_A  😍😍😍_X  
از‌نظر_E  قیمت_N  میارزه_N_V  ک_C_J  بری_V  ولی_J  واقعا_D  خفست_N_V  
مث_N_D  این_T_Z  جای_N  دیگه‌ای_N_Z  ندیدم_V  مشتری_N  اش_C  انقدر_D  زیاد_A  باشه_V  ._O  
کیفیت_N  پیتزاهاش_N  اصلن_N_D  خوب_A  نیست_V  …_O  از_E  شلوغ_A  یه_C  میدون_N  تجریش_N  داره_V  پول_N  درمیاره_N_V  ._O  
باز_D  م_C  از_E  ش_C  خرید_N  می‌کنم_V  ،_O  بهترین_A  منطق_N  ست_C  ._O  
اگه_J  یه_U  بار_N  بری_V  اونجا_D  مشتری_N  ش_C  میشی_A_V  ._O  
برای_E  ارسال_N  رزومه_N  به_E  آدرس_N  job@gmail.com_M  میل_N  بزنید_V  ._O  
کتابه_R_N  رو_N_P  تو_Z_N  فرهنگ‌سرا_A  پیدا_A  ش_C  کردم_V  ._O  
در‌صورت_E  مشکل_N  به_E  آیدی_N  @bitianist_S  پیام_N  بدهید_V  ._O  
حاضر_A  م_C_V  شرط_N  ببندم_V  همون_Z  و_J  ورداشتن_V  تزیین_N  کردن_V  و_J  برای_E  ما_Z  اووردن_V  !_O  
آخه_D  واقعا_D  درسته_D_A  این_T  کار_N  ؟_O  چرا_D  خب_D  درست_A  نمی‌کنن_V  ؟_O
    '''

    normal_text_content = normal_text_content.replace('\n', ' \\n ')
    normal_text_content = re.sub(' +', ' ', normal_text_content).strip()
    token_contents_tuple = normal_text_content.split(' ')

    tags_string = tags_string.replace('\n', ' ')
    tags_string = re.sub(' +', ' ', tags_string).strip()
    tags_string_tuple = tags_string.split(' ')


    logger.info(f'token_contents_tuple {len(token_contents_tuple)} : \n{token_contents_tuple}\n')
    logger.info(f'tags_string_tuple {len(tags_string_tuple)} : \n{tags_string_tuple}\n')

    tagged_tokens = zip(token_contents_tuple, tags_string_tuple)
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

def main():
    try:
        # import_tag_sets()
        # import_validators()
        import_normalizers()
        import_taggers()

        
        # import_bijankhan_data()
        # import_text_equivalents()
        # import_word_equivalents()

        # import_bitianist_text_tag('8f40d06e-aa29-46ed-8aed-82c942598be6')
        # import_bitianist_evaluate_text_tag()

        # import_tags()
        # import_translation_characters()
        # import_refinement_patterns()
    except Exception as e:
        logger.exception(e)

if __name__ == "__main__": main()




# # @utils.time_usage(logger)
# def read_bijankhan_xml_file(xml_file):
#     tagged_sentences = []
#     logger = utils.get_logger(logger_name='data_importer')
#     xml_string, token_content, tag_name, sentence_content = '', '', '', ''
#     tag, token, sentence, tagged_sentence = None, None, None, None
#     sentence_tokens = []
#     sentence_breaker_pattern = re.compile(r'[!\.\?⸮؟]')
#     # sentences_count = 0
#     try:
#         with open(xml_file, mode="r", encoding="utf-8") as xf:
#             file_name = os.path.basename(xml_file)
#             # logger.info(f'> Importing xml file "{file_name}"')
#             xml_string = xf.read()
#             tree = ET.ElementTree(ET.fromstring(xml_string))
#             root = tree.getroot()
#             for tagged_token_xml in root.findall('*'):
#                 token_content = tagged_token_xml.find('w').text.strip().replace(' ', '‌')
#                 sentence_content += token_content + ' '
#                 tag_name = tagged_token_xml.find('tag').text[0]
#                 tag = generate_tag_dictionary(name=tag_name)
#                 token = generate_tagged_token_dictionary(token_content, tag)
#                 sentence_tokens.append(token)
#                 if len(token_content) == 1 and sentence_breaker_pattern.search(token_content):
#                     sentence = generate_sentence_dictionary(sentence_content)
#                     tagged_sentence = generate_tagged_sentence_dictionary(
#                                 tokens=sentence_tokens,
#                                 tagger='bijankhan-manual-tagger', 
#                                 sentence=sentence)
#                     tagged_sentences.append(tagged_sentence)
#                     # sentences_count += 1
#                     sentence_content = ''
#                     sentence_tokens = []
#                     # if sentences_count % 25 == 0:
#                         # logger.info(f'> File {file_name} now has {sentences_count} imported sentence ...')

#             logger.info(f'> File {file_name} has {len(tagged_sentences)} sentences.')
#             return tagged_sentences
#     except IOError as exc:
#         if exc.errno != errno.EISDIR:
#             logger.exception(exc)

# # @utils.time_usage(logger)
# def send_bijankhan_tagged_sentence(tagged_sentence):
#     response, error = post(tagged_sentences_url, tagged_sentence)
#     if error:
#         return

# @utils.time_usage(logger)
# def import_bijankhan_data():
#     # global tagged_sentences, tagged_tokens, token_set, word_set, tag_example_dic
#     logger.info(f'>> Reading bijankhan data')
#     files = glob.glob(fr'{bijankhan_data_dir}/*.xml')
#     tagged_sentences, tagged_sentences_list = [], []
#     # files = files[0:1]
#     # num_cores = multiprocessing.cpu_count()
#     # logger.info(f'> Number of cup cores : {num_cores}')
#     # tagged_sentences.extend(
#     tagged_sentences_list = Parallel(n_jobs=-1, verbose=20)(delayed(read_bijankhan_xml_file)(xml_file) for xml_file in files)
#     # )
#     for current_tagged_sentences in tagged_sentences_list:
#         tagged_sentences.extend(current_tagged_sentences)
#     logger.info(f'>> Total {len(tagged_sentences)} sentences added.')
    
#     Parallel(n_jobs=24, verbose=20, backend='threading')(delayed(send_bijankhan_tagged_sentence)(tagged_sentence) for tagged_sentence in tagged_sentences)
    
#     logger.info(f'>> {len(tagged_sentences)} sentences imported.')



# def import_tags():
#     """ 
#     https://htmlcolorcodes.com/
#     """
#     tags = (
#         ('E', 'E', '#E74C3C'),
#         ('N', 'اسم', '#3498DB'),
#         ('V', 'فعل', '#9B59B6'),

#         ('J', 'J', '#1ABC9C'),
#         ('A', 'صفت', '#F1C40F'),
#         ('U', 'عدد', '#E67E22'),
        
#         ('T', 'T', '#ECF0F1'),
#         ('Z', 'ضمیر', '#BDC3C7'),
#         ('O', 'علامت', '#7F8C8D'),
        
#         ('L', 'L', '#34495E'),
#         ('P', 'حرف اضافه پسین', '#C39BD3'),
#         ('D', 'قید', '#FBFCFC'),
        
#         ('C', 'C', '#0E6655'),
#         ('R', 'R', '#922B21'),
#         ('I', 'حرف ندا', '#AED6F1'),

#     )
#     for tag_data in tags:
#         tag = generate_tag_dictionary(tag_data[0])
#         response, error = post(tag_url, tag)
#         if error:
#             continue

# def import_translation_characters():
#     translation_characters = (
#         # (r' ', r' ', 'space character 160 -> 32', 'hazm', 'true'),
#         # (r'ك', r'ک', '', 'hazm', 'true'),
#         # (r'ي', r'ی', '', 'hazm', 'true'),
#         # (r'“', r'\"', '', 'hazm', 'true'),
#         # (r'”', r'\"', '', 'hazm', 'true'),
#         # (r'0', r'۰', '', 'hazm', 'true'),
#         # (r'1', r'۱', '', 'hazm', 'true'),
#         # (r'2', r'۲', '', 'hazm', 'true'),
#         # (r'3', r'۳', '', 'hazm', 'true'),
#         # (r'4', r'۴', '', 'hazm', 'true'),
#         # (r'5', r'۵', '', 'hazm', 'true'),
#         # (r'6', r'۶', '', 'hazm', 'true'),
#         # (r'7', r'۷', '', 'hazm', 'true'),
#         # (r'8', r'۸', '', 'hazm', 'true'),
#         # (r'9', r'۹', '', 'hazm', 'true'),
#         # (r'%', r'٪', '', 'hazm', 'true'),
#         (r'?', r'؟', '', 'hazm', 'true'),
#     )
#     url = 'http://127.0.0.1:8000/mohaverekhan/api/rules/translation_character/'
#     for translation_character in translation_characters:
#         data = f'''
# {{
#     "source": "{translation_character[0]}",
#     "destination": "{translation_character[1]}",
#     "description": "{translation_character[2]}",
#     "owner": "{translation_character[3]}",
#     "is_valid": {translation_character[4]}
# }}'''
#         response, error = post(url, data)
#         if error:
#             continue
#         # response = requests.post(url, data=data.encode('utf-8'), headers={'Content-type': 'application/json; charset=utf-8'})
#         # if response.status_code != 200 and response.status_code != 201:
#         #     logger.info(f'> Error : {response.status_code} {response.text}')
#         #     response.raise_for_status()
#         #     break
#         # logger.info(f'{response.status_code} : {response.text}')

# def import_refinement_patterns():
#     punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
#     refinement_patterns = (
#         (r'\.{4,}', r'.', 'replace more than 3 dots with 1 dot', 0, 'bitianist', 'true'),
#         (r'( \.{2})|(\.{2} )', r' . ', 'replace exactly 2 dots with 1 dot', 0, 'bitianist', 'true'),
#         (r' ?\.\.\.', r' …', 'replace 3 dots', 0, 'hazm', 'true'),
#         (r'(.)\1{1,}', r'\1', 'remove repetitions', 0, 'bitianist', 'true'),
#         (r'[ـ\r]', r'', 'remove keshide', 0, 'hazm', 'true'),
#         (r'[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652]', r'', 'remove FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN', 0, 'hazm', 'true'),
#         (r'"([^\n"]+)"', r'«\1»', 'replace quotation with gyoome', 0, 'hazm', 'true'),
#         (rf'([{punctuations}])', r' \1 ', 'add extra space before and after of punctuations', 0, 'bitianist', 'true'),
#         (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
#         (r'\n+', r'\n', 'remove extra newlines', 0, 'bitianist', 'true'),
#         (r'([^ ]ه) ی ', r'\1‌ی ', 'before ی - replace space with non-joiner ', 0, 'hazm', 'true'),
#         (r'(^| )(ن?می) ', r'\1\2‌', 'after می،نمی - replace space with non-joiner ', 0, 'hazm', 'true'),
#         (rf'(?<=[^\n\d {punctuations}]{2}) (تر(ین?)?|گری?|های?)(?=[ \n{punctuations}]|$)', r'‌\1', 'before تر, تری, ترین, گر, گری, ها, های - replace space with non-joiner', 0, 'hazm', 'true'),
#         (rf'([^ ]ه) (ا(م|یم|ش|ند|ی|ید|ت))(?=[ \n{punctuations}]|$)', r'\1‌\2', 'before ام, ایم, اش, اند, ای, اید, ات - replace space with non-joiner', 0, 'hazm', 'true'),  
#         # (r'', r'', '', 0, 'hazm', 'true'),
#         # (r'', r'', '', 0, 'hazm', 'true'),
#         # (r'', r'', '', 0, 'hazm', 'true'),
#         # (r'', r'', '', 0, 'hazm', 'true'),
#         # (r'', r'', '', 0, 'hazm', 'true'),
#         # (r'', r'', '', 0, 'hazm', 'true'),
#     )
#     for refinement_pattern_data in refinement_patterns:
#         refinement_pattern = generate_refinement_pattern_dictionary(
#             pattern=refinement_pattern_data[0],
#             replacement=refinement_pattern_data[1],
#             description=refinement_pattern_data[2],
#             order=refinement_pattern_data[3],
#             owner=refinement_pattern_data[4],
#             is_valid=refinement_pattern_data[5]
#         )
     
#         response, error = post(refinement_pattern_url, refinement_pattern)
#         if error:
#             return




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
#                 token = generate_tagged_token_dictionary(token_content, tag)
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

# def generate_sentence_dictionary(content, text=None, id=None):
#     d = {}
#     d['content'] = content
#     if text:
#         d['text'] = text 
#     if id:
#         d['id'] = id 
#     return d






# def generate_normal_sentence_dictionary(content, normalizer, 
#         sentence, id=None):
#     d = {}
#     d['content'] = content
#     d['normalizer'] = normalizer
#     d['sentence'] = sentence
#     if id:
#         d['id'] = id 
#     return d



# def generate_tagged_sentence_dictionary(tokens, tagger, 
#         sentence, id=None):
#     d = {}
#     d['tokens'] = tokens
#     d['tagger'] = tagger
#     d['sentence'] = sentence
#     if id:
#         d['id'] = id 
#     return d

# def generate_translation_character_dictionary(source, destination, owner=None, 
#                                                     is_valid=False, description=None,):
#     d = {}
#     d['source'] = source
#     d['destination'] = destination
#     d['is_valid'] = is_valid
#     if description is not None:
#         d['description'] = description   
#     if owner is not None:
#         d['owner'] = owner    
#     return d

# def generate_refinement_pattern_dictionary(pattern, replacement, order=9999, owner=None, 
#                                                 is_valid=False, description=None):
#     d = {}
#     d['pattern'] = pattern
#     d['replacement'] = replacement
#     d['order'] = order
#     d['is_valid'] = is_valid
#     if description is not None:
#         d['description'] = description   
#     if owner is not None:
#         d['owner'] = owner    
#     return d

# tags_tuple = ('V', 'E', 'N', 'K', 'O', 'N', 'C', 'D')
#     tokens = [
# #برید_V     به_E     رستوران_N     https://chilivery.com/tehran/restaurant۱/_K     ._O     غذا_N     ش_C     خیلی_D     عالی_A     ه_C     😍😍😍_X             
#         generate_tagged_token_dictionary('برید', generate_tag_dictionary(name='A')),
#         generate_tagged_token_dictionary('به', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('رستوران', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('https://chilivery.com/tehran/restaurant۱/', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('غذا', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('خیلی', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('عالی', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('😍😍😍', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# # از‌نظر_E     قیمت_N     میارزه_N     ک_C     بری_V     ولی_J     واقعا_D     خف_N     ست_C                 
#         generate_tagged_token_dictionary('از‌نظر', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('قیمت', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('میارزه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ک', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('بری', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ولی', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('واقعا', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('خف', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ست', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# # مث_N     این_T     جای_N     دیگه‌ای_N     ندیدم_V     مشتریاش_N     انقدر_D     زیاد_A     باشه_V     ._O                 
#         generate_tagged_token_dictionary('مث', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('این', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('جای', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('دیگه‌ای', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ندیدم', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('مشتریاش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('انقدر', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('زیاد', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('باشه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# # کیفیت_N  پیتزاها_N  ش_C  اصلن_N  خوب_A  نیست_V  …_O  از_E  شلوغی_N  میدون_N  تجریش_N  داره_V  پول_N  در_E  میاره_V  ._O     
#         generate_tagged_token_dictionary('کیفیت', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('پیتزاها', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('اصلن', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('خوب', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('نیست', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('…', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('از', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('شلوغی', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('میدون', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('تجریش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('داره', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('پول', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('درمیاره', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# # باز_A  م_C  از_E  ش_C  خرید_N  می‌کنم_V  ،_O  بهترین_A  منطق_N  ست_C  ._O  
#         generate_tagged_token_dictionary('باز', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('م', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('از', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('خرید', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('می‌کنم', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('بهترین', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('منطق', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ست', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #اگه_J  یه_U  بار_N  بری_V  اونجا_D  مشتری_N  ش_C  میشی_A  ._O  
#         generate_tagged_token_dictionary('اگه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('یه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('بار', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('بری', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('اونجا', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('مشتری', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ش', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('میشی', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #برای_E  ارسال_N  رزومه_N  به_E  آدرس_N  job@gmail.com_M  میل_N  بزنید_V  ._O           
#         generate_tagged_token_dictionary('برای', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ارسال', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('رزومه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('به', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('آدرس', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('job@gmail.com', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('میل', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('بزنید', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('.', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #کتاب_N  ه_C  رو_P  تو_N  فرهنگ‌سرا_A  پیدا_A  ش_C  کردم_V  ._O           
#         generate_tagged_token_dictionary('کتاب', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('ه', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('رو', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #در‌صورت_E  مشکل_N  به_E  آیدی_N  @bitianist_S  پیام_N  بدهید_V  ._O  
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #حاضر_A  م_C  شرط_N  بند_N  م_C  همون_Z  و_J  ورداشتن_V  تزیین_N  کردن_V  و_J  برای_E  ما_Z  اووردن_V  !_O              
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('', generate_tag_dictionary(name='N')),
#         generate_tagged_token_dictionary('\\n', generate_tag_dictionary(name='N')),
# #آخه_D  واقعا_D  درست_A  ه_C  اینکار_N  ؟_O  چرا_D  خوب_D  درست_A  نمی‌کنن_V  ؟_O            
#     ]