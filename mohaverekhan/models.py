import uuid
import json
from collections import OrderedDict
import logging
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django import forms
from .core.nltk_taggers import model as nltk_taggers_model
from .core.seq2seq import model as seq2seq_model
from colorfield.fields import ColorField
from django.db.models import Count
import time
import datetime
import re

logger = None

from django.contrib.postgres.forms.jsonb import (
    InvalidJSONInput,
    JSONField as JSONFormField,
)

sentence_splitter_pattern = re.compile(r'([!\.\?⸮؟]+)')


class UTF8JSONFormField(JSONFormField):

    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return json.dumps(value, ensure_ascii=False, indent=4,)

class UTF8JSONField(JSONField):
    """JSONField for postgres databases.

    Displays UTF-8 characters directly in the admin, i.e. äöü instead of
    unicode escape sequences.
    """

    def formfield(self, **kwargs):
        return super().formfield(**{
            **{'form_class': UTF8JSONFormField},
            **kwargs,
        })

MANUAL = 'manual'
RULEBASED = 'rule-based'
STOCHASTIC = 'stochastic'
MODEL_TYPES = (
    (MANUAL, MANUAL),
    (RULEBASED, RULEBASED),
    (STOCHASTIC, STOCHASTIC),
)

# باید فاصله تو توکن ها رو تبدیل به نیم فاصله کنم تو ایمورت داده ها

class Normalizer(models.Model):
    name = models.SlugField(default='unknown-normalizer', unique=True)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.CharField(max_length=100, default='undefined')
    model_type = models.CharField(max_length=15, choices=MODEL_TYPES, default=MANUAL)
    last_update = models.DateTimeField(auto_now=True)
    model_details = UTF8JSONField(default=dict, blank=True) # contains model training details

    class Meta:
        verbose_name = 'Normalizer'
        verbose_name_plural = 'Normalizers'
        ordering = ('-created',)
    
    def __str__(self):
        return  self.name

    @property
    def total_normal_text_count(self):
        return self.normal_texts.count()

    @property
    def total_valid_normal_text_count(self):
        return self.normal_texts.filter(is_valid=True).count()

    def normalize(self, text):
        normal_text_content = text.content
        normal_text, created = NormalText.objects.update_or_create(
            normalizer=self, text=text,
            defaults={'content':normal_text_content},
        )
        logger.debug(f"> created : {created}")
        return normal_text

compile_patterns = lambda patterns: [(re.compile(pattern), repl) for pattern, repl in patterns]


class RefinementNormalizer(Normalizer):
    
    class Meta:
        proxy = True

    translation_characters = (
        (r' ', r' ', 'space character 160 -> 32', 'hazm', 'true'),
        (r'ك', r'ک', '', 'hazm', 'true'),
        (r'ي', r'ی', '', 'hazm', 'true'),
        (r'“', r'"', '', 'hazm', 'true'),
        (r'”', r'"', '', 'hazm', 'true'),
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
        (r'%', r'٪', '', 'hazm', 'true'),
        (r'?', r'؟', '', 'hazm', 'true'),
    )
    translation_characters = {tc[0]:tc[1] for tc in translation_characters}

    punctuations = r'\.:!،؛؟»\]\)\}«\[\(\{\'\"…'
    repetition_characters = r'یو'

    refinement_patterns = (
        (r'([^\.]|^)(\.\.\.)([^\.]|$)', r'\1…\3', 'replace 3 dots with …', 0, 'bitianist', 'true'),
        (rf'([^{repetition_characters}])\1{{1,}}', r'\1', 'remove repetitions except ی و', 0, 'bitianist', 'true'),
        (r'[ـ\r]', r'', 'remove keshide', 0, 'hazm', 'true'),
        (r'[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652]', r'', 'remove FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN', 0, 'hazm', 'true'),
        (r'"([^\n"]+)"', r'«\1»', 'replace quotation with gyoome', 0, 'hazm', 'true'),
        (rf'([{punctuations}])', r' \1 ', 'add extra space before and after of punctuations', 0, 'bitianist', 'true'),
        (r' +', r' ', 'remove extra spaces', 0, 'hazm', 'true'),
        (r'\n+', r'\n', 'remove extra newlines', 0, 'bitianist', 'true'),
        (r'([^ ]ه) ی ', r'\1‌ی ', 'between ی and ه - replace space with non-joiner ', 0, 'hazm', 'true'),
        (r'(^| )(ن?می) ', r'\1\2‌', 'after می،نمی - replace space with non-joiner ', 0, 'hazm', 'true'),
        (rf'(?<=[^\n\d {punctuations}]{2}) (تر(ین?)?|گری?|های?)(?=[ \n{punctuations}]|$)', r'‌\1', 'before تر, تری, ترین, گر, گری, ها, های - replace space with non-joiner', 0, 'hazm', 'true'),
        (rf'([^ ]ه) (ا(م|یم|ش|ند|ی|ید|ت))(?=[ \n{punctuations}]|$)', r'\1‌\2', 'before ام, ایم, اش, اند, ای, اید, ات - replace space with non-joiner', 0, 'hazm', 'true'),  
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
        # (r'', r'', '', 0, 'hazm', 'true'),
    )
    refinement_patterns = [(rp[0], rp[1]) for rp in refinement_patterns]
    refinement_patterns = compile_patterns(refinement_patterns)


    def uniform_signs(self, text):
        text.content = text.content.translate(text.content.maketrans(self.translation_characters))
        logger.info(f'> After uniform_signs : \n{text.content}')

    def refine_text(self, text):
        for pattern, replacement in self.refinement_patterns:
            text.content = pattern.sub(replacement, text.content)
            logger.info(f'> after {pattern} -> {replacement} : \n{text.content}')

    def normalize(self, text):
        logger.info(f'>> RefinementRuleBasedNormalizer : \n{text}')
        normal_text, created = NormalText.objects.get_or_create(
            text=text, 
            normalizer=self
            )
        normal_text.content = text.content.strip()
        self.uniform_signs(normal_text)
        self.refine_text(normal_text)
        normal_text.content = normal_text.content.strip()
        normal_text.save()
        logger.info(f'>> Result : \n{text}')
        # text = normalizer.normalize(text)
        return normal_text
    
