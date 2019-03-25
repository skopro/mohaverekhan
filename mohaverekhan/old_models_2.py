import uuid
import json
from collections import OrderedDict
import logging
from djongo import models
from django import forms

from .core.nltk_taggers import model as nltk_taggers_model
from .core.seq2seq import model as seq2seq_model
# from django.db import models
# from djongo.models import forms
logger = logging.getLogger(__name__)


class NonStrippingTextField(models.TextField):
    """A TextField that does not strip whitespace at the beginning/end of
    it's value.  Might be important for markup/code."""

    def formfield(self, **kwargs):
        kwargs['strip'] = False
        return super(NonStrippingTextField, self).formfield(**kwargs)

class NonStrippingCharField(models.CharField):
    """A TextField that does not strip whitespace at the beginning/end of
    it's value.  Might be important for markup/code."""

    def formfield(self, **kwargs):
        kwargs['strip'] = False
        return super(NonStrippingCharField, self).formfield(**kwargs)



class Tag(models.Model):
    E, N, V, J, A, U, T, Z, O, L, P, D, C, R, I = 'E', 'N', 'V', 'J', 'A', 'U', 'T', 'Z', 'O', 'L', 'P', 'D', 'C', 'R', 'I'

    tag_name_choices = (
        (N, 'N_اسم'),
        (E, 'E'),
        (V, 'V_فعل'),
        (J, 'J'),
        (A, 'A_صفت'),
        (U, 'U_عدد'),
        (T, 'T'),
        (Z, 'Z_ضمیر'),
        (O, 'O_علامت'),
        (L, 'L'),
        (P, 'P_حرف اضافه پسین'),
        (D, 'D_قید'),
        (C, 'C'),
        (R, 'R'),
        (I, 'I_حرف ندا'),
    )
    name = NonStrippingCharField(max_length=2, default=N, choices=tag_name_choices, unique=True)
    # persian = NonStrippingCharField(max_length=15, default='اسم', unique=True)
    # color = NonStrippingCharField(max_length=40, default='red', unique=True)

    tag_name_details_dic = {
        'E' : ('E', '#E74C3C'),
        'N' : ('اسم', '#3498DB'),
        'V' : ('فعل', '#9B59B6'),

        'J' : ('J', '#1ABC9C'),
        'A' : ('صفت', '#F1C40F'),
        'U' : ('عدد', '#E67E22'),
        
        'T' : ('T', '#ECF0F1'),
        'Z' : ('ضمیر', '#BDC3C7'),
        'O' : ('علامت', '#7F8C8D'),
        
        'L' : ('L', '#34495E'),
        'P' : ('حرف اضافه پسین', '#C39BD3'),
        'D' : ('قید', '#FBFCFC'),
        
        'C' : ('C', '#0E6655'),
        'R' : ('R', '#922B21'),
        'I' : ('حرف ندا', '#AED6F1'),
    }

    # @property
    # def persian(self):
    #     return self.tag_name_details_dic[self.name](0)

    # @property
    # def color(self):
    #     return self.tag_name_details_dic[self.name](1)


    def __str__(self):
        # return f'({self.name}, {self.persian}, {self.color})'
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']


class Token(models.Model):
    content = NonStrippingCharField(max_length=100)
    normalized = NonStrippingCharField(max_length=100)
    tag = models.EmbeddedModelField(model_container=Tag, blank=True)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.content}_{self.tag}'

    class Meta:
        abstract = True
    
    def normalize(self):
        self.normalized = self.content

class Tagger(models.Model):
    MANUAL_TAGGER = 'manual_tagger'
    IPPOST_TAGGER = 'ippost_tagger'
    HAZM_TAGGER = 'hazm_tagger'
    tagger_name_choices = (
        (MANUAL_TAGGER, 'manual_tagger'),
        (IPPOST_TAGGER, 'ippost_tagger'),
        (HAZM_TAGGER, 'hazm_tagger'),
    )
    name = NonStrippingCharField(max_length=50, default=IPPOST_TAGGER, choices=tagger_name_choices)
    tokens = models.ArrayModelField(model_container=Token, null=True, blank=True, default=[])
    is_valid = models.BooleanField(default=False, blank=True)

    class Meta:
        abstract = True
    
    def __str__(self):
        rep = "None"
        if self.tokens is not None:
            # rep += '\n'
            rep = ' '.join([token.__str__() for token in self.tokens])
        return rep

    def check_validation(self):
        self.is_valid = True
        for token in self.tokens:
            self.is_valid = self.is_valid and token.is_valid
        logger.info(f'> check_validation : {self.is_valid}')


    
class Sentence(models.Model):
    objects = models.DjongoManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    content = NonStrippingTextField(unique=True)
    normalized = NonStrippingTextField(blank=True)
    taggers = models.ArrayModelField(model_container=Tagger, null=True, blank=True, default=[])
    # text = models.ForeignKey(to=Text, on_delete=models.DO_NOTHING, related_name='sentences', related_query_name='sentence', blank=True, null=True)
    # formalizer = models.ForeignKey(to=Formalizer, on_delete=models.DO_NOTHING, related_name='sentences', related_query_name='sentence', blank=True, null=True)

    def __str__(self):
        rep = self.content
        return rep
    
    def save(self, *args, **kwargs):
        if self.taggers is not None:
            [tagger.check_validation() for tagger in self.taggers]
        super(Sentence, self).save(*args, **kwargs)

    def normalize(self):
        self.normalized = self.content



