import time
import logging
from mohaverekhan.models import Normalizer
from mohaverekhan import cache

class MohaverekhanBasicNormalizer(Normalizer):

    class Meta:
        proxy = True

    logger = logging.getLogger(__name__)

    translation_characters = (
        (r'0', r'۰', '', 'hazm', 'true'),
        (r'1', r'۱', '', 'hazm', 'true'),
        (r'2', r'۲', '', 'hazm', 'true'),
        (r'3', r'۳', '', 'hazm', 'true'),
        (r'4', r'۴', '', 'hazm', 'true'),
        (r'5', r'۵', '', 'hazm', 'true'),
        (r'6', r'۶', '', 'hazm', 'true'),
        (r'7', r'۷', '', 'hazm', 'true'),
        (r'8', r'۸', '', 'hazm', 'true'),
        (r'9', r'۹', '', 'hazm', 'true'),

        (r'٠', r'۰', '', 'mohaverekhan', 'true'),
        (r'١', r'۱', '', 'mohaverekhan', 'true'),
        (r'٢', r'۲', '', 'mohaverekhan', 'true'),
        (r'٣', r'۳', '', 'mohaverekhan', 'true'),
        (r'٤', r'۴', '', 'mohaverekhan', 'true'),
        (r'٥', r'۵', '', 'mohaverekhan', 'true'),
        (r'٦', r'۶', '', 'mohaverekhan', 'true'),
        (r'٧', r'۷', '', 'mohaverekhan', 'true'),
        (r'٨', r'۸', '', 'mohaverekhan', 'true'),
        (r'٩', r'۹', '', 'mohaverekhan', 'true'),

        (r' ', r' ', 'space character 160 -> 32', 'hazm', 'true'),
        (r'ك', r'ک', '', 'hazm', 'true'),
        (r'ي', r'ی', '', 'hazm', 'true'),
        (r'ئ', r'ی', '', 'hazm', 'true'),
        (r'ؤ', r'و', '', 'hazm', 'true'),
        (r'إ', r'ا', '', 'mohaverekhan', 'true'),
        (r'أ', r'ا', '', 'mohaverekhan', 'true'),
        (r'ة', r'ه', '', 'mohaverekhan', 'true'),
        (r'“', r'"', '', 'hazm', 'true'),
        (r'”', r'"', '', 'hazm', 'true'),
        (r'%', r'٪', '', 'mohaverekhan', 'true'),
        (r'?', r'؟', '', 'mohaverekhan', 'true'),
        # (r'آ', r'ا', '', 'mohaverekhan', 'true'),
        # (r'هٔ', r'ه', '', 'hazm', 'true'),
    )

    translation_characters = {tc[0]:tc[1] for tc in translation_characters}

    basic_patterns = (
        (r'[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652]', r'', 'remove FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN', 0, 'hazm', 'true'),
        (r'[ـ\r]', r'', r'remove keshide, \r', 0, 'hazm', 'true'),
        (r'ٔ', r'', r'remove  ٔ ', 0, 'mohaverekhan', 'true'),
        (r'([^\.]|^)(\.\.\.)([^\.]|$)', r'\1…\3', 'replace 3 dots with …', 0, 'mohaverekhan', 'true'),
        (rf'([{cache.punctuations}])\1+', r'\1', 'remove cache.punctuations repetitions', 0, 'mohaverekhan', 'true'),
        (r'"([^\n"]+)"', r'«\1»', 'replace quotation with gyoome', 0, 'hazm', 'true'),
        (r'\n+', r'\n', 'remove extra newlines', 0, 'mohaverekhan', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
    )
    basic_patterns = [(p[0], p[1]) for p in basic_patterns]
    basic_patterns = cache.compile_patterns(basic_patterns)

    def uniform_signs(self, text_content):
        text_content = text_content.translate(text_content.maketrans(self.translation_characters))
        text_content = text_content.strip(' ')
        return text_content
        # self.logger.info(f'> After uniform_signs : \n{text_content}')

    def do_basic_patterns(self, text_content):
        for pattern, replacement in self.basic_patterns:
            text_content = pattern.sub(replacement, text_content)
            # self.logger.info(f'> after {pattern} -> {replacement} : \n{text_content}')
        text_content = text_content.strip(' ')
        return text_content

    
    def normalize(self, text_content):
        beg_ts = time.time()
        # self.logger.info(f'>>> mohaverekhan-basic-normalizer : \n{text_content}')
        text_content = text_content.strip(' ')

        text_content = self.uniform_signs(text_content)
        # self.logger.info(f'>> uniform_signs : \n{text_content}')

        text_content = self.do_basic_patterns(text_content)
        # self.logger.info(f'>> do_basic_patterns : \n{text_content}')

        text_content = text_content.strip(' ')
        
        end_ts = time.time()
        # self.logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        # self.logger.info(f'> Result mohaverekhan-basic-normalizer : \n{text_content}')
        return text_content