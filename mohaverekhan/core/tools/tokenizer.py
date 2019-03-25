from hazm import *
from . import utils

logger = utils.get_logger(logger_name='tokenizer')
logger.info('-------------------------------------------------------------------')

def tokenize(text):
    words = word_tokenize(text)

    return words

def init():
    sample1 = 'من از قدیییییم مشتریشون بودم. سالها پیش که اول اسمش ذن بود و بعد شد خانه آسیایی. اون موقع هم سوشی ها و هم ساشیمی های عااااالی ای داشت. پیش غذا هم همیشه میسو سوپ میخوردم. از نظر توضیحاتی هم که در مورد غذا ها میدادن فوق‌العاده بود. الان فرصت ندارم ولی دوس دارم حتما باز هم برم'
    logger.info(f'\n>> Test\n\nInput : \n{sample1}\n\nOutput : \n{tokenize(sample1)}\n\n')
