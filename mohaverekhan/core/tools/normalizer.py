import re
from hazm import *
from . import utils
from mohaverekhan.core.data import data
from django.apps import apps

TRANSLATION_CHARACTER_DIC, REFINEMENT_PATTERNS = None, None

compile_patterns = lambda patterns: [(re.compile(pattern), repl) for pattern, repl in patterns]
logger = utils.get_logger(logger_name='normilizer')
logger.info('-------------------------------------------------------------------')

normalizer = Normalizer()

def uniform_signs(text):
    logger.info(f'>> Refine text : {text}')
    text = text.translate(text.maketrans(TRANSLATION_CHARACTER_DIC))
    logger.info(f'> after : {text}')
    return text

def refine_text(text):
    logger.info(f'>> Refine text : {text}')
    
    for pattern, replacement in REFINEMENT_PATTERNS:
        logger.info(f'> before {pattern} -> {replacement}')
        text = pattern.sub(replacement, text)
        logger.info(f'> after : {text}')
    return text

def normalize(text):
    logger.info(f'>> Normalize : {text}')
    text = uniform_signs(text)
    # text = refine_text(text, refinement_patterns)
    logger.info(f'>> Result : {text}')
    # text = normalizer.normalize(text)
    return text

def set_translation_character_dic():
    global TRANSLATION_CHARACTER_DIC
    TranslationCharacter = apps.get_model(app_label='mohaverekhan', model_name='TranslationCharacter')
    TRANSLATION_CHARACTER_DIC = dict(TranslationCharacter.objects.values_list('source', 'destination'))
    # translation_characters = TranslationCharacter.objects.all()
    # TRANSLATION_CHARACTER_DIC = {translation_character.source:translation_character.destination for translation_character in translation_characters}
    logger.info(f'> TRANSLATION_CHARACTER_DIC : {TRANSLATION_CHARACTER_DIC}')

def set_refinement_patterns():
    global REFINEMENT_PATTERNS
    RefinementPattern = apps.get_model(app_label='mohaverekhan', model_name='RefinementPattern')
    REFINEMENT_PATTERNS = RefinementPattern.objects.values_list('pattern', 'replacement')
    # REFINEMENT_PATTERNS = RefinementPattern.objects.all()
    # REFINEMENT_PATTERNS = [(refinement_pattern.pattern, refinement_pattern.replacement) for refinement_pattern in REFINEMENT_PATTERNS]
    logger.info(f'> REFINEMENT_PATTERNS : {REFINEMENT_PATTERNS}')
    REFINEMENT_PATTERNS = compile_patterns(REFINEMENT_PATTERNS)
    logger.info(f'> REFINEMENT_PATTERNS compiled : {REFINEMENT_PATTERNS}')

def do_samples():
    sample1 = '''
من از قدیییییم مشتریشون بودم.
سالها پیش که اول اسمش ذن بود و بعد شد خانه آسیایی. اون موقع هم سوشی ها و هم ساشیمی های عااااالی ای داشت.
پیش غذا هم همیشه میسو سوپ میخوردم.
از نظر توضیحاتی هم که در مورد غذا ها میدادن فوق‌العاده بود. الان فرصت ندارم ولی دوس دارم حتما باز هم برم
'''
    logger.info(f'\n>> Test\n\nInput : \n{sample1}\n\nOutput : \n{normalize(sample1)}\n\n')

    sample2 = '0123456789 كي“”%'
    logger.info(f'\n>> Test\n\nInput : \n{sample2}\n\nOutput : \n{normalize(sample2)}\n\n')

def init():
    set_translation_character_dic()
    set_refinement_patterns()
    do_samples()

"""
<tok><w>یادداشتها</w><tag>Nclp---</tag></tok>
<tok><w>یت</w><tag>Cez--nstv</tag></tok>
<tok><w>شده است</w><tag>Vpysshsf---</tag></tok>
<tok><w>رودخانه ای</w><tag>Ncspk-y</tag></tok>
<tok><w>انسانهای</w><tag>Nclp--z</tag></tok>
<tok><w>آن چنان</w><tag>Dgps---</tag></tok>
<tok><w>بین المللی</w><tag>Apsz</tag></tok>
<tok><w>خوش آمدگویی</w><tag>Ncsp---</tag></tok>
"""