class Text(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    normalizers = models.ManyToManyField(Normalizer, through='NormalText', related_name='texts', 
                            related_query_name='text', blank=True, through_fields=('text', 'normalizer'),)
    is_normal_text = models.BooleanField(default=False, blank=True)

    class Meta:
        verbose_name = 'Text'
        verbose_name_plural = 'Texts'
        ordering = ('-created',)

    def __str__(self):
        return f'{self.content[:50]}{" ..." if len(self.content) > 50 else ""}'

    def create_sentences(self):
        text = sentence_splitter_pattern.sub(r'\1\n\n', self.content)
        sentences = [sentence.replace('\n', ' ').strip() for sentence in text.split('\n\n') if sentence.strip()]
        order = 0
        for sentence in sentences:
            Sentence.objects.create(content=sentence, text=self, order=order)
            order += 1
    
class NormalText(Text):
    is_valid = models.BooleanField(default=False, blank=True)
    normalizer = models.ForeignKey(Normalizer, on_delete=models.CASCADE, related_name='normal_texts', related_query_name='normal_text')
    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='normal_texts', related_query_name='normal_text')

    class Meta:
        verbose_name = 'Normal Text'
        verbose_name_plural = 'Normal Texts'
        ordering = ('-created',)

    def save(self, *args, **kwargs):
        self.is_normal_text = True
        self.is_valid = False
        if self.normalizer:
            if self.normalizer.model_type == MANUAL:
                self.is_valid = True
        super(NormalText, self).save(*args, **kwargs)

def get_unknown_tag():
    return {'name':'unk', 'persian':'نامشخص', 'color':'#FFFFFF', 'examples':[]}

class TagSet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.SlugField(default='unknown-tag-set', unique=True)
    unknown_tag = UTF8JSONField(blank=True, default=get_unknown_tag)

    def __str__(self):  
        return self.name

    @property
    def total_tagged_sentence_count(self):
        return sum([tagger.total_tagged_sentence_count for tagger in self.taggers.all()])
    
    @property
    def total_valid_tagged_sentence_count(self):
        return sum([tagger.total_valid_tagged_sentence_count for tagger in self.taggers.all()])
    
    @property
    def number_of_tags(self):
        return self.tags.count()

    @property
    def number_of_taggers(self):
        return self.taggers.count()

    def add_to_unknown_tag_examples(self, token_content):
        examples = self.unknown_tag['examples']
        if (token_content not in examples 
                and len(examples) < 15 ):
            self.unknown_tag['examples'].append(token_content)
            self.save(update_fields=['unknown_tag']) 

    class Meta:
        verbose_name = 'Tag Set'
        verbose_name_plural = 'Tag Sets'
        ordering = ('-created',)

