import logging
import random
import re
from django.apps import apps
import time
from django.utils import timezone
import pytz
from django.db.models import Count

repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")
# debug_pattern = re.compile(r'[0-9۰۱۲۳۴۵۶۷۸۹]')
# debug_pattern = re.compile(r'^گرون$|^میدون$|^خونه$|^نون$|^ارزون$|^اون$|^قلیون$')
# debug_pattern = re.compile(r'هایمان')
debug_pattern = re.compile(r'^(.)\1{5}$')

logger = None
normalizers = {}
validators = {}
taggers = {}
token_set = set()
repetition_word_set = set()
compile_patterns = lambda patterns: [(re.compile(pattern), repl) for pattern, repl in patterns]
typographies = r'&*@‱\\/•^†‡⹋°〃=※×#÷%‰¶§‴~_\|‖¦٪'
punctuations = r'\.:!،؛?؟»\]\)\}«\[\(\{\'\"…¡¿'
num_punctuations = r':!،؛?؟»\]\)\}«\[\(\{\'\"…¡¿'
numbers = r'۰۱۲۳۴۵۶۷۸۹'
persians = 'اآب‌پتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
has_persian_character_pattern = re.compile(rf"([{persians}{numbers}])")
link = r'((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([a-zA-Z۰-۹0-9-]+)(\.([a-zA-Z۰-۹0-9]){2,})+([-\w@:%_\+\/~#?&=]+)?)'
emojies = r'\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD'
email = r'[a-zA-Z۰-۹0-9\._\+-]+@([a-zA-Z۰-۹0-9-]+\.)+[A-Za-z]{2,}'
id = r'@[a-zA-Z_]+'
num = r'[+-]?[\d۰-۹]+'
numf = r'[+-]?[\d۰-۹,]+[\.٫,]{1}[\d۰-۹]+'
tag = r'\#([\S]+)'
nj = '‌'
tag_set_token_tags = dict()
all_token_tags = dict()

is_number_pattern = re.compile(rf"^({num})|(numf)$")



###############################################################################
# باید بررسی کنیم نشانه‌های مورد نظر در مجموعه داده موجود وجود دارد یا نه
# ممکن است نشانه به حالت دیگری در مجموعه داده موجود باشد که این حالات استثنا را بررسی می‌کنیم
# ممکنه نشانه مورد نظر، یک نشانه بی‌نهایت باشد و یک نشانه بی‌نهایت برای ما معتبر هست.
def is_token_valid(token_content, replace_nj=True):

    # اگر نشانه عدد بود، آن را قبول و برای بهبود سرعت آن را در کش ذخیره می‌کنیم.
    if is_number_pattern.fullmatch(token_content):
        logger.info(f'> Number found and added : {token_content}')
        tag_set_token_tags['mohaverekhan-tag-set'][token_content] = {'U': 1}
        all_token_tags[token_content] = {'U': 1}
        return True, token_content

    # برچسب آر به معنای معتبر بودن نشانه نیست و اگر نشانه فقط برچسب آر داشت آن را معتبر نمی‌خوانیم.
    if token_content in all_token_tags and list(all_token_tags[token_content].keys()) != ['R']:
        return True, token_content

    # وقتی نشانه به این‌جا برسد، پس یعنی در مجموعه داده موجود نبوده.
    # تلاش‌های آخر را می‌کنیم تا ببینیم شاید نیم‌فاصله‌ای رعایت نشده‌است.
    
    # اگر در نشانه، نیم‌فاصله‌ای موجود بود، آن را حذف می‌کنیم و سپس معتبر بودن نشانه را بررسی می‌کنیم.
    if replace_nj:
        nj_pattern = re.compile(r'‌')
        if nj_pattern.search(token_content):
            # logger.debug(f'> nj found in token : {token_content}')
            token_content_parts = token_content.split('‌')
            is_valid = True

            # اگر یک قسمت اندازه‌اش کمتر از ۳ بود، پس احتمالا معتبر نیست.
            for part in token_content_parts:
                if len(part) < 3:
                    is_valid = False

            fixed_token_content = token_content.replace('‌', '')
            if is_valid and fixed_token_content in all_token_tags:
                logger.debug(f'> nj replaced with empty : {fixed_token_content}')
                return True, fixed_token_content

    # باید بررسی کنیم شاید نیم‌فاصله ای در نشانه رعایت نشده باشد.
    # بین تمام حروف، نیم‌فاصله می‌گذاریم. اگر معتبر بود، پس آن را بازمی‌گردانیم.
    part1, part2, nj_joined, sp_joined = '', '', '', ''
    for i in range(1, len(token_content)):
        part1, part2 = token_content[:i], token_content[i:]
        nj_joined = f'{part1}‌{part2}'
        if nj_joined in all_token_tags:
            logger.debug(f'> Found nj_joined : {nj_joined}')
            return True, nj_joined
    
    return False, token_content

