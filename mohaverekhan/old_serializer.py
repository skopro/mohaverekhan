from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from .models import (Formalizer, Text, FormalText, Tagger,
            Sentence, TaggedSentence, TranslationCharacter, 
            RefinementPattern)
import logging

logger = None

class TagSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Tag.tag_name_choices, default=Tag.N)
    persian = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    
    class Meta:
        fields = ('name', 'persian', 'color')

    def get_persian(self, obj):
        return Tag.tag_name_details_dic[obj.name][0]
    
    def get_color(self, obj):
        return Tag.tag_name_details_dic[obj.name][1]

class TokenSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=100)
    normalized = serializers.CharField(max_length=100, allow_null=True, required=False)
    tag = TagSerializer(allow_null=True, required=False)
    is_valid = serializers.BooleanField(default=False, required=False)

    class Meta:
        fields = ('content', 'normalized', 'tag', 'is_valid')

class TaggerSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Tagger.tagger_name_choices, 
                        default=Tagger.IPPOST_TAGGER)
    tokens = TokenSerializer(many=True, allow_null=True, required=False)
    is_valid = serializers.BooleanField(default=False, required=False)

    class Meta:
        fields = ('name', 'tokens', 'is_valid')

class SentenceSerializer(serializers.ModelSerializer):
    taggers = TaggerSerializer(many=True, allow_null=True, required=False)
    # text = None
    # formalizer = None

    class Meta:
        model = Sentence
        fields = ('id', 'created', 'content', 'normalized', 'taggers')

    def parse_tag(self, token, tag_data):
        if tag_data is not None:
            serializer = TagSerializer(data=tag_data)
            if not serializer.is_valid():
                logger.error(f'> TagSerializer problem : {serializer.errors}')
                raise Exception(f'> TagSerializer problem : {serializer.errors}')
            token.tag = Tag(**serializer.validated_data)

    def parse_tokens(self, tagger, tokens_data):
        serializer = None
        if tokens_data is not None and tokens_data:
            # tagger.tokens = []
            token, tag_data = None, None
            for token_data in tokens_data:
                tag_data = token_data.pop('tag', None)
                serializer = TokenSerializer(data=token_data)
                if not serializer.is_valid():
                    logger.error(f'> TokenSerializer problem : {serializer.errors}')
                    raise Exception(f'> TokenSerializer problem : {serializer.errors}')
                token = Token(**serializer.validated_data)
                self.parse_tag(token, tag_data)
                tagger.tokens.append(token)

    def parse_taggers(self, sentence, taggers_data):
        serializer = None
        if taggers_data is not None and taggers_data:
            # sentence.taggers = []
            tagger, tokens_data = None, None
            for tagger_data in taggers_data:
                tokens_data = tagger_data.pop('tokens', None)
                serializer = TaggerSerializer(data=tagger_data)
                if not serializer.is_valid():
                    logger.error(f'> TaggerSerializer problem : {serializer.errors}')
                    raise Exception(f'> TaggerSerializer problem : {serializer.errors}')
                tagger = Tagger(**serializer.validated_data)
                self.parse_tokens(tagger, tokens_data)
                sentence.taggers.append(tagger)
    
    def create(self, validated_data):
        taggers_data = validated_data.pop('taggers', None)
        sentence = Sentence.objects.create(**validated_data)
        self.parse_taggers(sentence, taggers_data)

        sentence.save()
        # logger.info(f'> text : {text}')
        return sentence
        
class FormalizerSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Formalizer.formalizer_name_choices, 
                        default=Formalizer.IPPOST_FORMALIZER)
    content = serializers.CharField()
    normalized = serializers.CharField(allow_null=True, required=False)
    is_valid = serializers.BooleanField(default=False, required=False)
    sentences = SentenceSerializer(many=True, allow_null=True, required=False)

    class Meta:
        fields = ('name', 'content', 'normalized', 'is_valid', 'sentences')