class Tag(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=15, default='unk')
    persian = models.CharField(max_length=30, default='نامشخص')
    color = ColorField(default='#FF0000')
    tag_set = models.ForeignKey(to=TagSet, on_delete=models.DO_NOTHING, related_name='tags', related_query_name='tag')
    examples = ArrayField(models.CharField(max_length=30), blank=True, default=list)

    def __str__(self):  
        return self.name

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ('-created',)
        unique_together = (("name", "persian"), ("name", "color"), ("name", "tag_set"))

    def add_to_examples(self, token_content):
        if (token_content not in self.examples 
                and len(self.examples) < 15 ):
            self.examples.append(token_content)
            self.save(update_fields=['examples']) 

class Tagger(models.Model):
    name = models.SlugField(default='unknown-tagger', unique=True)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.CharField(max_length=100, default='undefined')
    model_type = models.CharField(max_length=15, choices=MODEL_TYPES, default=MANUAL)
    last_update = models.DateTimeField(auto_now=True)
    model_details = UTF8JSONField(default=dict, blank=True) # contains model training details
    tag_set = models.ForeignKey(to=TagSet, on_delete=models.DO_NOTHING, related_name='taggers', related_query_name='tagger')

    class Meta:
        verbose_name = 'Tagger'
        verbose_name_plural = 'Taggers'
        ordering = ('-created',)
    
    @property
    def total_tagged_sentence_count(self):
        return self.tagged_sentences.count()
    
    @property
    def total_valid_tagged_sentence_count(self):
        return self.tagged_sentences.filter(is_valid=True).count()

    def __str__(self):
        return self.name

    def learn_model(self):
        num_epochs = 150
        logger.info(f'Model is going to train for {num_epochs} epochs.')
        seq2seq_model.train(False, num_epochs=num_epochs)

    
    def tag_sentence(self, sentence):

        tagged_sentence = TaggedSentence.objects.get_or_create(
                tagger=self,
                sentence=sentence,
        )

    def tag_text(self, text):
        if text.sentences.exists():
            logger.debug(f'> sentence was exists')
        else:
            text.create_sentences()

        for sentence in text.sentences:
            self.tag_sentence(sentence)
            
            tagged_sentence.split_to_tokens()

        sentence_tokens = [
            ("خیلی", "A"),
            ("افتضاح", "A"),
            ("است", "V"),
            (".", "O")
        ]
        sentence_tokens = [
            {
                'content':token, 
                'tag':
                {
                    'name': tag
                }
            } for token, tag in sentence_tokens]
        logger.info(f'sentence_tokens : \n\n{sentence_tokens}\n')

        obj, created = TaggedSentence.objects.update_or_create(
            tagger=self, sentence=sentence,
            defaults={'tokens': sentence_tokens},
        )
        logger.debug(f"> created : {created}")

        # TaggedSentence.objects.create(
        #     tagger=self,
        #     sentence=sentence,
        #     tokens=sentence_tokens
        # )
        return text

    def infpost(self):
        try:
            logger.info(f'> Informal : {self.content}')
            sentence_contents, token_tags = nltk_taggers_model.tag_text(self.content)
            logger.info(f'> sentence_contents : {sentence_contents}')
            logger.info(f'> token_tags : {token_tags}')
            sentences, tokens = [], []
            current_sentence, current_tag, current_token = None, None, None
            for i, sentence_content in enumerate(sentence_contents):
                print(f'> sentence_contents[{i}] : {sentence_content}')
                current_sentence = Sentence(content=sentence_content)
                print(f'> current_sentence : {current_sentence} {type(current_sentence)}')
                tokens = []
                for token_tag in token_tags[i]:
                    print(f'> token_tag : {token_tag}')
                    print(f'> token_tag[0] : {token_tag[0]}')
                    print(f'> token_tag[1] : {token_tag[1]}')
                    current_tag = Tag.objects.get(name=token_tag[1])
                    logger.info(f'> current_tag : {current_tag}')
                    current_token = Token(content=token_tag[0], tag=current_tag)
                    current_token.save()
                    tokens.append(current_token)
                    logger.info(f'> current_token : {current_token}')

                current_sentence.tokens = tokens
                current_sentence.save()
                logger.info(f'> current_sentence.tokens : {current_sentence.tokens}')
                sentences.append(current_sentence)

            self.sentences = sentences
            logger.info(f'> self.sentences : {self.sentences}')
            Text.objects.update_or_create(
                content=self.content, 
                defaults={'sentences': self.sentences},
                )
            # self.save()
            logger.info(f'> Text : {self}')
        except Exception as ex:
            logger.exception(ex)

