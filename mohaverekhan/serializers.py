from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from .models import (Normalizer, Text, NormalText, 
            TagSet, Tag, Tagger,
            Sentence, TaggedSentence, TranslationCharacter, 
            RefinementPattern)
import logging

logger = None

class TagInTagSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'persian', 
            'color')

class TagSetSerializer(serializers.ModelSerializer):
    tags = TagInTagSetSerializer(many=True, required=False)

    class Meta:
        model = TagSet
        fields = ('id', 'name', 'created', 
            'number_of_tags', 'number_of_taggers',
            'total_tagged_sentence_count',
            'total_valid_tagged_sentence_count',
            'unknown_tag', 'tags')
        read_only_fields = ('number_of_tags',
            'number_of_taggers',
            'total_tagged_sentence_count',
            'total_valid_tagged_sentence_count',
                    )
    
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        tag_set = TagSet.objects.create(**validated_data)
        if not tags_data:
            return tag_set

        tag = None
        created = False
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(tag_set=tag_set, **tag_data)

        return tag_set

class TagSerializer(serializers.ModelSerializer):
    tag_set = serializers.SlugRelatedField(slug_field='name', 
            queryset=TagSet.objects.all())

    class Meta:
        model = Tag
        fields = ('id', 'name', 'persian', 
            'color', 'created', 
            'examples', 'tag_set')
        read_only_fields = ('examples',
                    )

class NormalizerSerializer(serializers.ModelSerializer):
    # normal_text = NormalTextSerializer(required=False)
    # normal_texts = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Normalizer
        fields = ('id', 'name', 'owner', 'model_type', 'created', 
            'last_update', 'model_details',
            'total_normal_text_count', 
            'total_valid_normal_text_count')
        read_only_fields = ('total_text_count',
                 'total_valid_text_count', 'texts', 
                 'normal_texts')

class TaggerSerializer(serializers.ModelSerializer):
    # tagged_sentences = serializers.PrimaryKeyRelatedField(
    #         many=True, read_only=True)
    tag_set = serializers.SlugRelatedField(slug_field='name', 
            queryset=TagSet.objects.all())

    class Meta:
        model = Tagger
        fields = ('id', 'name', 'owner', 'model_type', 'created', 
                'tag_set', 'last_update', 'model_details',
                'total_tagged_sentence_count', 
                'total_valid_tagged_sentence_count', )
        read_only_fields = ('total_tagged_sentence_count',
                 'total_valid_tagged_sentence_count')


class SentenceInTaggedSentenceSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    content = serializers.CharField(required=False)

    class Meta:
        fields = ('id', 'content',)

class TaggedSentenceSerializer(serializers.ModelSerializer):
    tagger = serializers.SlugRelatedField(slug_field='name', 
            queryset=Tagger.objects.all())
    sentence = SentenceInTaggedSentenceSerializer()

    class Meta:
        model = TaggedSentence
        fields = ('id', 'created', 
            'tagger', 'sentence', 
            'tokens', 'is_valid')
        read_only_fields = ('is_valid',)
    
    def create(self, validated_data):
        sentence_data = validated_data.pop('sentence')
        sentence = None
        sentence_id = sentence_data.pop('id', None)
        if sentence_id:
            sentence = Sentence.objects.get(id=sentence_id)
        else:
            sentence = Sentence.objects.create(**sentence_data)
        tagged_sentence = TaggedSentence.objects.create(sentence=sentence, **validated_data)
        return tagged_sentence

class TaggedSentenceInSentenceSerializer(serializers.ModelSerializer):
    tagger = serializers.SlugRelatedField(slug_field='name', 
            queryset=Tagger.objects.all())

    class Meta:
        model = TaggedSentence
        fields = ('id', 'created', 'tagger', 'sentence', 
            'tokens', 'is_valid')
        read_only_fields = ('is_valid',)       

class TextInSentenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Text
        fields = ('id', 'is_normal_text', 'content')
        read_only_fields = ('is_normal_text', )

class SentenceSerializer(serializers.ModelSerializer):
    text = TextInSentenceSerializer()
    tagged_sentences = TaggedSentenceInSentenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sentence
        fields = ('id', 'content', 'created', 
            'text', 'order', 'tagged_sentences')
        read_only_fields = ('taggers',
                            'tagged_sentences')

    def create(self, validated_data):
        text_data = validated_data.pop('text')
        text = None
        text_id = text_data.pop('id', None)
        if text_id:
            text = Text.objects.get(id=text_id)
        else:
            text = Text.objects.create(**text_data)
        sentence = Sentence.objects.create(text=text, **validated_data)
        return sentence

class SentenceInTextSerializer(serializers.ModelSerializer):
    tagged_sentences = TaggedSentenceInSentenceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Sentence
        fields = ('id', 'content', 'created', 
            'tagged_sentences')
        read_only_fields = ('taggers',
                            'tagged_sentences')

class TextSerializer(serializers.ModelSerializer):
    sentences = SentenceInTextSerializer(many=True, required=False)
    normalizers = serializers.SlugRelatedField(many=True, slug_field='name', 
                                read_only=True)

    class Meta:
        model = Text
        fields = ('id', 'created', 'is_normal_text', 'content', 
            'normalizers', 'sentences')
        read_only_fields = ('is_normal_text', 'normalizers', 
                'normal_texts', 'sentences')

    # def to_representation(self, instance):
    #     instance.sentences.set(instance.sentences.order_by('order'))
    #     data = super(TextSerializer, self).to_representation(instance)
    #     return data

class NormalTextSerializer(serializers.ModelSerializer):
    normalizer = serializers.SlugRelatedField(slug_field='name', 
        queryset=Normalizer.objects.all())
    text = TextSerializer()
    sentences = SentenceSerializer(many=True, required=False)

    class Meta:
        model = NormalText
        fields = ('id', 'created', 'content', 
            'is_valid', 'normalizer', 'text', 
            'sentences')
        read_only_fields = ('is_valid', 'sentences')

    def create(self, validated_data):
        text_data = validated_data.pop('text')
        text = None
        text_id = text_data.pop('id', None)
        if text_id:
            text = Text.objects.get(id=text_id)
        else:
            text = Text.objects.create(**text_data)
        normal_text = NormalText.objects.create(text=text, **validated_data)
        return normal_text





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

def init():
    global logger
    logger = logging.getLogger(__name__)
