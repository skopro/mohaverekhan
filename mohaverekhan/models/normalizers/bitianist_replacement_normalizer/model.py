import time
import logging
from mohaverekhan.models import Normalizer
from mohaverekhan import cache

class BitianistReplacementNormalizer(Normalizer):
    
    class Meta:
        proxy = True

    logger = logging.getLogger(__name__)

    replacement_patterns = (
        (rf'([{cache.emojies}]+)(?=[ {cache.persians}{cache.punctuations}]|$)', r' EMOJI ', '', 0, 'bitianist', 'true'),
        (rf'({cache.email})(?=[ {cache.persians}{cache.punctuations}{cache.emojies}]|$)', r' EMAIL ', '', 0, 'bitianist', 'true'),
        (rf'({cache.link})(?=[ {cache.persians}{cache.punctuations}{cache.emojies}]|$)', r' LINK ', '', 0, 'bitianist', 'true'),
        (rf'({cache.id})(?=[ {cache.persians}{cache.emojies}]|$)', r' ID ', '', 0, 'bitianist', 'true'),
        (rf'({cache.tag})(?=[ {cache.persians}{cache.punctuations}{cache.emojies}]|$)', r' TAG ', '', 0, 'bitianist', 'true'),
        (rf'({cache.num}|{cache.numf})(?=[ {cache.persians}{cache.num_punctuations}{cache.emojies}]|$)', r' NUMBER ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.punctuations}])([{cache.emojies}]+)', r' EMOJI ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.punctuations}{cache.emojies}])({cache.email})', r' EMAIL ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.punctuations}{cache.emojies}])({cache.link})', r' LINK ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.punctuations}{cache.emojies}])({cache.id})', r' ID ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.punctuations}{cache.emojies}])({cache.tag})', r' TAG ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[ {cache.persians}{cache.num_punctuations}{cache.emojies}])({cache.num}|{cache.numf})', r' NUMBER ', '', 0, 'bitianist', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
        # (r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+', r' EMOJI ', 'emoji', 0, 'hazm', 'true'),
        # (r'[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}', r' EMAIL ', 'email', 0, 'hazm', 'true'),
        # (r'((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)', r' LINK ', 'link, hazm + "="', 0, 'hazm', 'true'),
        # (r'([^\w\._]*)(@[\w_]+)([\S]+)', r' ID ', 'id', 0, 'hazm', 'true'),
        # (r'\#([\S]+)', r' TAG ', 'tag', 0, 'hazm', 'true'),
        # (r'-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?', r' NUMBER ', 'number', 0, 'bitianist', 'true'),
    )
    replacement_patterns = [(rp[0], rp[1]) for rp in replacement_patterns]
    replacement_patterns = cache.compile_patterns(replacement_patterns)

    def normalize(self, text_content):
        beg_ts = time.time()
        self.logger.info(f'>>> bitianist_replacement_normalizer : \n{text_content}')

        text_content = cache.normalizers['bitianist-basic-normalizer']\
                        .normalize(text_content)
        self.logger.info(f'>>> bitianist-basic-normalizer : \n{text_content}')
        
        text_content = text_content.strip(' ')

        for pattern, replacement in self.replacement_patterns:
            text_content = pattern.sub(replacement, text_content)
            self.logger.info(f'> After {pattern} -> {replacement} : \n{text_content}')
        self.logger.info(f'>> replace_text : \n{text_content}')
        text_content = text_content.strip()

        end_ts = time.time()
        self.logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        self.logger.info(f'>>> Result bitianist_replacement_normalizer : \n{text_content}')
        return text_content
