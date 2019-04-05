from __future__ import unicode_literals
import os
import logging
import nltk
from nltk.tag import brill, brill_trainer 
# from hazm import *
from pickle import dump, load
from django.db.models import Count, Q
from mohaverekhan.models import Tagger, Text, TextTag, TagSet
from mohaverekhan import cache
from mohaverekhan import utils

logger = None
# logger = utils.get_logger(logger_name='nltk_taggers')
# logger.info('-------------------------------------------------------------------')




punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
numbers = r'۰۱۲۳۴۵۶۷۸۹'
persians = 'اآب‌پتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'

"""
Emoji => X
ID => S
Link => K
Email => M
Tag => G
"""
WORD_PATTERNS = [
    (r'^-?[0-9۰۱۲۳۴۵۶۷۸۹]+([.,][0-9۰۱۲۳۴۵۶۷۸۹]+)?$', 'U'),
    (r'^[\.:!،؛؟»\]\)\}«\[\(\{\'\"…#+*,$@]+$', 'O'),
    (rf'^بی‌[{persians}]+$|^بی [{persians}]+$', 'A'),
    (r'^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F4CC\U0001F4CD]+$', 'X'), #hazm emoticons - symbols & pictographs - pushpin & round pushpin
    (r'^([^\w\._]*)(@[\w_]+).*$', 'S'), #hazm
    (r'^((https?|ftp):\/\/)?(?<!@)([wW]{3}\.)?(([\w-]+)(\.(\w){2,})+([-\w@:%_\+\/~#?&=]+)?)$', 'K'), #hazm forgot "="? lol
    (r'^[a-zA-Z0-9\._\+-]+@([a-zA-Z0-9-]+\.)+[A-Za-z]{2,}$', 'M'), #hazm
    (r'^\#([\S]+)$', 'G'), #hazm
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

MAIN_TAGGER_PATH = os.path.join(CURRENT_PATH, 'metadata.pkl')
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
    suffix_tagger = nltk.AffixTagger(train_data, backoff=default_tagger, affix_length=-3, min_stem_length=2, verbose=True)
    logger.info(f'> suffix_tagger : \n{suffix_tagger.unicode_repr()}\n')
    affix_tagger = nltk.AffixTagger(train_data, backoff=suffix_tagger, affix_length=5, min_stem_length=1, verbose=True)
    regexp_tagger = nltk.RegexpTagger(WORD_PATTERNS, backoff=affix_tagger)
    unigram_tagger = nltk.UnigramTagger(train_data, backoff=regexp_tagger, verbose=True)
    bigram_tagger = nltk.BigramTagger(train_data, backoff=unigram_tagger, verbose=True)
    trigram_tagger = nltk.TrigramTagger(train_data, backoff=bigram_tagger, verbose=True)
    # main_tagger = trigram_tagger

    templates = brill.fntbl37()
    brill_trainer_result = brill_trainer.BrillTaggerTrainer( 
            trigram_tagger, templates, deterministic=True) 
    brill_tagger = brill_trainer_result.train(train_data, max_rules=300, min_score=10)
    logger.info(f'>brill_tagger.print_template_statistics() => in console :(')
    brill_tagger.print_template_statistics()
    rules = '\n'.join([rule.__str__() for rule in brill_tagger.rules()])
    logger.info(f'>brill_tagger.rules() : \n{rules}')
    main_tagger = brill_tagger

    accuracy = main_tagger.evaluate(test_data)
    logger.info(f'>> Main tagger evaluate accuracy : {accuracy}')
    return main_tagger, accuracy

def train(tagged_sentences):
    try:
        global TAG_EXAMPLE_DIC, MAIN_TAGGER
        train_data, test_data = separate_train_and_test_data(tagged_sentences)
        MAIN_TAGGER, accuracy = create_main_tagger(train_data, test_data)
        save_trained_main_tagger()
        return accuracy
    except Exception as ex:
        logger.exception(ex)

def tag(tokens):
    global MAIN_TAGGER

    logger.info(f'> Tokens : {tokens}')
    if not MAIN_TAGGER:
        if os.path.isfile(MAIN_TAGGER_PATH):
            load_trained_main_tagger()
        else:
            raise Exception()
    
    tags = MAIN_TAGGER.tag(tokens)
    # logger.info(f'>brill_tagger.print_template_statistics() : \n{MAIN_TAGGER.print_template_statistics(printunused=False)}')
    return tags


class BitianistFormalNLTKTagger(Tagger):
    
    class Meta:
        proxy = True
    
    temp_text, normalizer = None, None
    def refine_training_token(self, token):
        token_content = token['content']
        token_tag_name = token['tag']['name']
        self.temp_text.content = token_content
        self.normalizer.uniform_signs(self.temp_text)
        self.normalizer.remove_some_characters(self.temp_text)
        self.temp_text.content = self.temp_text.content.strip()
        self.temp_text.content = self.temp_text.content.replace(' ', '‌')
        token_content = self.temp_text.content
        return (token_content, token_tag_name)

    def train(self):
        bijankhan_tag_set = TagSet.objects.get(name='bijankhan-tag-set')
        tagged_sentences = TaggedSentence.objects.filter(
            Q(is_valid=True) &
            (Q(tagger__tag_set=self.tag_set) | Q(tagger__tag_set=bijankhan_tag_set))
            )
            # .filter(tagger__tag_set=bijankhan_tag_set, is_valid=True)
            # .filter(tagger__tag_set=self.tag_set, is_valid=True)\
        logger.info(f'> tagged_sentences.count() : {tagged_sentences.count()}')
        if tagged_sentences.count() == 0:
            logger.error(f'> tagged_sentences count == 0 !!!')
            return

        self.normalizer = RefinementNormalizer.objects.get(name='refinement-normalizer')
        self.temp_text = Text()
        # tagged_sentences = [[(self.refine_training_token(token['content']), token['tag']['name']) \
        tagged_sentences = [[self.refine_training_token(token) \
            for token in tagged_sentence.tokens] \
            for tagged_sentence in tagged_sentences]
        logger.info(f'> tagged_sentences[:20] : \n\n{tagged_sentences[:20]}\n\n')
        nltk_taggers_model.train(tagged_sentences)
        self.model_details['state'] = 'trained'
        self.save()

    def get_or_create_sentences(self, text):
        if text.sentences.exists():
            logger.debug(f'> sentence was exists')
            return False
        text_content = sentence_splitter_pattern.sub(r' \1\2 newline', text.content) # hazm
        sentence_contents = [sentence_content.replace('\n', ' ').strip() \
            for sentence_content in text_content.split('newline') if sentence_content.strip()] #hazm
        order = 0
        for sentence_content in sentence_contents:
            Sentence.objects.create(content=sentence_content, text=text, order=order)
            logger.debug(f'> new sentence : {sentence_content}')
            order += 1
        return True

    def tag(self, text):
        created = self.get_or_create_sentences(text)
        tagged_sentence = None
        for sentence in text.sentences.all():
            tagged_sentence, created = TaggedSentence.objects.get_or_create(
                                tagger=self, 
                                sentence=sentence
                                )
            token_contents = split_into_token_contents(tagged_sentence.sentence.content)
            tagged_tokens = nltk_taggers_model.tag(token_contents)
            token_dictionary = {}
            for tagged_token in tagged_tokens:
                token_dictionary = {
                    'content': tagged_token[0],
                    'tag': {
                        'name': tagged_token[1]
                    }
                }
                tagged_sentence.tokens.append(token_dictionary)
            tagged_sentence.save()
            logger.info(f'{tagged_sentence.__unicode__()}')
        return text
        # for sentence in text.sentences:
        #     self.tag_sentence(sentence)
            
        #     tagged_sentence.split_to_tokens()

        # sentence_tokens = [
        #     ("خیلی", "A"),
        #     ("افتضاح", "A"),
        #     ("است", "V"),
        #     (".", "O")
        # ]
        # sentence_tokens = [
        #     {
        #         'content':token, 
        #         'tag':
        #         {
        #             'name': tag
        #         }
        #     } for token, tag in sentence_tokens]
        # logger.info(f'sentence_tokens : \n\n{sentence_tokens}\n')

        # obj, created = TaggedSentence.objects.update_or_create(
        #     tagger=self, sentence=sentence,
        #     defaults={'tokens': sentence_tokens},
        # )
        # logger.debug(f"> created : {created}")

        # TaggedSentence.objects.create(
        #     tagger=self,
        #     sentence=sentence,
        #     tokens=sentence_tokens
        # )
        # return text


def init():
    global logger
    logger = logging.getLogger(__name__)
    if os.path.isfile(MAIN_TAGGER_PATH):
        load_trained_main_tagger()