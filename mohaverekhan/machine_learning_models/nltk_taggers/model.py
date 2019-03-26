from __future__ import unicode_literals
import os
import nltk
from mohaverekhan.core.tools import utils, normalizer, sentence_splitter, tokenizer
# from hazm import *
from pickle import dump, load


logger = utils.get_logger(logger_name='nltk_taggers')
logger.info('-------------------------------------------------------------------')

WORD_PATTERNS = [
    (r'^-?[0-9]+(.[0-9]+)?$', 'U'),
    (r'.*ها$', 'N')
    # (r'.*ing$', 'VBG'),
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
DATA_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'data')

MAIN_TAGGER_PATH = os.path.join(utils.DATA_PATH, 'nltk_main_tagger.pkl')
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
    regexp_tagger = nltk.RegexpTagger(WORD_PATTERNS, backoff=default_tagger)
    affix_tagger = nltk.AffixTagger(train_data, backoff=regexp_tagger)
    unigram_tagger = nltk.UnigramTagger(train_data, backoff=affix_tagger)
    bigram_tagger = nltk.BigramTagger(train_data, backoff=unigram_tagger)
    trigram_tagger = nltk.TrigramTagger(train_data, backoff=bigram_tagger)

    main_tagger = trigram_tagger
    result = main_tagger.evaluate(test_data)
    logger.info(f'>> Main tagger evaluate result : {result}')
    return main_tagger

def tag_sentence(sentence):
    logger.info(f'>> Tagging sentence')
    logger.info(f'> Input : {sentence}')

    sentence = normalizer.normalize(sentence)
    logger.info(f'> Normalize : {sentence}')

    # tagger = POSTagger(model='/home/bitianist/bitianist/python/externals/hazm/resources/postagger.model')
    # print(tagger.tag(word_tokenize(s1)), file=open('output9.txt', 'a'))
    tokens = tokenizer.tokenize(sentence)
    logger.info(f'> Tokenize : {tokens}')

    tags = MAIN_TAGGER.tag(tokens)
    logger.info(f'> Output : {tags}')
    # tags = dict(tags)
    # logger.info(f'> Output dictionary : |{tags}|')
    return tags

def tag_text(text):
    global MAIN_TAGGER

    logger.info(f'>> Tagging text')
    logger.info(f'> Input : {text}')
    if not MAIN_TAGGER:
        return text
    
    sentences = sentence_splitter.split(text)
    logger.info(f'> Sentences : {sentences}')
    # tags = {}
    # for sentence in sentences:
    #     tags.update(tag_sentence(sentence))
    #     logger.info(f'> current tags : {tags}')
    # return tags
    tags = [tag_sentence(sentence) for sentence in sentences]
    logger.info(f'> tags : {tags}')
    return sentences, tags

def train():
    try:
        global TAG_EXAMPLE_DIC, MAIN_TAGGER
        if os.path.isfile(MAIN_TAGGER_PATH):
            load_trained_main_tagger()
        else:
            train_data, test_data = separate_train_and_test_data(utils.tagged_sentence_list)
            MAIN_TAGGER = create_main_tagger(train_data, test_data)
            save_trained_main_tagger()
        tag_text('سلام دوستان خوبید. رستورانش واقعا عالی بود.')
        tag_text('غذایش خوب است.')
        tag_text('خیلی خیلی خوب بودطعم برگرش عالی بودمن که خیلی خوشم اومد.')
        tag_text('من دو بار اینجا رفتم برای ناهاار و برای کافی شاپ برای ناهار من فیله مینیون سفارش دادم که از هر نظر عالی بود سس قارچ فوق العاده ای داشت اما استیک مرغش خیلی معمولی بود اسموتی استوایی هم معمولی بود اما اسموتی هاوایی برخلاف ظهر جذابش خوش طعم نبود، دکوراسیون خیلییی عالیه برخورد پرسنل هم عالی')
        tag_text('اصلا خوب نیست. شیشلیک بسیار خشک و کم حجم بودمیکس فیله سفارش دادیم که پر از سماق و گوجه له شده بودپرسنلش هم سربه هوا و‌بی توجهنفضای رستوران هم فوق العاده قدیمی و نامرتبه')
        tag_text('غذاشون فوق العاده بی کیفیته . . اصلا گوشت نمیریزن تو غذاهای گوشتی فقط سویا میریزن.')
        tag_text('برگر خوب و آبدار و خوشمزه ای ندارن در عوض قیمت ها هم خیلی بالاست،سیب زمینی هم اصلا خوشمزه نیست')
        tag_text('گازنی ران سفارش دادیم که با سرویس و مالیات بالای ١٠٠ تومان میشد اما قرار بود ران بره باشد ولی بیشتر شبیه گوشت گوساله ی ریش ریش بود که خیلی خشک بود و از استخوان جدا کرده بودند که اصلا درست نیست وقتی ران بره سفارش میدهیم گوشت از استخوان جدا شده باشد و معلوم نشود چه گوشتی بوده و کنارش ماست مخصوصی بود که گارسون را صدا کردیم گفتیم یک ظرف دیگه از این ماست بیار که بتونیم اینو بخوریم چون خیلی خشک بود گوشت و ریش ریش گارسون گفت نمیشه فقط روی هر پرس غذا میاریم اضافه نمیدیم!!!')
    except Exception as ex:
        logger.exception(ex)

def init():
    # train()