def cache_token_tags_dic():
    global tag_set_token_tags, all_token_tags, repetition_word_set
    temp_tag_set_token_tags = {}
    temp_all_token_tags = {}
    temp_repetition_word_set = set()
    token_content, tag_name = '', ''
    Tag = apps.get_model(app_label='mohaverekhan', model_name='Tag')
    Token = apps.get_model(app_label='mohaverekhan', model_name='Token')
    TokenTag = apps.get_model(app_label='mohaverekhan', model_name='TokenTag')
    TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
    
    # yesterday = timezone.date.today() - timezone.timedelta(days=1)
    # yesterday = timezone.now() - timezone.timedelta(days=1)
    # Tag.objects.filter(created__gt=yesterday).delete()
    # TokenTag.objects.filter(created__gt=yesterday).delete()
    # logger.info(f'> today deleted')
    c = Token.objects.annotate(tags_count=Count('tags')).filter(tags_count__exact=0).delete()
    logger.info(f'>>>>>>>>>>>>> c : {c}')
    logger.info(f'> Tokens with 0 tags deleted')

    text_tag_list = TextTag.objects.filter(is_valid=True).values_list('tagger__tag_set__name', 'tagged_tokens')
    if text_tag_list.count() == 0:
        return
    before, after = '', ''
    logger.info(f'> Looking for {debug_pattern}')
    tag_set_name = ''
    tagged_tokens = None
    for text_tag in text_tag_list:
        tag_set_name = text_tag[0]
        tagged_tokens = text_tag[1]
        for index, tagged_token in enumerate(tagged_tokens):
            token_content = tagged_token['token']
            tag_name = tagged_token['tag']['name']

            if debug_pattern.search(token_content):
                # if tag_name != 'U':
                if index - 1 >= 0:
                    before = tagged_tokens[index-1]['token']
                else:
                    before = '^'

                if index + 1 < len(tagged_tokens):
                    after = tagged_tokens[index+1]['token']
                else:
                    after = '$'

                logger.info(f'> Token A {after} A    B {token_content} B    C {before} C has tag [{tag_name}]')
            # if tag_name not in ('O', 'U'):
            # token_set.add(token_content)
            token_tags = temp_tag_set_token_tags.get(tag_set_name, {})
            tag_counts = token_tags.get(token_content, {})
            tag_count = tag_counts.get(tag_name, 0)
            tag_counts[tag_name] = tag_count + 1
            token_tags[token_content] = tag_counts
            temp_tag_set_token_tags[tag_set_name] = token_tags

            

                # token_tags.append(tag_name)
                # token_tags_dic[token_content] = token_tags
    plural_token_content = ''
    mi_verb_heh = ''
    a_o_token = ''
    ie_token = ''
    token, tag = None, None
    middle_a_pattern = re.compile(r"^.*[^و]ان.*$") # ببندم=بند
    for tag_set_name, tag_set_token_tags in dict(temp_tag_set_token_tags).items():
        for token_content, tags in dict(tag_set_token_tags).items():
            # Try add plural names
            if(
                len(token_content) > 2 and 
                'N' in tags and 
                token_content[-2:] != 'ها' and
                token_content[-3:] != 'های' and
                token_content[-4:] != 'هایی' and
                not (token_content[-3:] == 'هان' and token_content[:-2] in tag_set_token_tags)
            ):
                if token_content[-1] in ('ه', 'ی'):
                    plural_token_content = token_content + '‌' + 'ها'
                else:
                    plural_token_content = token_content + 'ها'
                # logger.info(f'> plural {plural_token_content}')
                if plural_token_content not in tag_set_token_tags:
                    temp_tag_set_token_tags[tag_set_name][plural_token_content] = {'N': 1}
                    temp_tag_set_token_tags[tag_set_name][plural_token_content+'ی'] = {'N': 1}

                    # tag = Tag.objects.get(tag_set__name='mohaverekhan-tag-set', name='N')

                    # token, created = Token.objects.get_or_create(content=plural_token_content)
                    # TokenTag.objects.get_or_create(token=token, tag=tag)

                    # token, created = Token.objects.get_or_create(content=plural_token_content+'ی')
                    # TokenTag.objects.get_or_create(token=token, tag=tag)

                    # logger.info(f'> Added plural {plural_token_content} {plural_token_content}ی')


                if token_content[-1] != 'ا':
                    informal_plural_token_content = token_content + 'ا'
                    if informal_plural_token_content not in tag_set_token_tags:
                        # logger.info(f'> Added informal plural {informal_plural_token_content} {informal_plural_token_content}ی')
                        temp_tag_set_token_tags[tag_set_name][informal_plural_token_content] = {'N': 1}
                        temp_tag_set_token_tags[tag_set_name][informal_plural_token_content+'ی'] = {'N': 1}

                        # tag = Tag.objects.get(tag_set__name='mohaverekhan-tag-set', name='N')
                        # token, created = Token.objects.get_or_create(content=informal_plural_token_content)
                        # TokenTag.objects.get_or_create(token=token, tag=tag)

                        # token, created = Token.objects.get_or_create(content=informal_plural_token_content+'ی')
                        # TokenTag.objects.get_or_create(token=token, tag=tag)

                        # logger.info(f'> Added plural {informal_plural_token_content} {informal_plural_token_content}ی')

            if (
                len(token_content) > 2 and 
                token_content.endswith('ه‌ای')
            ):
                ie_token = token_content + 'ه'
                if ie_token not in tag_set_token_tags:
                    temp_tag_set_token_tags[tag_set_name][ie_token] = {'A': 1}


            # if(
            #     len(token_content) > 2 and 
            #     'N' in tags and
            #     (
            #         token_content.endswith('ان') or
            #         token_content.endswith('انه')
            #     ) and
            #     token_content.find('وان') == -1
            # ):
            #     a_o_token = token_content.replace('ان', 'ون')
            #     logger.info(f'> a_o_token {token_content} {a_o_token}')
            #     if a_o_token not in tag_set_token_tags:
            #         temp_tag_set_token_tags[tag_set_name][a_o_token] = {'N': 1}

            # Try add می‌فعل‌ه
            # if(
            #     'V' in tags and 
            #     token_content[:2] == 'می' and
            #     token_content[-1] == 'د'
            # ):
            #     if token_content[-2] == 'و' or token_content[-2] == 'ه':
            #         mi_verb_heh = token_content[:-2] + 'ه'
            #     else:
            #         mi_verb_heh = token_content[:-1] + 'ه'
            #     if mi_verb_heh not in tag_set_token_tags or 'V' not in tag_set_token_tags[mi_verb_heh]:
            #         temp_tag_set_token_tags[tag_set_name][mi_verb_heh] = {'V': 1}
            #         logger.info(f'> Added mi_verb_heh {mi_verb_heh}')

    # token_set.remove('دیگهای')
    del temp_tag_set_token_tags['bijankhan-tag-set']['دیگهای']
    del temp_tag_set_token_tags['bijankhan-tag-set']['هارو']

    
    logger.info(f'> len(temp_tag_set_token_tags) : {len(temp_tag_set_token_tags)}')
    logger.info(f'>>> Random samples')
    for tag_set, token_tags in temp_tag_set_token_tags.items():
        logger.info(f'>> tag_set : {tag_set}')
        for token in random.sample(list(token_tags), min(len(token_tags), 25)):
            logger.info(f'> {token} : {token_tags[token]}')

    
    [temp_all_token_tags.update(token_tags) for token_tags in temp_tag_set_token_tags.values()]
    for token in temp_all_token_tags:
        if repetition_pattern.search(token):
            no_repeat = repetition_pattern.sub(r'\1', token)
            logger.info(f'> ({token}, {no_repeat})')
            if no_repeat in temp_all_token_tags:
                temp_repetition_word_set.add(token)

    if temp_repetition_word_set:
        logger.info(f'> len(temp_repetition_word_set) : {len(temp_repetition_word_set)}')
        logger.info(f'> temp_repetition_word_set samples: {set(random.sample(temp_repetition_word_set, min(len(temp_repetition_word_set), 100)))}')

    tag_set_token_tags = temp_tag_set_token_tags
    all_token_tags = temp_all_token_tags
    repetition_word_set = temp_repetition_word_set


    two_length_token_set = set()
    for token_content in all_token_tags:
        if (
            len(token_content) == 2 and 
            # ('C' in all_token_tags[token_content] or 'R' in all_token_tags[token_content])
            'R' not in all_token_tags[token_content] and 
            'C' not in all_token_tags[token_content]
        ):
            two_length_token_set.add(token_content)