# class MohaverekhanTagger
class Sentence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    taggers = models.ManyToManyField(Tagger, through='TaggedSentence', related_name='sentences', related_query_name='sentence', blank=True)
    text = models.ForeignKey(to=Text, on_delete=models.SET_NULL, related_name='sentences', related_query_name='sentence', blank=True, null=True)
    order = models.IntegerField(default=0, blank=True)

    class Meta:
        verbose_name = 'Sentence'
        verbose_name_plural = 'Sentences'
        ordering = ('order', '-created')

    def __str__(self):
        rep = f'{self.content[:200]}{" ..." if len(self.content) > 200 else ""}'
        return rep
    
class TaggedSentence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    tagger = models.ForeignKey(Tagger, on_delete=models.CASCADE, related_name='tagged_sentences', related_query_name='tagged_sentence')
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='tagged_sentences', related_query_name='tagged_sentence')
    tokens = UTF8JSONField(default=list) # contains list of token with it's tag
    is_valid = models.BooleanField(default=False, blank=True)
    
    class Meta:
        verbose_name = 'Tagged Sentence'
        verbose_name_plural = 'Tagged Sentences'
        ordering = ('-created',)

    def is_tokens_valid(self):
        is_valid = True
        for token in self.tokens:
            if 'is_valid' not in token:
                token['is_valid'] = False
                break
            is_valid = is_valid and token['is_valid']
            if not is_valid:
                break
        return is_valid
    
    def check_validation(self):
        self.is_valid = False
        if self.tagger:
            if not self.tagger.model_type == MANUAL:
                self.is_valid = self.is_tokens_valid()
            else:
                self.is_valid = True
                for token in self.tokens:
                    token['is_valid'] = True

    def set_tag_details(self):
        tag_details_dictionary = {tag.name:tag for tag in self.tagger.tag_set.tags.all()}
        referenced_tag = None
        for token in self.tokens:
            if ('tag' not in token 
                or 'name' not in token['tag'] 
                or token['tag']['name'] not in tag_details_dictionary):
                
                token['tag'] = self.tagger.tag_set.unknown_tag
                self.tagger.tag_set.add_to_unknown_tag_examples(token['content'])
                continue

            referenced_tag = tag_details_dictionary[token['tag']['name']]
            referenced_tag.add_to_examples(token['content'])
            token['tag']['persian'] = referenced_tag.persian
            token['tag']['color'] = referenced_tag.color

    def save(self, *args, **kwargs):
        self.check_validation()
        self.set_tag_details()
        super(TaggedSentence, self).save(*args, **kwargs)

    def __unicode__(self):
        rep = ""
        if self.tokens:
            for token in self.tokens:
                rep += f'{token["content"]}_{token["tag"]["name"]} '
        return rep
    
    def split_to_tokens(self):
        pass

class TranslationCharacter(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=2, unique=True)
    destination = models.CharField(max_length=2)
    description = models.TextField(blank=True)
    owner = models.CharField(max_length=75)
    is_valid = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Translation Character'
        verbose_name_plural = 'Translation Characters'
        ordering = ('-created',)

    def __str__(self):
        return f'''
            ({self.source}, {self.destination}, {self.description}, {self.description}, 
            {self.owner}, {self.is_valid})
            '''

class RefinementPattern(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    pattern = models.CharField(max_length=200, unique=True)
    replacement = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=9999, unique=True)
    owner = models.CharField(max_length=75)
    is_valid = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Refinement Pattern'
        verbose_name_plural = 'Refinement Patterns'
        ordering = ('order',)

    def __str__(self):
        return f'''
            ({self.pattern}, {self.replacement}, {self.description}, {self.order}, 
            {self.owner}, {self.is_valid})
            '''



