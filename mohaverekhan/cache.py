from django.apps import apps
import logging
import random
import re
repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")
# debug_pattern = re.compile(r'[0-9۰۱۲۳۴۵۶۷۸۹]')
# debug_pattern = re.compile(r'^گرون$|^میدون$|^خونه$|^نون$|^ارزون$|^اون$|^قلیون$')
# debug_pattern = re.compile(r'هایمان')
debug_pattern = re.compile(r'باید|دنبال')

logger = None
normalizers = {}
validators = {}
tokenizers = {}
taggers = {}
token_set = set()
repetition_word_set = set()

def cache_tokens():
    # tokens = set()
    TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
    # tokens = TaggedSentence.objects.only('tokens__content')
    token_content, tag_name = '', ''
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

bitianist_validator = None

def cache_bitianist_validator():
    global bitianist_validator
    Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')
    q = Validator.objects.filter(name='bitianist-validator')
    if q:
        bitianist_validator = q.first()
    else:
        logger.error("> There isn't bitianist-validator!")

def cache_validators():
    global validators
    Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')

    q = Validator.objects.filter(name='bitianist-validator')
    if q:
        validators['bitianist-validator'] = q.first()

    logger.info(f'>> Cached validators : {list(validators.keys)}')

def cache_normalizers():
    global normalizers
    RefinementNormalizer = apps.get_model(app_label='mohaverekhan', model_name='RefinementNormalizer')
    ReplacementNormalizer = apps.get_model(app_label='mohaverekhan', model_name='ReplacementNormalizer')

    q = RefinementNormalizer.objects.filter(name='refinement-normalizer')
    if q:
        normalizers['refinement-normalizer'] = q.first()

    q = ReplacementNormalizer.objects.filter(name='replacement-normalizer')
    if q:
        normalizers['replacement-normalizer'] = q.first()
    
    logger.info(f'>> Cached normalizers : {list(normalizers.keys)}')

def cache_tokenizers():
    global tokenizers
    BitianistTokenizer = apps.get_model(app_label='mohaverekhan', model_name='BitianistTokenizer')

    q = BitianistTokenizer.objects.filter(name='bitianist-tokenizer')
    if q:
        tokenizers['bitianist-tokenizer'] = q.first()

    logger.info(f'>> Cached tokenizers : {list(tokenizers.keys)}')

def cache_taggers():
    global taggers
    FormalTagger = apps.get_model(app_label='mohaverekhan', model_name='FormalTagger')
    InformalTagger = apps.get_model(app_label='mohaverekhan', model_name='InformalTagger')

    q = FormalTagger.objects.filter(name='formal-tagger')
    if q:
        taggers['formal-tagger'] = q.first()

    q = InformalTagger.objects.filter(name='informal-tagger')
    if q:
        taggers['informal-tagger'] = q.first()
    
    logger.info(f'>> Cached taggers : {list(taggers.keys)}')


def init():
    global logger
    logger = logging.getLogger(__name__)
    # cache_bitianist_validator()
    cache_validators()
    cache_normalizers()
    cache_tokenizers()
    cache_taggers()
    cache_tokens()