class Formalizer(models.Model):
    MANUAL_FORMALIZER = 'manual_formalizer'
    IPPOST_FORMALIZER = 'ippost_formalizer'
    formalizer_name_choices = (
        (MANUAL_FORMALIZER, 'manual_formalizer'),
        (IPPOST_FORMALIZER, 'ippost_formalizer'),
    )
    name = NonStrippingCharField(max_length=50, default=IPPOST_FORMALIZER, choices=formalizer_name_choices)
    content = NonStrippingTextField()
    normalized = NonStrippingTextField(blank=True)
    is_valid = models.BooleanField(default=False, blank=True)
    # sentences = models.ArrayReferenceField(to=Sentence, on_delete=models.DO_NOTHING, null=True, blank=True, default=set())
    sentences = models.ArrayModelField(model_container=Sentence, null=True, blank=True, default=[])
    
    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.content}'

    def normalize(self):
        self.normalized = self.content

class Text(models.Model):
    objects = models.DjongoManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    content = NonStrippingTextField(unique=True)
    normalized = NonStrippingTextField(blank=True)
    # sentences = models.ArrayModelField(model_container=Sentence, null=True, blank=True, default=[])
    sentences = models.ArrayReferenceField(to=Sentence, on_delete=models.DO_NOTHING, null=True, blank=True, default=set())
    formalizers = models.ArrayModelField(model_container=Formalizer, null=True, blank=True, default=[])

    def __str__(self):
        return f'{self.content[:50]}{" ..." if len(self.content) > 50 else ""}'

    def normalize(self):
        self.normalized = self.content
    
    def convert_to_formal(self):
        try:
            logger.info(f'Informal : {self.content}')
            self.formal = seq2seq_model.inference(self.content)
            logger.info(f'Formal content : {self.formal}')
            # words = Word.objects.all()
            # self.formal_content = self.content
            # content_words = self.formal_content.split(' ')

            # logger.debug(f'content_words : {content_words}')

            # self.formal_content = ''
            # for content_word in content_words:
            #     formal = content_word
            #     for word in words:
            #         if content_word == word.informal:
            #             logger.debug(f'word {word.informal} is replaced by {word.formal}')
            #             formal = word.formal
            #             break
            #     self.formal_content += formal + ' '
            #     logger.debug(self.formal_content)
        except Exception as ex:
            logger.exception(ex)

    def learn_model(self):
        num_epochs = 150
        logger.info(f'Model is going to train for {num_epochs} epochs.')
        seq2seq_model.train(False, num_epochs=num_epochs)

    def convert_and_fpost(self):
        logger.info(f'Informal : {self.content}')
        # self.fpost_content = ''
        # for word in self.content.split(' '):
        #     self.fpost_content += seq2seq_model.inference(word) + ' '
        # logger.info(f'Fpost content : {self.fpost_content}')

    def infpost(self):
        try:
            logger.info(f'> Informal : {self.content}')
            sentence_contents, token_tag_list = nltk_taggers_model.tag_text(self.content)
            logger.info(f'> sentence_contents : {sentence_contents}')
            logger.info(f'> token_tag_list : {token_tag_list}')
            sentences, tokens = [], []
            current_sentence, current_tag, current_token = None, None, None
            for i, sentence_content in enumerate(sentence_contents):
                print(f'> sentence_contents[{i}] : {sentence_content}')
                current_sentence = Sentence(content=sentence_content)
                print(f'> current_sentence : {current_sentence} {type(current_sentence)}')
                tokens = []
                for token_tag in token_tag_list[i]:
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


class TranslationCharacter(models.Model):
    objects = models.DjongoManager()
    created = models.DateTimeField(auto_now_add=True)
    source = NonStrippingCharField(max_length=2, unique=True)
    destination = NonStrippingCharField(max_length=2)
    description = NonStrippingTextField(blank=True)
    owner = NonStrippingCharField(max_length=75)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return f'''
            ({self.source}, {self.destination}, {self.description}, {self.description}, 
            {self.owner}, {self.is_valid})
            '''

class RefinementPattern(models.Model):
    objects = models.DjongoManager()
    created = models.DateTimeField(auto_now_add=True)
    pattern = NonStrippingCharField(max_length=200, unique=True)
    replacement = NonStrippingCharField(max_length=200)
    description = NonStrippingTextField(blank=True)
    order = models.IntegerField(default=9999, unique=True)
    owner = NonStrippingCharField(max_length=75)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return f'''
            ({self.pattern}, {self.replacement}, {self.description}, {self.order}, 
            {self.owner}, {self.is_valid})
            '''

"""
from ippost.models import Text, Sentence, Tag, Token
from ippost.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
text = Text.objects.create(content="سلام. چطوری خوبی؟")
serializer = TextSerializer(text)
serializer.data
sentence1 = Sentence.objects.create(content="سلام.")
serializer = SentenceSerializer(sentence1)
serializer.data
text.sentences.add(sentence1)
serializer = TextSerializer(text)
serializer.data

from ippost.models import Text, Sentence, Tag, Token
from ippost.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
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


from ippost.models import Text, Sentence, Tag, Token
from ippost.serializers import TextSerializer, SentenceSerializer, TokenSerializer, TagSerializer
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
