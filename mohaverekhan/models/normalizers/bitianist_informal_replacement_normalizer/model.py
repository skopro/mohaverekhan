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
        (r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+', r' EMOJI ', 'emoji', 0, 'hazm', 'true'),
        (r'[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}', r' EMAIL ', 'email', 0, 'hazm', 'true'),
        (r'((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)', r' LINK ', 'link, hazm + "="', 0, 'hazm', 'true'),
        (r'([^\w\._]*)(@[\w_]+)([\S]+)', r' ID ', 'id', 0, 'hazm', 'true'),
        (r'\#([\S]+)', r' TAG ', 'tag', 0, 'hazm', 'true'),
        (r'-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?', r' NUMBER ', 'number', 0, 'bitianist', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
    )
    replacement_patterns = [(rp[0], rp[1]) for rp in replacement_patterns]
    replacement_patterns = cache.compile_patterns(replacement_patterns)

    def normalize(self, text):
        logger.info(f'>> RefinementRuleBasedNormalizer : \n{text}')
        text_normal = cache.normalizers['bitianist-informal-refinement-normalizer']\
                        .normalize(text)
        logger.info(f'> After refinement : \n{text_normal.content}\n')
        text_normal, created = TextNormal.objects.update_or_create(
            text=text_normal, 
            normalizer=self,
            defaults={'content': text_normal.content},
            )
        logger.info(f'> update or create text_normal : \n{text_normal.content}\n')
        text_normal.content = text_normal.content.strip()
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