import logging
import random
import re
from django.apps import apps
import time

repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")
# debug_pattern = re.compile(r'[0-9۰۱۲۳۴۵۶۷۸۹]')
# debug_pattern = re.compile(r'^گرون$|^میدون$|^خونه$|^نون$|^ارزون$|^اون$|^قلیون$')
# debug_pattern = re.compile(r'هایمان')
debug_pattern = re.compile(r'^کنده$')

logger = None
# Word, WordNormal, Text, TextNormal = None, None, None, None
# TextTag, TagSet, Tag, Validator = None, None, None, None
# Normalizer, Tagger = None, None, None
normalizers = {}
validators = {}
taggers = {}
token_set = set()
repetition_word_set = set()
compile_patterns = lambda patterns: [(re.compile(pattern), repl) for pattern, repl in patterns]
punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
numbers = r'۰۱۲۳۴۵۶۷۸۹'
persians = 'اآب‌پتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
link = r'((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)'
emoji = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+'
email = r'[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}'
id = r'([^\w\._]*)(@[\w_]+)([\S]+)'
tag = r'\#([\S]+)'
# def cache_models():
#     global Word, WordNormal, Text, TextNormal
#     global TextTag, TagSet, Tag, Validator
#     global Normalizer, Tagger
#     Word = apps.get_model(app_label='mohaverekhan', model_name='Word')
#     WordNormal = apps.get_model(app_label='mohaverekhan', model_name='WordNormal')
#     Text = apps.get_model(app_label='mohaverekhan', model_name='Text')
#     TextNormal = apps.get_model(app_label='mohaverekhan', model_name='TextNormal')
#     TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
#     TagSet = apps.get_model(app_label='mohaverekhan', model_name='TagSet')
#     Tag = apps.get_model(app_label='mohaverekhan', model_name='Tag')
#     Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')
#     Normalizer = apps.get_model(app_label='mohaverekhan', model_name='Normalizer')
#     Tagger = apps.get_model(app_label='mohaverekhan', model_name='Tagger')
tag_set_token_tags = dict()
all_token_tags = dict()

def cache_token_tags_dic():
    global tag_set_token_tags, all_token_tags, repetition_word_set
    temp_tag_set_token_tags = {}
    temp_all_token_tags = {}
    temp_repetition_word_set = set()
    token_content, tag_name = '', ''
    TokenTag = apps.get_model(app_label='mohaverekhan', model_name='TokenTag')
    TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
    text_tag_list = TextTag.objects.filter(is_valid=True).values_list('tagger__tag_set__name', 'tagged_tokens')
    if text_tag_list.count() == 0:
        return
    before, after = '', ''
    logger.info(f'> Looking for {debug_pattern}')
    tag_set_name = ''
    tagged_tokens = None
    for text_tag in text_tag_list:
        tag_set_name = text_tag[0]
        tagged_tokens = text_tag[1]
        for index, tagged_token in enumerate(tagged_tokens):
            token_content = tagged_token['token']
            tag_name = tagged_token['tag']['name']

            if debug_pattern.search(token_content):
                # if tag_name != 'U':
                if index - 1 >= 0:
                    before = tagged_tokens[index-1]['token']
                else:
                    before = '^'

                if index + 1 < len(tagged_tokens):
                    after = tagged_tokens[index+1]['token']
                else:
                    after = '$'

                logger.info(f'> Token A {after} A    B {token_content} B    C {before} C has tag [{tag_name}]')
            # if tag_name not in ('O', 'U'):
            # token_set.add(token_content)
            token_tags = temp_tag_set_token_tags.get(tag_set_name, {})
            tag_counts = token_tags.get(token_content, {})
            tag_count = tag_counts.get(tag_name, 0)
            tag_counts[tag_name] = tag_count + 1
            token_tags[token_content] = tag_counts
            temp_tag_set_token_tags[tag_set_name] = token_tags
                # token_tags.append(tag_name)
                # token_tags_dic[token_content] = token_tags

    # token_set.remove('دیگهای')
    del temp_tag_set_token_tags['bijankhan-tag-set']['دیگهای']

    #Remove ه in عالیه درسته کتابه زیاده
    # old_token_set = set(token_set)
    # got_tokens = set()
    # for token in old_token_set: 
    #     if token not in got_tokens and token[-1] == 'ه' and token[0:-1] in token_set:
    #         self_score = max([value for key, value in token_tags_dic[token].items()])
    #         main_token_score = max([value for key, value in token_tags_dic[token[0:-1]].items()])
    #         # logger.info(f'> {token} {self_score} {main_token_score}')
    #         if self_score > 20 or main_token_score < 200:
    #             continue
    #         got_tokens.add(token)
    #         logger.info(f'>> D : {token} {token_tags_dic[token]} {token_tags_dic[token[0:-1]]}')
    #         # token_set.remove(token)

    # removed_tokens = [
    #     'واحده', 'کتابه', 'عالیه', 'درسته', 'زیاده', 'مثبته',
    #     'ضروریه', 'منه', 'قابله', 'مثله', 'حرفه', 'مختلفه',
    #     'اسلامیه', 'اصله', 'مالیه', 'قتله', 'عمله', 'موجبه',
    #     '', '', '', '', '', '', '', '', 
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    # ]
    # token_set.remove('واحده')
    # token_set.remove('کتابه')
    # token_set.remove('عالیه')
    # token_set.remove('درسته')
    # token_set.remove('زیاده')

    # if 'زیاده' in token_set:
    #     logger.error(f"> Can't remove زیاده کتابه درسته عالیه ...")
    
    logger.info(f'> len(temp_tag_set_token_tags) : {len(temp_tag_set_token_tags)}')
    logger.info(f'>>> Random samples')
    for tag_set, token_tags in temp_tag_set_token_tags.items():
        logger.info(f'>> tag_set : {tag_set}')
        for token in random.sample(list(token_tags), min(len(token_tags), 25)):
            logger.info(f'> {token} : {token_tags[token]}')

    
    [temp_all_token_tags.update(token_tags) for token_tags in temp_tag_set_token_tags.values()]
    # logger.info(f'> token_tags_dic samples : {set(random.sample(list(token_tags_dic), 20)) }')
    for token in temp_all_token_tags:
        if repetition_pattern.search(token):
            temp_repetition_word_set.add(token)
    # for repetition_word in temp_repetition_word_set:
    #     # logger.info(f'> repetition_word : {repetition_word}')
    #     fuck = repetition_pattern.sub(r'\1', repetition_word)
        
    #     # logger.info(f'> fuck : {fuck}')
    #     fuck1 = fuck + 'ه'
    #     fuck2 = fuck + 'و'
    #     fuck3 = fuck + 'ی'
    #     fuck4 = fuck + 'ا'

    #     if fuck1 != repetition_word and fuck1 in token_set:
    #         logger.info(f'> Fuckkkking1 : {repetition_word} - {fuck} - {fuck1}')
    #     if fuck2 != repetition_word and fuck2 in token_set:
    #         logger.info(f'> Fuckkkking2 : {repetition_word} - {fuck} - {fuck2}')
    #     if fuck3 != repetition_word and fuck3 in token_set:
    #         logger.info(f'> Fuckkkking3 : {repetition_word} - {fuck} - {fuck3}')
    #     if fuck4 != repetition_word and fuck4 in token_set:
    #         logger.info(f'> Fuckkkking4 : {repetition_word} - {fuck} - {fuck4}')
    if len(temp_repetition_word_set) != 0:
        logger.info(f'> len(temp_repetition_word_set) : {len(temp_repetition_word_set)}')
        logger.info(f'> temp_repetition_word_set samples: {set(random.sample(temp_repetition_word_set, min(len(temp_repetition_word_set), 100)))}')

    tag_set_token_tags = temp_tag_set_token_tags
    all_token_tags = temp_all_token_tags
    repetition_word_set = temp_repetition_word_set
    # logger.info(f'> debug_pattern : {debug_pattern}')
    # for token in token_set:
    #     if debug_pattern.search(token):
    #         logger.info(token)
    # tokens = TaggedSentence.objects.only('tokens__content').order_by('-tokens__content').distinct('tokens__content')
    # logger.info(f'tokens.count() : {tokens.count()}')

