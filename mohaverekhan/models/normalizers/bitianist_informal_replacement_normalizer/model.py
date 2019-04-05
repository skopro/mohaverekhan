import time
import logging
import re
from mohaverekhan.models import Normalizer, Text, TextNormal
from mohaverekhan import cache

logger = None


class BitianistInformalReplacementNormalizer(Normalizer):
    
    class Meta:
        proxy = True

    replacement_patterns = (
        (r'-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?', r' NUMBER ', 'number', 0, 'bitianist', 'true'),
        (r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+', r' EMOJI ', 'emoji', 0, 'hazm', 'true'),
        (r'[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}', r' EMAIL ', 'email', 0, 'hazm', 'true'),
        (r'((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)', r' LINK ', 'link, hazm + "="', 0, 'hazm', 'true'),
        (r'([^\w\._]*)(@[\w_]+)([\S]+)', r' ID ', 'id', 0, 'hazm', 'true'),
        (r'\#([\S]+)', r' TAG ', 'tag', 0, 'hazm', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
    )
    replacement_patterns = [(rp[0], rp[1]) for rp in replacement_patterns]
    replacement_patterns = cache.compile_patterns(replacement_patterns)

    def normalize(self, text):
        logger.info(f'>> RefinementRuleBasedNormalizer : \n{text}')
        text_normal, created = TextNormal.objects.get_or_create(
            text=text, 
            normalizer=self
            )
        text_normal.content = text.content.strip()
        beg_ts = time.time()
        
        for pattern, replacement in self.replacement_patterns:
            text_normal.content = pattern.sub(replacement, text_normal.content)
            logger.info(f'> After {pattern} -> {replacement} : \n{text_normal.content}')
        text_normal.content = text_normal.content.strip()

        end_ts = time.time()
        logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        text_normal.save()
        logger.info(f'{text_normal}')
        return text_normal

def init():
    global logger
    logger = logging.getLogger(__name__)