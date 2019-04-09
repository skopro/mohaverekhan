import time
import logging
import re
from mohaverekhan.models import Normalizer, Text, TextNormal
from mohaverekhan import cache

logger = None


class BitianistInformalRefinementNormalizer(Normalizer):
    
    class Meta:
        proxy = True

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

        (r'٠', r'۰', '', 'bitianist', 'true'),
        (r'١', r'۱', '', 'bitianist', 'true'),
        (r'٢', r'۲', '', 'bitianist', 'true'),
        (r'٣', r'۳', '', 'bitianist', 'true'),
        (r'٤', r'۴', '', 'bitianist', 'true'),
        (r'٥', r'۵', '', 'bitianist', 'true'),
        (r'٦', r'۶', '', 'bitianist', 'true'),
        (r'٧', r'۷', '', 'bitianist', 'true'),
        (r'٨', r'۸', '', 'bitianist', 'true'),
        (r'٩', r'۹', '', 'bitianist', 'true'),

        (r' ', r' ', 'space character 160 -> 32', 'hazm', 'true'),
        (r'ك', r'ک', '', 'hazm', 'true'),
        (r'ي', r'ی', '', 'hazm', 'true'),
        (r'ئ', r'ی', '', 'hazm', 'true'),
        (r'ؤ', r'و', '', 'hazm', 'true'),
        # (r'آ', r'ا', '', 'bitianist', 'true'),
        (r'إ', r'ا', '', 'bitianist', 'true'),
        (r'أ', r'ا', '', 'bitianist', 'true'),
        (r'ة', r'ه', '', 'bitianist', 'true'),
        # (r'هٔ', r'ه', '', 'hazm', 'true'),
        (r'“', r'"', '', 'hazm', 'true'),
        (r'”', r'"', '', 'hazm', 'true'),
        (r'%', r'٪', '', 'bitianist', 'true'),
        (r'?', r'؟', '', 'bitianist', 'true'),
        
    )

    translation_characters = {tc[0]:tc[1] for tc in translation_characters}

    remove_character_patterns = (
        (r'[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652]', r'', 'remove FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN', 0, 'hazm', 'true'),
        (r'[ـ\r]', r'', r'remove keshide, \r', 0, 'hazm', 'true'),
        (r'ٔ', r'', r'remove  ٔ ', 0, 'bitianist', 'true'),

    )
    remove_character_patterns = [(rc[0], rc[1]) for rc in remove_character_patterns]
    remove_character_patterns = cache.compile_patterns(remove_character_patterns)

    refinement_patterns = (
        (r'([^\.]|^)(\.\.\.)([^\.]|$)', r'\1…\3', 'replace 3 dots with …', 0, 'bitianist', 'true'),
        (rf'([{cache.punctuations}])\1+', r'\1', 'remove cache.punctuations repetitions', 0, 'bitianist', 'true'),
        (r'"([^\n"]+)"', r'«\1»', 'replace quotation with gyoome', 0, 'hazm', 'true'),
        # (r'(-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?)', r' \1 ', 'number', 0, 'bitianist', 'true'),
        (rf'({cache.emoji})(?=[{cache.persians}{cache.punctuations}])', r'\1 ', '', 0, 'bitianist', 'true'),
        (rf'({cache.link})(?=[{cache.persians}{cache.punctuations}{cache.emoji}])', r'\1 ', '', 0, 'bitianist', 'true'),
        (rf'({cache.email})(?=[{cache.persians}{cache.punctuations}{cache.emoji}])', r'\1 ', '', 0, 'bitianist', 'true'),
        (rf'({cache.id})(?=[{cache.persians}{cache.punctuations}{cache.emoji}])', r'\1 ', '', 0, 'bitianist', 'true'),
        (rf'({cache.tag})(?=[{cache.persians}{cache.punctuations}{cache.emoji}])', r'\1 ', '', 0, 'bitianist', 'true'),
        # (rf'({cache.link}|{cache.emoji}|{cache.email}|{cache.id}|{cache.tag})(?=[{cache.persians}{cache.punctuations}])', r'\1 ', '', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.emoji})', r' \1', '', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.link})', r' \1', '', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.email})', r' \1', '', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.id})', r' \1', '', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.tag})', r' \1', '', 0, 'bitianist', 'true'),
        # (rf'(?<=[{cache.persians}{cache.punctuations}])({cache.link}|{cache.emoji}|{cache.email}|{cache.id}|{cache.tag})', r' \1', '', 0, 'bitianist', 'true'),
        # (rf'(?<=[^a-zA-Z{cache.numbers}])([{cache.punctuations}])(?=[^a-zA-Z]|$)', r' \1 ', 'add extra space before and after of cache.punctuations', 0, 'bitianist', 'true'),
        (rf'([{cache.punctuations}]|[{cache.numbers}]+)(?=[{cache.persians}])', r'\1 ', 'add extra space before and after of cache.punctuations', 0, 'bitianist', 'true'),
        (rf'(?<=[{cache.persians}])([{cache.punctuations}]|[{cache.numbers}]+)', r' \1', 'add extra space before and after of cache.punctuations', 0, 'bitianist', 'true'),
        # (rf'([^a-zA-Z {cache.numbers}]+)([{cache.numbers}]+)|([{cache.numbers}]+)([^a-zA-Z {cache.numbers}]+)', r'\1 \2\3 \4', '', 0, 'bitianist', 'true'),
        # (rf'([{cache.persians}]+)([{cache.numbers}]+|[{cache.punctuations}]+|cache.link_pattern)|([{cache.numbers}]+)([{cache.persians}]+)', r'\1 \2\3 \4', '', 0, 'bitianist', 'true'),
        (r'\n+', r'\n', 'remove extra newlines', 0, 'bitianist', 'true'),
        (r'\n', r' newline ', 'replace \n to newline for changing back', 0, 'bitianist', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),

        (r'([^ ]ه) ی ', r'\1‌ی ', 'between ی and ه - replace space with non-joiner ', 0, 'hazm', 'true'),
        (r'(^| )(ن?می) ', r'\1\2‌', 'after می،نمی - replace space with non-joiner ', 0, 'hazm', 'true'),
        (rf'(?<=[^\n\d {cache.punctuations}]{{2}}) (تر(ین?)?|گری?|های?)(?=[ \n{cache.punctuations}]|$)', r'‌\1', 'before تر, تری, ترین, گر, گری, ها, های - replace space with non-joiner', 0, 'hazm', 'true'),
        (rf'([^ ]ه) (ا(م|یم|ش|ند|ی|ید|ت))(?=[ \n{cache.punctuations}]|$)', r'\1‌\2', 'before ام, ایم, اش, اند, ای, اید, ات - replace space with non-joiner', 0, 'hazm', 'true'),  

        # (rf'([^{repetition_characters}])\1{{1,}}', r'\1', 'remove repetitions except ی و', 0, 'bitianist', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
    )
    refinement_patterns = [(rp[0], rp[1]) for rp in refinement_patterns]
    refinement_patterns = cache.compile_patterns(refinement_patterns)

    def split_into_token_contents(self, text, delimiters='[ ]+'):
        return re.split(delimiters, text.content)


    def uniform_signs(self, text):
        text.content = text.content.translate(text.content.maketrans(self.translation_characters))
        text.content = text.content.strip(' ')
        # logger.info(f'> After uniform_signs : \n{text.content}')

    def remove_some_characters(self, text):
        for pattern, replacement in self.remove_character_patterns:
            text.content = pattern.sub(replacement, text.content)
            # logger.info(f'> after {pattern} -> {replacement} : \n{text.content}')
        text.content = text.content.strip(' ')

    def refine_text(self, text):
        for pattern, replacement in self.refinement_patterns:
            text.content = pattern.sub(replacement, text.content)
            # logger.info(f'> after {pattern} -> {replacement} : \n{text.content}')
        text.content = text.content.strip(' ')


    repetition_pattern = re.compile(r"([^ب])\1{1,}") # ببندم=بند
    # repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")

    def fix_repetition_token(self, token_content):
        if len(token_content) <= 2: #شش
            return token_content


        fixed_token_content = token_content
        if self.repetition_pattern.search(fixed_token_content):
            fixed_token_content = self.repetition_pattern.sub(r'\1\1', token_content) #شش
            if fixed_token_content in cache.all_token_tags:
                logger.info(f'> found repetition token {token_content} -> {fixed_token_content}')
                return fixed_token_content

            fixed_token_content = self.repetition_pattern.sub(r'\1', token_content)
            if fixed_token_content == 'کنده':
                return 'کننده'
            if fixed_token_content in cache.all_token_tags:
                logger.info(f'> found repetition token {token_content} -> {fixed_token_content}')
                return fixed_token_content
            
            # عاااالیه
            logger.info(f'> fix_repetition_token token_content[0:-1] : {token_content[0:-1]}')
            fixed_token_content = self.repetition_pattern.sub(r'\1\1', token_content[0:-1])
            if fixed_token_content in cache.all_token_tags:
                fixed_token_content += token_content[-1]
                logger.info(f'> found repetition token {token_content} -> {fixed_token_content}')
                return fixed_token_content

            fixed_token_content = self.repetition_pattern.sub(r'\1', token_content[0:-1])
            if fixed_token_content in cache.all_token_tags:
                fixed_token_content += token_content[-1]
                logger.info(f'> found repetition token {token_content} -> {fixed_token_content}')
                return fixed_token_content
            
            fixed_token_content = token_content
            
        return fixed_token_content

    def fix_repetition_tokens(self, text):
        logger.info(f'>> fix_repetition_tokens')
        token_contents = self.split_into_token_contents(text)
        fixed_text_content = ''
        fixed_token_content = ''
        for token_content in token_contents:
            fixed_token_content = token_content.strip(' ')
            if fixed_token_content not in cache.all_token_tags:
                fixed_token_content = self.fix_repetition_token(fixed_token_content)
            
            fixed_text_content += fixed_token_content.strip(' ') + " "
        text.content = fixed_text_content[:-1]
        text.content = text.content.strip(' ')

    move_limit = 3
    def join_multipart_tokens(self, text):
        logger.debug(f'>> join_multipart_tokens')
        logger.debug(f'{text.content}')

        token_contents = self.split_into_token_contents(text)
        logger.debug(f'token_contents : {token_contents}')
        fixed_text_content = ''
        fixed_token_content = ''
        token_length = len(token_contents)
        
        i = 0
        while i < token_length:
            move_count = min(token_length - (i+1), self.move_limit)
            # logger.debug(f'> i : {i} | move_count : {move_count}')

            # end
            if move_count == 0:
                logger.debug(f'> Join the last one : {token_contents[i]}')
                fixed_text_content += token_contents[i]
                break

            # try to join
            for move_count in reversed(range(0, move_count+1)):
                # end when move_count = 0 return the word without any join
                fixed_token_content = '‌'.join(token_contents[i:i+move_count+1])
                if fixed_token_content in cache.all_token_tags or move_count == 0:
                    logger.debug(f'> nj [i:i+move_count+1] : [{i}:{i+move_count+1}] : {fixed_token_content}')
                    # logger.debug(f'> Found => move_count : {move_count} | fixed_token_content : {fixed_token_content}')
                    i = i + move_count + 1
                    fixed_text_content += fixed_token_content + ' '
                    break

                #دو بار بری رو داشت جمع میکردی دو باربری
                #باید جدول توکن ها درست کنم که براساس تگ تصمیم بگیرم بچسبونم یا نه
                # fixed_token_content = ''.join(token_contents[i:i+move_count+1])
                # if fixed_token_content in cache.all_token_tags or move_count == 0:
                #     logger.debug(f'> empty [i:i+move_count+1] : [{i}:{i+move_count+1}] : {fixed_token_content}')
                #     # logger.debug(f'> Found => move_count : {move_count} | fixed_token_content : {fixed_token_content}')
                #     i = i + move_count + 1
                #     fixed_text_content += fixed_token_content + ' '
                #     break

        text.content = fixed_text_content.strip(' ')
        logger.debug(f'{text.content}')


    def fix_wrong_joined_undefined_token(self, token_content):
        nj_pattern = re.compile(r'‌')
        if nj_pattern.search(token_content):
            logger.debug(f'> nj found in token : {token_content}')
            fixed_token_content = token_content.replace('‌', '')
            if fixed_token_content in cache.all_token_tags:
                logger.debug(f'> nj replaced with empty : {fixed_token_content}')
                return fixed_token_content

        part1, part2, nj_joined, sp_joined = '', '', '', ''
        for i in range(1, len(token_content)):
            part1, part2 = token_content[:i], token_content[i:]
            nj_joined = f'{part1}‌{part2}'
            if nj_joined in cache.all_token_tags:
                logger.debug(f'> Found nj_joined : {nj_joined}')
                return nj_joined
        
        # for i in range(1, len(token_content)): # محاوره‌ خوان
        #     part1, part2 = token_content[:i], token_content[i:]
        #     if part1 in cache.all_token_tags and part2 in cache.all_token_tags:
        #         sp_joined = f'{part1} {part2}'
        #         logger.debug(f'> Found sp_joined : {sp_joined}')
        #         return sp_joined

        # logger.debug(f"> Can't fix {token_content}")
        return token_content

    def fix_wrong_joined_undefined_tokens(self, text):
        logger.debug(f'>> fix_wrong_joined_undefined_tokens')
        logger.debug(f'{text.content}')

        token_contents = self.split_into_token_contents(text)
        logger.debug(f'> token_contents : {token_contents}')
        fixed_text_content = ''
        fixed_token_content = ''

        for token_content in token_contents:
            fixed_token_content = token_content.strip(' ')
            if fixed_token_content not in cache.all_token_tags:
                logger.debug(f'> {fixed_token_content} not in token set!')
                fixed_token_content = self.fix_wrong_joined_undefined_token(fixed_token_content)
            
            fixed_text_content += fixed_token_content.strip(' ') + " "
        text.content = fixed_text_content[:-1]
        text.content = text.content.strip(' ')

    def normalize(self, text):
        logger.info(f'>> RefinementRuleBasedNormalizer : \n{text}')
        text_normal, created = TextNormal.objects.get_or_create(
            text=text, 
            normalizer=self
            )
        text_normal.content = text.content.strip(' ')
        beg_ts = time.time()
        self.uniform_signs(text_normal)
        self.remove_some_characters(text_normal)
        self.refine_text(text_normal)
        self.join_multipart_tokens(text_normal) # آرام کننده
        self.fix_repetition_tokens(text_normal)
        self.join_multipart_tokens(text_normal) # فرههههههههنگ سرا
        self.fix_wrong_joined_undefined_tokens(text_normal) # آرامکننده کتابمن 
        self.join_multipart_tokens(text_normal) # آرام کنندهخوبی
        text_normal.content = text_normal.content.replace(' newline ', '\n').strip(' ')
        end_ts = time.time()
        logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        text_normal.save()
        logger.info(f'> Result : \n{text_normal.content}')
        return text_normal


def init():
    global logger
    logger = logging.getLogger(__name__)