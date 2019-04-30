from __future__ import unicode_literals
import os
import time
import logging
import nltk
from nltk.tag import brill, brill_trainer 
# from hazm import *
from pickle import dump, load
from django.db.models import Count, Q
from mohaverekhan.models import Tagger, Text, TextTag, TagSet
from mohaverekhan import cache


class MohaverekhanCorrectionTagger(Tagger):
    
    class Meta:
        proxy = True
    
    logger = logging.getLogger(__name__)
    
    """
    Emoji => X
    ID => S
    Link => K
    Email => M
    Tag => G
    """
    
    word_patterns = [
        (rf'^بی[{cache.persians}]+$|^بی‌[{cache.persians}]+$', 'A'),
        (rf'^.*(می{cache.nj})|(نمی).*$', 'V'), #می‌دونه نمیتونه
        (rf'^.*(ون).*$', 'N'), #میدون میدونه میتونه
        (rf'^.*(یم)|(ید)|(ند)$', 'V'),
        (rf'^.*(می)|(خواه).*$', 'V'), #می
        (r'^\\n$', 'O'), #mohaverekhan
        (rf'^({cache.num})|(cache.numf)$', 'U'),
        (rf'^[{cache.punctuations}{cache.typographies}]+$', 'O'),
        # (rf'^.*(ی)$', 'A'), # اقتصادی آمریکایی اجرایی
        # (rf'^.*(ه)$', 'A'), # خوبه عالیه خارجه
        (rf'^[{cache.emojies}]+$', 'X'), #hazm emoticons - symbols & pictographs - pushpin & round pushpin
        (rf'^({cache.id})$', 'S'), #hazm
        (rf'^({cache.link})$', 'K'), #hazm forgot "="? lol
        (rf'^({cache.email})$', 'M'), #hazm
        (rf'^({cache.tag})$', 'G'), #hazm
        # (r'^[a-zA-Z]+$', 'R'), #mohaverekhan
    ]

    current_path = os.path.abspath(os.path.dirname(__file__))

    main_tagger_path = os.path.join(current_path, 'metadata.pkl')
    main_tagger = None
    accuracy = 0
    train_data, test_data = [], []
    mohaverekhan_text_tag_index = -1

    def __init__(self, *args, **kwargs):
        super(MohaverekhanCorrectionTagger, self).__init__(*args, **kwargs)
        if os.path.isfile(self.main_tagger_path):
            self.load_trained_main_tagger()

    def save_trained_main_tagger(self):
        self.logger.info(f'>> Trying to save main tagger in "{self.main_tagger_path}"')
        output = open(self.main_tagger_path, 'wb')
        dump(self.main_tagger, output, -1)
        output.close()

    def load_trained_main_tagger(self):
        self.logger.info(f'>> Trying to load main tagger from "{self.main_tagger_path}"')
        input = open(self.main_tagger_path, 'rb')
        self.main_tagger = load(input)
        input.close()

    def separate_train_and_test_data(self, data):
        self.logger.info('>> Separate train and test data')
        self.logger.info(f'len(data) : {len(data)}')
        size = int(len(data) * 0.9)
        self.train_data = data[:size]
        self.test_data = data[size:]
        self.logger.info(f'len(train_data) : {len(self.train_data)}')
        self.logger.info(f'len(test_data) : {len(self.test_data)}')
        
    def create_main_tagger(self):
        self.logger.info('>> Create main tagger')
        default_tagger = nltk.DefaultTagger('N')
        # default_tagger = nltk.DefaultTagger('R')
        suffix_tagger = nltk.AffixTagger(self.train_data, backoff=default_tagger, affix_length=-3, min_stem_length=2, verbose=True)
        # suffix_tagger = nltk.AffixTagger(self.train_data, affix_length=-3, min_stem_length=2, verbose=True)
        # self.logger.info(f'> suffix_tagger : \n{suffix_tagger.unicode_repr()}\n')
        affix_tagger = nltk.AffixTagger(self.train_data, backoff=suffix_tagger, affix_length=5, min_stem_length=1, verbose=True)
        # affix_tagger = nltk.AffixTagger(self.train_data, affix_length=5, min_stem_length=1, verbose=True)
        regexp_tagger = nltk.RegexpTagger(self.word_patterns, backoff=affix_tagger)
        # regexp_tagger = nltk.RegexpTagger(self.word_patterns)
        unigram_tagger = nltk.UnigramTagger(self.train_data, backoff=regexp_tagger, verbose=True)
        # unigram_tagger = nltk.UnigramTagger(self.train_data, verbose=True)
        bigram_tagger = nltk.BigramTagger(self.train_data, backoff=unigram_tagger, verbose=True)
        # bigram_tagger = nltk.BigramTagger(self.train_data, verbose=True)
        trigram_tagger = nltk.TrigramTagger(self.train_data, backoff=bigram_tagger, verbose=True)
        # self.main_tagger = trigram_tagger

        templates = brill.fntbl37()
        brill_trainer_result = brill_trainer.BrillTaggerTrainer( 
                trigram_tagger, templates, deterministic=True) 
        brill_tagger = brill_trainer_result.train(self.train_data, max_rules=300, min_score=30)
        self.logger.info(f'>brill_tagger.print_template_statistics() => in console :(')
        brill_tagger.print_template_statistics()
        rules = '\n'.join([rule.__str__() for rule in brill_tagger.rules()])
        self.logger.info(f'>brill_tagger.rules() : \n{rules}')
        self.main_tagger = brill_tagger

        self.accuracy = self.main_tagger.evaluate(self.test_data)
        self.logger.info(f'>> Main tagger evaluate accuracy : {self.accuracy}')


    normalizer = None
    def train(self):
        bijankhan_tag_set = TagSet.objects.get(name='bijankhan-tag-set')
        # text_tokens_list = TextTag.objects.filter(tagger__tag_set=bijankhan_tag_set).values_list('tagged_tokens', flat=True)
        self.logger.info(f'> self.tag_set : {self.tag_set}')
        text_tokens_list = TextTag.objects.filter(
            Q(is_valid=True) &
            (Q(tagger__tag_set=self.tag_set) | Q(tagger__tag_set=bijankhan_tag_set))
        ).order_by('-tagger').values_list('tagged_tokens', flat=True)
        self.logger.info(f'> text_tokens_list.count() : {text_tokens_list.count()}')
        if text_tokens_list.count() == 0:
            self.logger.error(f'> text_tokens_list count == 0 !!!')
            return

        self.normalizer = cache.normalizers['mohaverekhan-basic-normalizer']
        tagged_sentences = []
        tagged_sentence = []
        token_content = ''
        specials = r'شلوغی فرهنگ‌سرا آیدی انقدر اوورد اووردن منو میدون خونه جوون زمونه نون مسلمون کتابخونه دندون نشون پاستا پنه تاچ تنظیمات می‌تونید سی‌پی‌یو‌ سی‌پی‌یو‌‌ها گرافیک اومدن می‌خان واس ٪ kb m kg g cm mm'.split()
        self.mohaverekhan_text_tag_index = -1
        for index, text_tokens in enumerate(text_tokens_list):
            for token in text_tokens:
                token_content = self.normalizer.normalize(token['token']).replace(' ', '‌')
                if token_content == '٪':
                    if token['tag']['name'] == 'O':
                        self.mohaverekhan_text_tag_index = index
                    token['tag']['name'] = 'O'

                if token_content in ('.', '…'):
                    token['tag']['name'] = 'O'
                    
                tagged_sentence.append((token_content, token['tag']['name']))
                # if self.mohaverekhan_text_tag_index == -1 and token_content in specials:
                #     self.logger.info(f"> He see that {token_content} {token['tag']['name']}")
                #     self.mohaverekhan_text_tag_index = 
                

                if token_content in ('.', '!', '?', '؟'):
                    tagged_sentences.append(tagged_sentence)
                    tagged_sentence = []

        self.logger.info(f'> self.mohaverekhan_text_tag_index : {self.mohaverekhan_text_tag_index}')
        self.logger.info(f'> tagged_sentences[0] : \n\n{tagged_sentences[0]}\n\n')
        self.logger.info(f'> tagged_sentences[-1] : \n\n{tagged_sentences[-1]}\n\n')
        self.separate_train_and_test_data(tagged_sentences)
        self.create_main_tagger()
        self.save_trained_main_tagger()
        self.model_details['state'] = 'ready'
        self.model_details['accuracy'] = self.accuracy
        self.save()

    
    def tag(self, text_content):
        beg_ts = time.time()
        self.logger.info(f'>>> mohaverekhan_correction_tagger : \n{text_content}')

        text_content = cache.normalizers['mohaverekhan-correction-normalizer']\
                        .normalize(text_content)
        self.logger.info(f'>>> mohaverekhan_correction_normalizer: \n{text_content}')

        token_contents = text_content.replace('\n', ' \\n ').split(' ')
        if not self.main_tagger:
            if os.path.isfile(self.main_tagger_path):
                self.load_trained_main_tagger()
            else:
                raise Exception()
        
        tagged_tokens = self.main_tagger.tag(token_contents)
        token, tag = '', ''
        most = 0
        for index, tagged_token in enumerate(tagged_tokens):
            token, tag = tagged_token
            if tag == 'R':
                if list(cache.all_token_tags[token].keys()) != ['R']:
                    most = 0
                    for key, value in cache.all_token_tags[token].items():
                        if key != 'R' and most < value:
                            most = value
                            tag = key
                            tagged_tokens[index] = (token, tag)

        end_ts = time.time()
        self.logger.info(f"> (Time)({end_ts - beg_ts:.6f})")
        self.logger.info(f'>>> Result mohaverekhan_correction_tagger : \n{tagged_tokens}')
        return tagged_tokens


