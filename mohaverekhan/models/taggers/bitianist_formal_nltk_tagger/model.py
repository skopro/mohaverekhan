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

logger = None


class BitianistFormalNLTKTagger(Tagger):
    
    class Meta:
        proxy = True
    
    """
    Emoji => X
    ID => S
    Link => K
    Email => M
    Tag => G
    """
    word_patterns = [
        (r'^\\n$', 'O'), #bitianist
        (rf'^-?[0-9{cache.numbers}]+([.,][0-9{cache.numbers}]+)?$', 'U'),
        (r'^[\.:!،؛؟»\]\)\}«\[\(\{\'\"…#+*,$@]+$', 'O'),
        (rf'^بی‌[{cache.persians}]+$|^بی [{cache.persians}]+$', 'A'),
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

    current_path = os.path.abspath(os.path.dirname(__file__))

    main_tagger_path = os.path.join(current_path, 'metadata.pkl')
    main_tagger = None
    accuracy = 0
    train_data, test_data  = [], []

    def __init__(self, *args, **kwargs):
        super(BitianistFormalNLTKTagger, self).__init__(*args, **kwargs)
        if os.path.isfile(self.main_tagger_path):
            self.load_trained_main_tagger()

    def save_trained_main_tagger(self):
        logger.info(f'>> Trying to save main tagger in "{self.main_tagger_path}"')
        output = open(self.main_tagger_path, 'wb')
        dump(self.main_tagger, output, -1)
        output.close()

    def load_trained_main_tagger(self):
        logger.info(f'>> Trying to load main tagger from "{self.main_tagger_path}"')
        input = open(self.main_tagger_path, 'rb')
        self.main_tagger = load(input)
        input.close()

    def separate_train_and_test_data(self, data):
        logger.info('>> Separate train and test data')
        logger.info(f'len(data) : {len(data)}')
        size = int(len(data) * 0.9)
        self.train_data = data[:size]
        self.test_data = data[size:]
        logger.info(f'len(train_data) : {len(self.train_data)}')
        logger.info(f'len(test_data) : {len(self.test_data)}')
        
    def create_main_tagger(self):
        logger.info('>> Create main tagger')
        default_tagger = nltk.DefaultTagger('N')
        # default_tagger = nltk.DefaultTagger('R')
        suffix_tagger = nltk.AffixTagger(self.train_data, backoff=default_tagger, affix_length=-3, min_stem_length=2, verbose=True)
        logger.info(f'> suffix_tagger : \n{suffix_tagger.unicode_repr()}\n')
        affix_tagger = nltk.AffixTagger(self.train_data, backoff=suffix_tagger, affix_length=5, min_stem_length=1, verbose=True)
        regexp_tagger = nltk.RegexpTagger(self.word_patterns, backoff=affix_tagger)
        unigram_tagger = nltk.UnigramTagger(self.train_data, backoff=regexp_tagger, verbose=True)
        bigram_tagger = nltk.BigramTagger(self.train_data, backoff=unigram_tagger, verbose=True)
        trigram_tagger = nltk.TrigramTagger(self.train_data, backoff=bigram_tagger, verbose=True)
        # main_tagger = trigram_tagger

        templates = brill.fntbl37()
        brill_trainer_result = brill_trainer.BrillTaggerTrainer( 
                trigram_tagger, templates, deterministic=True) 
        brill_tagger = brill_trainer_result.train(self.train_data, max_rules=300, min_score=10)
        logger.info(f'>brill_tagger.print_template_statistics() => in console :(')
        brill_tagger.print_template_statistics()
        rules = '\n'.join([rule.__str__() for rule in brill_tagger.rules()])
        logger.info(f'>brill_tagger.rules() : \n{rules}')
        self.main_tagger = brill_tagger

        self.accuracy = self.main_tagger.evaluate(self.test_data)
        logger.info(f'>> Main tagger evaluate accuracy : {self.accuracy}')


    temp_text, normalizer = None, None
    def refine_training_token(self, token_content):
        self.temp_text.content = token_content
        self.normalizer.uniform_signs(self.temp_text)
        self.normalizer.remove_some_characters(self.temp_text)
        self.temp_text.content = self.temp_text.content.strip()
        self.temp_text.content = self.temp_text.content.replace(' ', '‌')
        token_content = self.temp_text.content
        return token_content

    def train(self):
        bijankhan_tag_set = TagSet.objects.get(name='bijankhan-tag-set')
        text_tokens_list = TextTag.objects.filter(tagger__tag_set=bijankhan_tag_set).values_list('tokens', flat=True)
            # Q(is_valid=True) &
            # (Q(tagger__tag_set=self.tag_set) | 
            # Q(tagger__tag_set=bijankhan_tag_set)
        # )
        # ).values_list('tokens', flat=True)
        logger.info(f'> text_tokens_list.count() : {text_tokens_list.count()}')
        if text_tokens_list.count() == 0:
            logger.error(f'> text_tokens_list count == 0 !!!')
            return

        self.normalizer = cache.normalizers['bitianist-informal-refinement-normalizer']
        self.temp_text = Text()
        tagged_sentences = []
        tagged_sentence = []
        token_content = ''
        for text_tokens in text_tokens_list:
            for token in text_tokens:
                token_content = self.refine_training_token(token['content'])
                tagged_sentence.append((token_content, token['tag']['name']))
                if token_content in ('.', '!', '?', '؟'):
                    tagged_sentences.append(tagged_sentence)
                    tagged_sentence = []

        logger.info(f'> tagged_sentences[:20] : \n\n{tagged_sentences[:20]}\n\n')
        self.separate_train_and_test_data(tagged_sentences)
        self.create_main_tagger()
        self.save_trained_main_tagger()
        self.model_details['state'] = 'ready'
        self.model_details['accuracy'] = self.accuracy
        self.save()

    
    def tag(self, text):
        text_tag = cache.tokenizers['bitianist-informal-tokenizer']\
                            .tokenize(text)
        text_tag.tagger = self
        token_contents = [token['content'] for token in text_tag.tokens]
        if not self.main_tagger:
            if os.path.isfile(self.main_tagger_path):
                self.load_trained_main_tagger()
            else:
                raise Exception()
        
        tagged_tokens = self.main_tagger.tag(token_contents)
        for i in range(len(text_tag.tokens)):
            text_tag.tokens[i]['tag'] = {'name': tagged_tokens[i][1]}
        text_tag.save()
        logger.info(f'text tags : {text_tag.__unicode__()}')
        return text_tag

def init():
    global logger
    logger = logging.getLogger(__name__)

    # def get_or_create_sentences(self, text):
    #     if text.sentences.exists():
    #         logger.debug(f'> sentence was exists')
    #         return False
    #     text_content = sentence_splitter_pattern.sub(r' \1\2 newline', text.content) # hazm
    #     sentence_contents = [sentence_content.replace('\n', ' ').strip() \
    #         for sentence_content in text_content.split('newline') if sentence_content.strip()] #hazm
    #     order = 0
    #     for sentence_content in sentence_contents:
    #         Sentence.objects.create(content=sentence_content, text=text, order=order)
    #         logger.debug(f'> new sentence : {sentence_content}')
    #         order += 1
    #     return True

    # def tag(self, text):
    #     created = self.get_or_create_sentences(text)
    #     tagged_sentence = None
    #     for sentence in text.sentences.all():
    #         tagged_sentence, created = TaggedSentence.objects.get_or_create(
    #                             tagger=self, 
    #                             sentence=sentence
    #                             )
    #         token_contents = split_into_token_contents(tagged_sentence.sentence.content)
    #         tagged_tokens = nltk_taggers_model.tag(token_contents)
    #         token_dictionary = {}
    #         for tagged_token in tagged_tokens:
    #             token_dictionary = {
    #                 'content': tagged_token[0],
    #                 'tag': {
    #                     'name': tagged_token[1]
    #                 }
    #             }
    #             tagged_sentence.tokens.append(token_dictionary)
    #         tagged_sentence.save()
    #         logger.info(f'{tagged_sentence.__unicode__()}')
    #     return text
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