def init():
    global logger
    logger = logging.getLogger(__name__)

    # logger.info(f'> count of normal text list : {NormalText.objects.count()}')
    # logger.info(f'> count of text list : {Text.objects.count()}')

    # same_text_count = NormalText.objects.order_by('text_id').distinct('text').count()
    # logger.info(f'> same_text_count : {same_text_count}')
    # logger.info(f'> same_text_count : {same_text_count.count()}')

    # same_text = Text.objects.values('normal_text')
    # same_text = same_text.annotate(same_text_count=Count('normal_text'))
    # same_text = Text.objects.annotate(Count('normal_text'))
    # same_text = same_text.filter(normal_text__count__gt=1)
    # logger.info(f'> same_text : {same_text.values("id", "content")}')
    
    # empty_text = NormalText.objects.filter(text__exact=None)
    # logger.info(f'> empty_text : {empty_text}')
    
    # text = Text.objects.get(id='eb3bc179-7a8c-4a5e-b6bc-9556983fd45c')
    # logger.info(f'> text : {text}') 
    # for sentence in text.sentences.all():
    #     logger.info(f'> sentence : {sentence.content}') 

"""
from mohaverekhan.models import Text, Sentence, Tag, Token
from mohaverekhan.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
text = Text.objects.create(content="سلام. چطوری خوبی؟")
serializer = TextSerializer(text)
serializer.data
sentence1 = Sentence.objects.create(content="سلام.")
serializer = SentenceSerializer(sentence1)
serializer.data
text.sentences.add(sentence1)
serializer = TextSerializer(text)
serializer.data

from mohaverekhan.models import Text, Sentence, Tag, Token
from mohaverekhan.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
text = Text.objects.create(content="سلام. چطوری خوبی؟")
serializer = TextSerializer(text)
serializer.data
sentence1 = Sentence.objects.create(content="سلام.")
serializer = SentenceSerializer(sentence1)
serializer.data
text.sentences = sentence1
text.save()
serializer = TextSerializer(text)
serializer.data


from mohaverekhan.models import Text, Sentence, Tag, Token
from mohaverekhan.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
text = Text(content="سلام. چطوری خوبی؟")
text.save()
serializer = TextSerializer(text)
serializer.data
sentence1 = Sentence(content="سلام.")
sentence1.save()
serializer = SentenceSerializer(sentence1)
serializer.data
text.sentences.add(sentence1)
serializer = TextSerializer(text)
serializer.data


sentence2 = Sentence.objects.create(text=text, content="چطوری خوبی؟")
tag1 = Tag.objects.create(name="V")
tag2 = Tag.objects.create(name="N")
tag3 = Tag.objects.create(name="E")
token1 = Token.objects.create(sentence=sentence1, content="سلام", tag=tag1)
token1


text = Text.objects.get(pk=1)
text
"""




