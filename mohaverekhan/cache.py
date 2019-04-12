import logging
import random
import re
from django.apps import apps
import time

repetition_pattern = re.compile(r"([^A-Za-z])\1{1,}")
# debug_pattern = re.compile(r'[0-9۰۱۲۳۴۵۶۷۸۹]')
# debug_pattern = re.compile(r'^گرون$|^میدون$|^خونه$|^نون$|^ارزون$|^اون$|^قلیون$')
# debug_pattern = re.compile(r'هایمان')
debug_pattern = re.compile(r'^(.)\1{5}$')

logger = None
# Word, WordNormal, Text, TextNormal = None, None, None, None
# TextTag, TagSet, Tag, Validator = None, None, None, None
# Normalizer, Tagger = None, None, None
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
tag_set_token_tags = dict()
all_token_tags = dict()

is_number_pattern = re.compile(rf"^({num})|(numf)$")

def is_token_valid(token_content):

    if is_number_pattern.fullmatch(token_content):
        logger.info(f'> Number found and added : {token_content}')
        tag_set_token_tags['bitianist-tag-set'][token_content] = {'U': 1}
        all_token_tags[token_content] = {'U': 1}
        return True, token_content

    if token_content in all_token_tags:
        return True, token_content



    nj_pattern = re.compile(r'‌')
    if nj_pattern.search(token_content):
        # logger.debug(f'> nj found in token : {token_content}')
        token_content_parts = token_content.split('‌')
        is_valid = True
        for part in token_content_parts:
            if len(part) < 3:
                is_valid = False

        fixed_token_content = token_content.replace('‌', '')
        if is_valid and fixed_token_content in all_token_tags:
            logger.debug(f'> nj replaced with empty : {fixed_token_content}')
            return True, fixed_token_content

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
    TokenTag = apps.get_model(app_label='mohaverekhan', model_name='TokenTag')
    TextTag = apps.get_model(app_label='mohaverekhan', model_name='TextTag')
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
                    # logger.info(f'> Added plural {plural_token_content} {plural_token_content}ی')
                    temp_tag_set_token_tags[tag_set_name][plural_token_content] = {'N': 1}
                    temp_tag_set_token_tags[tag_set_name][plural_token_content+'ی'] = {'N': 1}

                if token_content[-1] != 'ا':
                    informal_plural_token_content = token_content + 'ا'
                    if informal_plural_token_content not in tag_set_token_tags:
                        # logger.info(f'> Added informal plural {informal_plural_token_content} {informal_plural_token_content}ی')
                        temp_tag_set_token_tags[tag_set_name][informal_plural_token_content] = {'N': 1}
                        temp_tag_set_token_tags[tag_set_name][informal_plural_token_content+'ی'] = {'N': 1}

            if (
                len(token_content) > 2 and 
                token_content.endswith('ه‌ای')
            ):
                ie_token = token_content + 'ه'
                logger.info(f'> ie_token {token_content} {ie_token}')
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

    #Remove ه in عالیه درسته کتابه زیاده
    # old_token_set = set(token_set)
    # got_tokens = set()
    # for token in old_token_set: 
    #     if token not in got_tokens and token[-1] == 'ه' and token[0:-1] in token_set:
    #         self_score = max([value for key, value in token_tags_dic[token].items()])
    #         main_token_score = max([value for key, value in token_tags_dic[token[0:-1]].items()])
    #         # logger.info(f'> {token} {self_score} {main_token_score}')
    #         if self_score > 20 or main_token_score < 200:
    #             continue
    #         got_tokens.add(token)
    #         logger.info(f'>> D : {token} {token_tags_dic[token]} {token_tags_dic[token[0:-1]]}')
    #         # token_set.remove(token)

    # removed_tokens = [
    #     'واحده', 'کتابه', 'عالیه', 'درسته', 'زیاده', 'مثبته',
    #     'ضروریه', 'منه', 'قابله', 'مثله', 'حرفه', 'مختلفه',
    #     'اسلامیه', 'اصله', 'مالیه', 'قتله', 'عمله', 'موجبه',
    #     '', '', '', '', '', '', '', '', 
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    #     '', '', '', '', '', '', '', '',
    # ]
    # token_set.remove('واحده')
    # token_set.remove('کتابه')
    # token_set.remove('عالیه')
    # token_set.remove('درسته')
    # token_set.remove('زیاده')

    # if 'زیاده' in token_set:
    #     logger.error(f"> Can't remove زیاده کتابه درسته عالیه ...")
    
    logger.info(f'> len(temp_tag_set_token_tags) : {len(temp_tag_set_token_tags)}')
    logger.info(f'>>> Random samples')
    for tag_set, token_tags in temp_tag_set_token_tags.items():
        logger.info(f'>> tag_set : {tag_set}')
        for token in random.sample(list(token_tags), min(len(token_tags), 25)):
            logger.info(f'> {token} : {token_tags[token]}')

    
    [temp_all_token_tags.update(token_tags) for token_tags in temp_tag_set_token_tags.values()]
    # logger.info(f'> token_tags_dic samples : {set(random.sample(list(token_tags_dic), 20)) }')
    for token in temp_all_token_tags:
        if repetition_pattern.search(token):
            temp_repetition_word_set.add(token)
    # for repetition_word in temp_repetition_word_set:
    #     # logger.info(f'> repetition_word : {repetition_word}')
    #     fuck = repetition_pattern.sub(r'\1', repetition_word)
        
    #     # logger.info(f'> fuck : {fuck}')
    #     fuck1 = fuck + 'ه'
    #     fuck2 = fuck + 'و'
    #     fuck3 = fuck + 'ی'
    #     fuck4 = fuck + 'ا'

    #     if fuck1 != repetition_word and fuck1 in token_set:
    #         logger.info(f'> Fuckkkking1 : {repetition_word} - {fuck} - {fuck1}')
    #     if fuck2 != repetition_word and fuck2 in token_set:
    #         logger.info(f'> Fuckkkking2 : {repetition_word} - {fuck} - {fuck2}')
    #     if fuck3 != repetition_word and fuck3 in token_set:
    #         logger.info(f'> Fuckkkking3 : {repetition_word} - {fuck} - {fuck3}')
    #     if fuck4 != repetition_word and fuck4 in token_set:
    #         logger.info(f'> Fuckkkking4 : {repetition_word} - {fuck} - {fuck4}')
    if len(temp_repetition_word_set) != 0:
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
    logger.info('> Two length tokens')
    logger.info('\n'.join([f'{token_content} {list(all_token_tags[token_content].keys())}' for token_content in two_length_token_set]))
    # logger.info(f'> debug_pattern : {debug_pattern}')
    # for token in token_set:
    #     if debug_pattern.search(token):
    #         logger.info(token)
    # tokens = TaggedSentence.objects.only('tokens__content').order_by('-tokens__content').distinct('tokens__content')
    # logger.info(f'tokens.count() : {tokens.count()}')

