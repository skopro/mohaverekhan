from __future__ import unicode_literals
import os
import nltk
from nltk.tag import brill, brill_trainer 
# from hazm import *
from pickle import dump, load
from mohaverekhan import utils

logger = utils.get_logger(logger_name='nltk_taggers')
logger.info('-------------------------------------------------------------------')

punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
numbers = r'۰۱۲۳۴۵۶۷۸۹'
persians = 'اآب‌پتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'

"""
Emoji => X
ID => S
Link => K
Email => M
Tag => G
"""
WORD_PATTERNS = [
    (r'^-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?$', 'U'),
    (r'^[\.:!،؛؟»\]\)\}«\[\(\{\'\"…#+*,$@]+$', 'O'),
    (rf'^بی‌[{persians}]+$|^بی [{persians}]+$', 'A'),
    (r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+$', 'X'), #hazm emoticons - symbols & pictographs - pushpin & round pushpin
    (r'^([^\w\._]*)(@[\w_]+).*$', 'S'), #hazm
    (r'^((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)$', 'K'), #hazm forgot "="? lol
    (r'^[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}$', 'M'), #hazm
    (r'^\#([\S]+)$', 'G'),
    # (r'.*ed$', 'VBD'),
    # (r'.*ness$', 'NN'),
    # (r'.*ment$', 'NN'),
    # (r'.*ful$', 'JJ'),
    # (r'.*ious$', 'JJ'),
    # (r'.*ble$', 'JJ'),
    # (r'.*ic$', 'JJ'),
    # (r'.*ive$', 'JJ'),
    # (r'.*ic$', 'JJ'),
    # (r'.*est$', 'JJ'),
    # (r'^a$', 'PREP'),
]

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

MAIN_TAGGER_PATH = os.path.join(CURRENT_PATH, 'nltk_main_tagger.pkl')
MAIN_TAGGER = None

def save_trained_main_tagger():
    logger.info(f'>> Trying to save main tagger in "{MAIN_TAGGER_PATH}"')
    global MAIN_TAGGER
    output = open(MAIN_TAGGER_PATH, 'wb')
    dump(MAIN_TAGGER, output, -1)
    output.close()

def load_trained_main_tagger():
    logger.info(f'>> Trying to load main tagger from "{MAIN_TAGGER_PATH}"')
    global MAIN_TAGGER
    input = open(MAIN_TAGGER_PATH, 'rb')
    MAIN_TAGGER = load(input)
    input.close()

def separate_train_and_test_data(data):
    logger.info('>> Separate train and test data')
    logger.info(f'len(data) : {len(data)}')
    size = int(len(data) * 0.9)
    train_data = data[:size]
    test_data = data[size:]
    logger.info(f'len(train_data) : {len(train_data)}')
    logger.info(f'len(test_data) : {len(test_data)}')

    return train_data, test_data
    
def create_main_tagger(train_data, test_data):
    logger.info('>> Create main tagger')
    default_tagger = nltk.DefaultTagger('N')
    # default_tagger = nltk.DefaultTagger('UNK')
    suffix_tagger = nltk.AffixTagger(train_data, backoff=default_tagger, affix_length=-3, min_stem_length=2, verbose=True)
    # suffix_tagger = nltk.AffixTagger(train_data, affix_length=-3, min_stem_length=2, verbose=True)
    affix_tagger = nltk.AffixTagger(train_data, backoff=suffix_tagger, affix_length=5, min_stem_length=1, verbose=True)
    regexp_tagger = nltk.RegexpTagger(WORD_PATTERNS, backoff=affix_tagger)
    unigram_tagger = nltk.UnigramTagger(train_data, backoff=regexp_tagger, verbose=True)
    bigram_tagger = nltk.BigramTagger(train_data, backoff=unigram_tagger, verbose=True)
    trigram_tagger = nltk.TrigramTagger(train_data, backoff=bigram_tagger, verbose=True)
    # main_tagger = trigram_tagger

    # affix_tagger = nltk.AffixTagger(train_data, backoff=default_tagger)
    # unigram_tagger = nltk.UnigramTagger(train_data, backoff=affix_tagger)
    # bigram_tagger = nltk.BigramTagger(train_data, backoff=unigram_tagger)
    # trigram_tagger = nltk.TrigramTagger(train_data, backoff=bigram_tagger)
    # regexp_tagger = nltk.RegexpTagger(WORD_PATTERNS, backoff=default_tagger)

    templates = brill.fntbl37()
    # templates = [ 
    #         brill.Template(brill.Pos([-1]), brill.Pos([0]), brill.Pos([1])), 
    #         brill.Template(brill.Pos([-1, 0, 1])), 
    #         # brill.Template(brill.Pos([1])), 
    #         # brill.Template(brill.Pos([-2])), 
    #         # brill.Template(brill.Pos([2])), 
    #         # brill.Template(brill.Pos([-2, -1])), 
    #         # brill.Template(brill.Pos([1, 2])), 
    #         # brill.Template(brill.Pos([-3, -2, -1])), 
    #         # brill.Template(brill.Pos([1, 2, 3])), 
    #         # brill.Template(brill.Pos([-1]), brill.Pos([1])), 
    #         # brill.Template(brill.Word([-1])), 
    #         # brill.Template(brill.Word([1])), 
    #         # brill.Template(brill.Word([-2])), 
    #         # brill.Template(brill.Word([2])), 
    #         # brill.Template(brill.Word([-2, -1])), 
    #         # brill.Template(brill.Word([1, 2])), 
    #         # brill.Template(brill.Word([-3, -2, -1])), 
    #         # brill.Template(brill.Word([1, 2, 3])), 
    #         # brill.Template(brill.Word([-1]), brill.Word([1])), 
    #         ] 
    brill_trainer_result = brill_trainer.BrillTaggerTrainer( 
            trigram_tagger, templates, deterministic=True) 
    brill_tagger = brill_trainer_result.train(train_data, max_rules=300, min_score=10)
    logger.info(f'>brill_tagger.print_template_statistics() => in console :(')
    brill_tagger.print_template_statistics()
    rules = '\n'.join([rule.__str__() for rule in brill_tagger.rules()])
    logger.info(f'>brill_tagger.rules() : \n{rules}')
    main_tagger = brill_tagger

    accuracy = main_tagger.evaluate(test_data)
    logger.info(f'>> Main tagger evaluate accuracy : {accuracy}')
    return main_tagger, accuracy

def train(tagged_sentences):
    try:
        global TAG_EXAMPLE_DIC, MAIN_TAGGER
        train_data, test_data = separate_train_and_test_data(tagged_sentences)
        MAIN_TAGGER, accuracy = create_main_tagger(train_data, test_data)
        save_trained_main_tagger()
        return accuracy
    except Exception as ex:
        logger.exception(ex)

def tag(tokens):
    global MAIN_TAGGER

    logger.info(f'> Tokens : {tokens}')
    if not MAIN_TAGGER:
        if os.path.isfile(MAIN_TAGGER_PATH):
            load_trained_main_tagger()
        else:
            raise Exception()
    
    tags = MAIN_TAGGER.tag(tokens)
    # logger.info(f'>brill_tagger.print_template_statistics() : \n{MAIN_TAGGER.print_template_statistics(printunused=False)}')
    return tags

def init():
    if os.path.isfile(MAIN_TAGGER_PATH):
        load_trained_main_tagger()