class TextSerializer(serializers.ModelSerializer):
    sentences = SentenceSerializer(many=True, allow_null=True, required=False)
    formalizers = FormalizerSerializer(many=True, allow_null=True, required=False)
    
    class Meta:
        model = Text
        fields = ('id', 'created', 'content', 'normalized', 'sentences', 
            'formalizers')
    
    def parse_formalizers(self, text, formalizers_data):
        serializer = None
        if formalizers_data is not None and formalizers_data:
            # text.formalizers = []
            formalizer, sentences_data = None, None
            for formalizer_data in formalizers_data:
                sentences_data = formalizer_data.pop('sentences', None)
                serializer = FormalizerSerializer(data=formalizer_data)
                if not serializer.is_valid():
                    logger.error(f'> FormalizerSerializer problem : {serializer.errors}')
                    raise Exception(f'> FormalizerSerializer problem : {serializer.errors}')
                formalizer = Formalizer(**serializer.validated_data)
                self.parse_sentences(formalizer, sentences_data)
                text.formalizers.append(formalizer)
            
    def parse_sentences(self, text_or_formalizer, sentences_data):
        serializer = None
        if sentences_data is not None and sentences_data:
            # text_or_formalizer.sentences = []
            sentence = None
            for sentence_data in sentences_data:
                serializer = SentenceSerializer(data=sentence_data)
                if not serializer.is_valid():
                    logger.error(f'> SentenceSerializer problem : {serializer.errors}')
                    raise Exception(f'> SentenceSerializer problem : {serializer.errors}')
                sentence = serializer.save()
                serializer = SentenceSerializer(sentence)
                logger.info(f'> parse_sentences : \n\nsentence : \n\n{serializer.data}\n\n')
                text_or_formalizer.sentences.add(sentence)

    def create(self, validated_data):
        # logger.info(f'> validated_data : {validated_data.__str__()[:100]...}')
        sentences_data = validated_data.pop('sentences', None)
        formalizers_data = validated_data.pop('formalizers', None)
        text = Text.objects.create(**validated_data)
        self.parse_sentences(text, sentences_data)
        self.parse_formalizers(text, formalizers_data)
        serializer = TextSerializer(text)
        logger.info(f'> TextSerializer create => text : \n\n{serializer.data}\n\n')
                
        text.save()
        # logger.info(f'> text : {text}')
        return text

# SentenceSerializer.text = TextSerializer(allow_null=True, required=False)
# SentenceSerializer.formalizer = FormalizerSerializer(allow_null=True, required=False)
# SentenceSerializer.Meta.fields += ('text', 'formalizer')

class TranslationCharacterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TranslationCharacter
        fields = ('id', 'source', 'destination', 'description', 'owner', 'is_valid')
        extra_kwargs = {
            "source": {"trim_whitespace": False},
            "destination": {"trim_whitespace": False},
        }

class RefinementPatternSerializer(serializers.ModelSerializer):

    class Meta:
        model = RefinementPattern
        fields = ('id', 'pattern', 'replacement', 'description', 'order', 'owner', 'is_valid')
        extra_kwargs = {
            "pattern": {"trim_whitespace": False},
            "replacement": {"trim_whitespace": False},
        }


    # def create(self, validated_data):
    #     logger.info(f'>> Create method of SentenceSerializer')
    #     tags_data = validated_data.pop('tags')
    #     logger.info(f'> tags_data : {tags_data}')
    #     tags = []
    #     for tag_data in tags_data:
    #         tags += TagSerializer.create(TagSerializer(), validated_data=tag_data)
    #     logger.info(f'> tags : {tags}')
    #     sentence, created = Sentence.objects.update_or_create(tags=tags,
    #                         content=validated_data.pop('content'))
    #     logger.info(f'> sentence : {sentence}')
    #     logger.info(f'> created : {created}')
    #     return sentence


 
    # def create(self, validated_data):
    #     logger.info(f'>> Create method of TextSerializer')
    #     sentences_data = validated_data.pop('sentences')
    #     logger.info(f'> sentences_data : {sentences_data}')
    #     sentences = []
    #     for sentence_data in sentences_data:
    #         sentences += SentenceSerializer.create(SentenceSerializer(), validated_data=sentence_data)
    #     logger.info(f'> sentences : {sentences}')
    #     text, created = Text.objects.update_or_create(sentences=sentences,
    #                         content=validated_data.pop('content'))
    #     logger.info(f'> text : {text}')
    #     logger.info(f'> created : {created}')
    #     return text

def init():
    global logger
    logger = logging.getLogger(__name__)