# bitianist_validator = None


# def cache_bitianist_validator():
#     global bitianist_validator
#     Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')
#     bitianist_validator = Validator.objects.filter(name='bitianist-validator').first()
#     if not bitianist_validator:
#         logger.error("> There isn't bitianist-validator!")

def cache_validators():
    Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')

    validators['bitianist-validator'] = Validator.objects.filter(
        name='bitianist-validator').first()

    logger.info(f'>> Cached validators : {list(validators.keys())}')

def cache_normalizers():
    BitianistInformalRefinementNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistInformalRefinementNormalizer')
    BitianistInformalReplacementNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistInformalReplacementNormalizer')
    BitianistInformalSeq2SeqNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistInformalSeq2SeqNormalizer')

    normalizers['bitianist-informal-refinement-normalizer'] = BitianistInformalRefinementNormalizer.objects.filter(
        name='bitianist-informal-refinement-normalizer').first()

    normalizers['bitianist-informal-replacement-normalizer'] = BitianistInformalReplacementNormalizer.objects.filter(
        name='bitianist-informal-replacement-normalizer').first()

    normalizers['bitianist-informal-seq2seq-normalizer'] = BitianistInformalSeq2SeqNormalizer.objects.filter(
        name='bitianist-informal-seq2seq-normalizer').first()
    
    logger.info(f'>> Cached normalizers : {list(normalizers.keys())}')

def cache_taggers():
    BitianistFormalNLTKTagger = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistFormalNLTKTagger')
    BitianistInformalNLTKTagger = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistInformalNLTKTagger')

    taggers['bitianist-formal-nltk-tagger'] = BitianistFormalNLTKTagger.objects.filter(
        name='bitianist-formal-nltk-tagger').first()

    taggers['bitianist-informal-nltk-tagger'] = BitianistInformalNLTKTagger.objects.filter(
        name='bitianist-informal-nltk-tagger').first()
    
    logger.info(f'>> Cached taggers : {list(taggers.keys())}')



def init():
    global logger
    logger = logging.getLogger(__name__)
    # cache_bitianist_validator()
    # cache_models()

    cache_validators()
    cache_normalizers()
    cache_taggers()

    cache_token_tags_dic()