# bitianist_validator = None


# def cache_bitianist_validator():
#     global bitianist_validator
#     Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')
#     bitianist_validator = Validator.objects.filter(name='bitianist-validator').first()
#     if not bitianist_validator:
#         logger.error("> There isn't bitianist-validator!")

def cache_validators():
    Validator = apps.get_model(app_label='mohaverekhan', model_name='Validator')

    validators['bitianist-validator'] = Validator.objects.filter(
        name='bitianist-validator').first()

    logger.info(f'>> Cached validators : {list(validators.keys())}')

def cache_normalizers():
    BitianistBasicNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistBasicNormalizer')
    BitianistRefinementNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistRefinementNormalizer')
    BitianistReplacementNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistReplacementNormalizer')
    BitianistSeq2SeqNormalizer = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistSeq2SeqNormalizer')

    normalizers['bitianist-basic-normalizer'] = BitianistBasicNormalizer.objects.filter(
        name='bitianist-basic-normalizer').first()

    normalizers['bitianist-refinement-normalizer'] = BitianistRefinementNormalizer.objects.filter(
        name='bitianist-refinement-normalizer').first()

    normalizers['bitianist-replacement-normalizer'] = BitianistReplacementNormalizer.objects.filter(
        name='bitianist-replacement-normalizer').first()

    normalizers['bitianist-seq2seq-normalizer'] = BitianistSeq2SeqNormalizer.objects.filter(
        name='bitianist-seq2seq-normalizer').first()
    
    logger.info(f'>> Cached normalizers : {list(normalizers.keys())}')

def cache_taggers():
    BitianistRefinementTagger = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistRefinementTagger')
    BitianistSeq2SeqTagger = apps.get_model(
        app_label='mohaverekhan', model_name='BitianistSeq2SeqTagger')

    taggers['bitianist-refinement-tagger'] = BitianistRefinementTagger.objects.filter(
        name='bitianist-refinement-tagger').first()

    taggers['bitianist-seq2seq-tagger'] = BitianistSeq2SeqTagger.objects.filter(
        name='bitianist-seq2seq-tagger').first()
    
    logger.info(f'>> Cached taggers : {list(taggers.keys())}')



def init():
    global logger
    logger = logging.getLogger(__name__)
    # cache_bitianist_validator()
    # cache_models()

    cache_validators()
    cache_normalizers()
    cache_taggers()

    cache_token_tags_dic()