"""
E : ['با', 'در', 'به', 'از', 'برای', 'علیرغم', 'جز', 'در مقابل', 'پس از', 'تا', 'بر', 'به دنبال', 'از نظر', 'جهت', 'در پی', 'میان', 'به عنوان', 'تحت', 'از طریق', 'به دست', 'بر اساس', 'در جهت', 'از سوی', 'در زمینه', 'زیر', 'در معرض', 'به جای', 'وارد', 'از جمله', 'درباره', 'بدون', 'فرا', 'به صورت', 'به خاطر', 'پیرامون', 'در مورد', 'طی', 'روی', 'قبل از', 'توسط', 'بعد', 'مقابل', 'از روی', 'در حضور', 'به رغم', 'به دلیل', 'برابر', 'در برابر', 'با توجه به', 'به نفع']
Noun - اسم - N : ['قدرت', 'یهودیها', 'انگلیس', 'وجود', 'فضای', 'سو', 'مطبوعات', 'کشور', 'نیاز', 'منابع', 'چیز', 'رشد', 'رویتر', 'فراهم', 'موقعیتی', 'سال', 'جلیوس', 'دفتر', 'نزدیکی', 'بازار', 'بورس', 'لندن', 'گشایش', 'عده', 'یهودیهای', 'آلمان', 'دعوت', 'کار', 'عهده', 'بازاریابی', 'معرفی', 'خبرگزاری', 'پترزبورگ', 'سفر', 'نامه ای', 'نیکولای', 'گریش', 'سردبیران', 'نشریات', 'جائی', 'سردبیر', 'درک', 'پل', 'استوف', 'استقبال', 'قراردادی', 'مبلغ', 'روبل', 'امضاء', 'خدمات']
Verb - فعل - V : ['گرفتن', 'آمدن', 'شدن', 'شده', 'بود', 'کرد', 'شدند', 'گرفتند', 'نوشت', 'نداشت', 'رساند', 'دهد', 'آورده', 'نبودند', 'می توانست', 'باشد', 'است', 'بودن', 'گردید', 'آوردند', 'یافت', 'توانسته', 'کند', 'نمی توانست', 'شود', 'بودند', 'بردن', 'نمود', 'کردند', 'می شد', 'می داشت', 'نیاورد', 'زدند', 'می کردند', 'داشت', 'کنند', 'آمد', 'بست', 'کردن', 'رفت', 'می کرد', 'گرفته', 'دادن', 'کندن', 'شد', 'افتاد', 'می گریختند', 'نمی شناختند', 'ریخت', 'آمدند']
J : ['و', 'از سوی دیگر', 'که', 'هم', 'درعین حال', 'اگر', 'لذا', 'ولی', 'هرچند', 'نیز', 'سپس', 'درحالیکه', 'چون', 'تا', 'هم چنین', 'اما', 'وقتی', 'یا', 'هنگامی که', 'تاآنجاکه', 'درحالی که', 'چراکه', 'چنانچه', 'در حالی که', 'همچنین', 'چنانکه', 'گرچه', 'به طوری که', 'به این ترتیب', 'نه فقط', 'بلکه', 'بنابراین', 'از آنجا که', 'ضمناً', 'اگرچه', 'نه تنها', 'زیرا', 'همانطورکه', 'در صورتی که', 'پس', 'باآنکه', 'به طوریکه', 'بدین ترتیب', 'یعنی', 'چنان که', 'چه', 'ولو', 'از این رو', 'آنگاه', 'علاوه برآنکه']
Adjective - صفت - A : ['مناسب', 'آزاد', 'خبری', 'سریع', 'دایر', 'زیادی', 'دقیقی', 'محلی', 'موظف', 'مرتب', 'ملموسی', 'مختلف', 'حاضر', 'معتبر', 'مجبور', 'فراوان', 'کمتر', 'تلگرافی', 'داخلی', 'جدید', 'مهمترین', 'مالی', 'دولتی', 'معتقد', 'موفق', 'بیشتر', 'مطبوعاتی', 'انحصاری', 'معترض', 'پیشتاز', 'رقیب', 'پیشرفته تر', 'مربوط', 'بالا', 'شایانی', 'خارجی', 'حساس', 'بحرانی', 'مستقر', 'سراسری', 'منعقد', 'مستحکمتر', 'شرقی', 'رایگان', 'سلطنتی', 'سفید', 'گروهی', 'نهایی', 'جالب', 'بزرگ']
Number - عدد - U : ['یک', '1857', 'اولین', 'یکی', '3000', '8', '1863', '1868', '9', '1887', '1890', '10', 'دو', '11', 'چهارمین', '1872', '1906', '12', 'بیستم', 'شصت', 'نخستین', 'بیست', 'میلیارد', 'هزاران', 'پنج', 'هزار', 'آخر', 'هفتاد', '1953', '21', '1962', 'چهار', '1988', '1989', 'آخرین', 'اول', '1984', 'سی', '1917', 'شش', 'چهارم', '1998', '7', '78', '53', 'تک', '3', '15', '75', '66']
T : ['این', 'همه', 'یکی', 'آن', 'بعضی', 'تعدادی', 'چند', 'هیچیک', 'هر', 'بیشتر', 'بسیاری', 'چندین', 'بیش', 'تمام', 'تمامی', 'هیچ', 'همین', 'چه', 'همان', 'کدام', 'برخی', 'اکثر', 'بخشی', 'عده ای', 'نیمی', 'کلیه', 'غالب', 'حداقل', 'جمعی', 'پاره ای', 'فلان', 'همهٌ', 'اکثریت', 'کل', 'همگی', 'مقداری', 'قسمتی', 'شمار', 'اغلب', 'اینگونه', 'حداکثر', 'جمله', 'همه ی', 'عموم', 'شماری', 'تجمعی', 'همانجا', 'کلیهٌ', 'کمی', 'خیلی']
Pronoun - ضمیر - Z : ['آنها', 'دیگر', 'خود', 'این', 'آن', 'دیگری', 'آن ها', 'او', 'آنهایی', 'همه', 'من', 'این ها', 'آنان', 'هم', 'وی', 'یکدیگر', 'آنانی', 'همین', 'آنچه', 'ایشان', 'همگی', 'غیره', 'اینان', 'تو', 'کی', 'بسیاری', 'چنین', 'همگان', 'خویش', 'ما', 'دیگران', 'چی', 'بعضیها', 'برخی ها', 'جنابعالی', 'شما', 'چنان', 'همان', 'اینها', 'خویشتن', 'بعضی', 'این چنین', 'حضرتعالی', 'برخی', 'جملگی', 'فلانی', 'ماها', 'همدیگر', 'اینی', 'پاره ای']
Sign - علائم - O : ['،', '.', '»', '«', '#', ':', '...', '؟', '_', 'ـ', '-', '/', ')', '(', '!', '؛', '"', '+', '*', ',', '$', '…', 'ْ', '@', '[', ']', '}', '{']
L : ['چنین', 'قبضه', 'گونه', 'تنها', 'رشته', 'قبیل', 'سلسله', 'تعداد', 'جفت', 'نوع', 'چنان', 'دستگاه', 'نفرساعت', 'مورد', 'نفر', 'سری', 'تن', 'فقره', 'هکتار', 'جمله', 'درصد', 'کیلوگرم', 'بسی', 'کیلو', 'فروند', 'میزان', 'لیتر', 'بسته', 'جلد', 'لیر', 'تخته', 'ریزه', 'گرم', 'بشکه', 'مترمربع', 'کیلومتر', 'میکروگرم', 'قلم', 'مقدار', 'لیره', 'قطعه', 'واحد', 'متر', 'نمونه', 'دست', 'ریشتر', 'عدد', 'نخ', 'لیوان', 'تا']
Postposition - حرف اضافه پسین - P : ['را', 'رو']
Adverb - قید - D : ['به گرمی', 'از آن پس', 'به موقع', 'هنوز', 'قطعا', 'باز', 'شدیدا', 'مثل', 'صریحا', 'عمدتا', 'بطورکلی', 'چون', 'ابتدا', 'در مقابل', 'البته', 'بعد', 'درحقیقت', 'دیگر', 'بهتر', 'بارها', 'مانند', 'اکنون', 'اینک', 'کاملاً', 'چگونه', 'به زور', 'حتی', 'مبادا', 'همزمان', 'بعداً', 'به سرعت', 'نه', 'بویژه', 'نظیر', 'قبلاً', 'قاچاقی', 'عمدتاً', 'بسیار', 'واقعاً', 'فقط', 'کنار', 'به ویژه', 'بندرت', 'مسلماً', 'مطمئناً', 'دوباره', 'کم وبیش', 'به طور قطع', 'در حال حاضر', 'به ترتیب']
C : ['ش', 'یشان', 'شان', 'م', 'ام', 'یش', 'اش', 'ست', 'ند', 'اند', 'ب', 'دین', 'ت', 'ک', 'ستی', 'یم', 'مان', 'ید', 'دان', 'یتان', 'تان', 'ا', 'یند', 'ات', 'یت', 'ی', 'ه', 'یمان', 'اید', 'یی', 'ز', 'ایم', 'ییم', 'ین', 'دانان', 'ستند', 'ئی', 'ستم', 'و', 'ای', 'ر', 'دانچه', 'دو', 'چ', 'هات', 'تون', 'شون', 'س', 'یه', 'هام']
R : ['سالگی', 'ساله', 'الف', 'د', '!!!', 'G . I . S', 'کیلومتری', 'روزه', 'نه', 'آری', 'ردوا', 'الحجر', 'من', 'حیث', 'جاء', 'فان', 'الشر', 'لا', 'یدفعه', 'الا', 'بسمه تعالی', 'ساله ای', 'APB', 'ماهه', 'نفره', 'سلام', 'پوندی', 'STAINLESS', 'STEEL', 'AWTE', 'تنی', 'میلیونی', 'صفحه ای', 'یا', 'صــاح', 'للعجـب', 'دعــوتک', 'ثـم', 'لـم', 'تجـب', 'الی', 'القینات', 'والشهوات', 'والصهبــاء', 'و', 'الطـــرب', 'باطیه', 'مکلله', 'علیهــا', 'سـاده']
Interjection - حرف ندا - حرف ربط - I : ['ای', 'یا', 'زهی', 'هان', 'الا', 'آی', 'ایها', 'آهای'] 
"""
