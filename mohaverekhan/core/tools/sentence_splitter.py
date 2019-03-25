import re
from hazm import *
from . import utils

logger = utils.get_logger(logger_name='sentence_splitter')
logger.info('-------------------------------------------------------------------')

sentence_splitters = '.*?[.!\?]'

def split(text):
    # output = re.findall(sentence_splitters, text)
    tokenizer = SentenceTokenizer()
    output = tokenizer.tokenize(text)
    logger.info(f'\n>> Test\n\nInput : \n{text}\n\nOutput : \n{output}\n\n')
    return output


def init():
    sample1 = 'من از قدیییییم مشتریشون بودم. سالها پیش که اول اسمش ذن بود و بعد شد خانه آسیایی. اون موقع هم سوشی ها و هم ساشیمی های عااااالی ای داشت. پیش غذا هم همیشه میسو سوپ میخوردم. از نظر توضیحاتی هم که در مورد غذا ها میدادن فوق‌العاده بود. الان فرصت ندارم ولی دوس دارم حتما باز هم برم'
