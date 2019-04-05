import logging
import random
import re
from django.apps import apps

repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")
# debug_pattern = re.compile(r'[0-9۰۱۲۳۴۵۶۷۸۹]')
# debug_pattern = re.compile(r'^گرون$|^میدون$|^خونه$|^نون$|^ارزون$|^اون$|^قلیون$')
# debug_pattern = re.compile(r'هایمان')
debug_pattern = re.compile(r'باید|دنبال')

logger = None
# Word, WordNormal, Text, TextNormal = None, None, None, None
# TextTag, TagSet, Tag, Validator = None, None, None, None
# Normalizer, Tokenizer, Tagger = None, None, None
normalizers = {}
validators = {}
tokenizers = {}
taggers = {}
token_set = set()
repetition_word_set = set()
compile_patterns = lambda patterns: [(re.compile(pattern), repl) for pattern, repl in patterns]

# def cache_models():
#     global Word, WordNormal, Text, TextNormal
#     global TextTag, TagSet, Tag, Validator
#     global Normalizer, Tokenizer, Tagger
#     Word = apps.get_model(app_label='mohaverekhan', model_name='Word')
#     WordNormal = apps.get_model(app_label='mohaverekhan', model_name='WordNormal')
#     Text = apps.get_model(app_label='mohaverekhan', model_name='Text')
#     TextNormal = apps.get_model(app_label='mohaverekhan', model_name='TextNormal')
#     TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
#     TagSet = apps.get_model(app_label='mohaverekhan', model_name='TagSet')
#     Tag = apps.get_model(app_label='mohaverekhan', model_name='Tag')
#     Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')
#     Normalizer = apps.get_model(app_label='mohaverekhan', model_name='Normalizer')
#     Tokenizer = apps.get_model(app_label='mohaverekhan', model_name='Tokenizer')
#     Tagger = apps.get_model(app_label='mohaverekhan', model_name='Tagger')

def cache_tokens():
    token_content, tag_name = '', ''
    TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
    text_tokens_list = TextTag.objects.filter(is_valid=True).values_list('tokens', flat=True)
    if text_tokens_list.count() == 0:
        return
    for text_tokens in text_tokens_list:
        for token in text_tokens:
            token_content = token['content']
            tag_name = token['tag']['name']
            if debug_pattern.search(token_content):
                # if tag_name != 'U':
                logger.info(f'> Token [{token_content}] has tag [{tag_name}]')
            if tag_name not in ('O', 'U'):
                token_set.add(token_content)
    logger.info(f'> len(token_set) : {len(token_set)}')
    logger.info(f'> token_set samples : {set(random.sample(token_set, 20)) }')
    for token in token_set:
        if repetition_pattern.search(token):
            repetition_word_set.add(token)
    if len(repetition_word_set) != 0:
        logger.info(f'> len(repetition_word_set) : {len(repetition_word_set)}')
        logger.info(f'> repetition_word_set samples: {set(random.sample(repetition_word_set, min(len(repetition_word_set), 100)))}')


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
    RefinementNormalizer = apps.get_model(app_label='mohaverekhan', model_name='RefinementNormalizer')
    ReplacementNormalizer = apps.get_model(app_label='mohaverekhan', model_name='ReplacementNormalizer')

    normalizers['refinement-normalizer'] = RefinementNormalizer.objects.filter(
        name='refinement-normalizer').first()

    normalizers['replacement-normalizer'] = ReplacementNormalizer.objects.filter(
        name='replacement-normalizer').first()
    
    logger.info(f'>> Cached normalizers : {list(normalizers.keys())}')

def cache_tokenizers():
    BitianistTokenizer = apps.get_model(app_label='mohaverekhan', model_name='BitianistTokenizer')

    tokenizers['bitianist-tokenizer'] = BitianistTokenizer.objects.filter(
        name='bitianist-tokenizer').first()

    logger.info(f'>> Cached tokenizers : {list(tokenizers.keys())}')

def cache_taggers():
    FormalTagger = apps.get_model(app_label='mohaverekhan', model_name='FormalTagger')
    InformalTagger = apps.get_model(app_label='mohaverekhan', model_name='InformalTagger')

    taggers['formal-tagger'] = FormalTagger.objects.filter(
        name='formal-tagger').first()

    taggers['informal-tagger'] = InformalTagger.objects.filter(
        name='informal-tagger').first()
    
    logger.info(f'>> Cached taggers : {list(taggers.keys())}')



def init():
    global logger
    logger = logging.getLogger(__name__)
    # cache_bitianist_validator()
    # cache_models()
    cache_validators()
    cache_normalizers()
    cache_tokenizers()
    cache_taggers()
    cache_tokens()