def cache_validators():
    Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')

    validators['mohaverekhan-validator'] = Validator.objects.filter(
        name='mohaverekhan-validator').first()

    logger.info(f'>> Cached validators : {list(validators.keys())}')

def cache_normalizers():
    MohaverekhanBasicNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanBasicNormalizer')
    MohaverekhanCorrectionNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanCorrectionNormalizer')
    MohaverekhanReplacementNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanReplacementNormalizer')
    MohaverekhanSeq2SeqNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanSeq2SeqNormalizer')

    normalizers['mohaverekhan-basic-normalizer'] = MohaverekhanBasicNormalizer.objects.filter(
        name='mohaverekhan-basic-normalizer').first()

    normalizers['mohaverekhan-correction-normalizer'] = MohaverekhanCorrectionNormalizer.objects.filter(
        name='mohaverekhan-correction-normalizer').first()

    normalizers['mohaverekhan-replacement-normalizer'] = MohaverekhanReplacementNormalizer.objects.filter(
        name='mohaverekhan-replacement-normalizer').first()

    normalizers['mohaverekhan-seq2seq-normalizer'] = MohaverekhanSeq2SeqNormalizer.objects.filter(
        name='mohaverekhan-seq2seq-normalizer').first()
    
    logger.info(f'>> Cached normalizers : {list(normalizers.keys())}')

def cache_taggers():
    MohaverekhanCorrectionTagger = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanCorrectionTagger')
    MohaverekhanSeq2SeqTagger = apps.get_model(
        app_label='mohaverekhan', model_name='MohaverekhanSeq2SeqTagger')

    taggers['mohaverekhan-correction-tagger'] = MohaverekhanCorrectionTagger.objects.filter(
        name='mohaverekhan-correction-tagger').first()

    taggers['mohaverekhan-seq2seq-tagger'] = MohaverekhanSeq2SeqTagger.objects.filter(
        name='mohaverekhan-seq2seq-tagger').first()
    
    logger.info(f'>> Cached taggers : {list(taggers.keys())}')



def init():
    global logger
    logger = logging.getLogger(__name__)

    cache_validators()
    cache_normalizers()
    cache_taggers()

    cache_token_tags_dic()