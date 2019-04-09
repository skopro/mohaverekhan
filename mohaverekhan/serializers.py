from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField
from .models import (
            Word, WordNormal,
            Text, TextNormal, TextTag,
            TagSet, Tag, Token, TokenTag,
            Normalizer,
            Tagger, Validator
            )
import logging

logger = None


class NormalizerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Normalizer
        fields = ('id', 'name', 'show_name', 'owner', 'is_automatic', 
            'created', 'last_update', 'model_details',
            'total_text_normal_count',
            'total_valid_text_normal_count',
            'total_word_normal_count',
            'total_valid_word_normal_count',
            )
        read_only_fields = (
            'total_text_normal_count', 
            'total_valid_text_normal_count',
            'total_word_normal_count',
            'total_valid_word_normal_count',
            )


class TaggerSerializer(serializers.ModelSerializer):
    tag_set = serializers.SlugRelatedField(slug_field='name', 
            queryset=TagSet.objects.all())

    class Meta:
        model = Tagger
        fields = ('id', 'name', 'show_name', 'owner', 'is_automatic', 'created', 
                'tag_set', 'last_update', 'model_details',
                'total_text_tag_count', 
                'total_valid_text_tag_count', )
        read_only_fields = ('total_text_tag_count',
                 'total_valid_text_tag_count')


class ValidatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Validator
        fields = ('id', 'name', 'show_name', 'owner', 'created', 
            'total_text_normal_count', 
            'total_word_normal_count',
            'total_text_tag_count',
            )
        read_only_fields = (
            'total_text_normal_count', 
            'total_word_normal_count',
            'total_text_tag_count',
            )


class TagInTagSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'persian', 
            'color')
        # read_only_fields = (,
        #             )

class TagSetSerializer(serializers.ModelSerializer):
    tags = TagInTagSetSerializer(many=True, required=False)

    class Meta:
        model = TagSet
        fields = ('id', 'name', 'created', 'last_update',
            'number_of_tags', 'number_of_taggers',
            'total_text_tag_count',
            'total_valid_text_tag_count',
            'tags')
        read_only_fields = ('number_of_tags',
            'number_of_taggers',
            'total_text_tag_count',
            'total_valid_text_tag_count',
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

class TagInTokenSerializer(serializers.ModelSerializer):
    tag_set = serializers.SlugRelatedField(slug_field='name', 
            queryset=TagSet.objects.all())

    class Meta:
        model = Tag
        fields = ('id', 'name', 'persian', 
            'color', 'created', 
            'tag_set')
        # read_only_fields = (,
        #             )

class TokenSerializer(serializers.ModelSerializer):
    tags = TagInTokenSerializer(many=True, read_only=True)

    class Meta:
        model = Token
        fields = ('id', 'content', 'number_of_tags', 
            'tags', 'created',)
        read_only_fields = ('tags', 'number_of_tags',
                    )

class TokenTagSerializer(serializers.ModelSerializer):
    tag = TagInTokenSerializer()
    token = serializers.SlugRelatedField(slug_field='content', 
            queryset=Token.objects.all())

    class Meta:
        model = TokenTag
        fields = ('id', 'token', 'tag', 
            'number_of_repetitions', 'created')
        read_only_fields = ('number_of_repetitions',
                    )

class TagSerializer(serializers.ModelSerializer):
    tag_set = serializers.SlugRelatedField(slug_field='name', 
            queryset=TagSet.objects.all())

    class Meta:
        model = Tag
        fields = ('id', 'name', 'persian', 
            'color', 'created', 'number_of_tokens',
            'tag_set', )
        # read_only_fields = (,
        #             )


class TextNormalInTextSerializer(serializers.ModelSerializer):
    normalizer = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)
    validator = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)

    class Meta:
        model = TextNormal
        fields = ('id', 'created', 'content', 'normalizer', 'is_valid', 
                    'validator')
        read_only_fields = ('is_valid',)       

class TextTagInTextSerializer(serializers.ModelSerializer):
    tagger = serializers.SlugRelatedField(slug_field='name', 
            queryset=Tagger.objects.all())
    validator = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)

    class Meta:
        model = TextTag
        fields = ('id', 'created', 'tagger', 'accuracy', 'true_text_tag',
            'is_valid', 'validator', 'tagged_tokens', 'tagged_tokens_html')
        read_only_fields = ('is_valid',)    


class TextSerializer(serializers.ModelSerializer):
    text_normals = TextNormalInTextSerializer(many=True, required=False)
    text_tags = TextNormalInTextSerializer(many=True, required=False)
    normalizers = serializers.SlugRelatedField(many=True, slug_field='name', 
                                read_only=True)

    class Meta:
        model = Text
        fields = ('id', 'created', 'content', 'normalizers_sequence',
            'normalizers', 'text_normals', 'text_tags')
        read_only_fields = ('normalizers_sequence', 'normalizers', 
                'text_normals', 'text_tags')

class TextInTextNormalOrTextTag(serializers.ModelSerializer):

    class Meta:
        model = Text
        fields = ('id', 'created', 'content', 'normalizers_sequence')
        read_only_fields = ('normalizers_sequence',)

class TextNormalSerializer(serializers.ModelSerializer):
    normalizer = serializers.SlugRelatedField(slug_field='name', 
        queryset=Normalizer.objects.all())
    text = TextInTextNormalOrTextTag()
    validator = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)

    class Meta:
        model = TextNormal
        fields = ('id', 'created', 'content', 
            'normalizer', 'text', 
            'is_valid', 'validator',)
        read_only_fields = ('is_valid',)

    def create(self, validated_data):
        text_data = validated_data.pop('text')
        text = None
        text_id = text_data.pop('id', None)
        if text_id:
            text = Text.objects.get(id=text_id)
        else:
            text = Text.objects.create(**text_data)
        text_normal = TextNormal.objects.create(text=text, **validated_data)
        return text_normal

class TrueTextTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = TextTag
        fields = ('id', 'created', 
            'tagger', 'accuracy', 
            'tagged_tokens', 'tagged_tokens_html')

class TextTagSerializer(serializers.ModelSerializer):
    tagger = serializers.SlugRelatedField(slug_field='name', 
            queryset=Tagger.objects.all(), required=False)
    text = TextInTextNormalOrTextTag()
    validator = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)
    true_text_tag = TrueTextTagSerializer(required=False, read_only=True)
        
    class Meta:
        model = TextTag
        fields = ('id', 'created', 
            'tagger', 'text', 'accuracy', 'true_text_tag', 
            'is_valid', 'validator', 'tagged_tokens', 
            'tagged_tokens_html', 'tags_string')
        read_only_fields = ('is_valid', 'accuracy', 'true_text_tag')
    
    def create(self, validated_data):
        text_data = validated_data.pop('text')
        text = None
        text_id = text_data.pop('id', None)
        if text_id:
            text = Text.objects.get(id=text_id)
        else:
            text = Text.objects.create(**text_data)
        tagged_text = TextTag.objects.create(text=text, **validated_data)
        return tagged_text

    def update(self, instance, validated_data):
        text_data = validated_data.get('text', None)
        if not text_data:
            return instance
        text_content = text_data.get('content', None)
        if not text_content:
            return instance
        instance.text.content = text_content
        instance.text.save(update_fields=['content'])

        instance.tagged_tokens = validated_data.get('tagged_tokens', instance.tagged_tokens)
        instance.save(update_fields=['tagged_tokens'])
        return instance

class WordNormalInWordSerializer(serializers.ModelSerializer):
    normalizer = serializers.SlugRelatedField(slug_field='name', 
        read_only=True)
    validator = serializers.SlugRelatedField(slug_field='name', 
        read_only=True)
    

    class Meta:
        model = WordNormal
        fields = ('id', 'created', 'content', 
            'is_valid', 'validator', 'normalizer')
        read_only_fields = ('is_valid')


class WordSerializer(serializers.ModelSerializer):
    word_normals = WordNormalInWordSerializer(many=True, required=False)
    normalizers = serializers.SlugRelatedField(many=True, slug_field='name', 
                                read_only=True)

    class Meta:
        model = Word
        fields = ('id', 'created', 'content', 
            'normalizers', 'word_normals')
        read_only_fields = ('normalizers', 
                'word_normals')

    # def to_representation(self, instance):
    #     instance.sentences.set(instance.sentences.order_by('order'))
    #     data = super(WordSerializer, self).to_representation(instance)
    #     return data

class WordInWordNormalSerializer(serializers.ModelSerializer):
    normalizers = serializers.SlugRelatedField(many=True, slug_field='name', 
                                read_only=True)

    class Meta:
        model = Word
        fields = ('id', 'created', 'content', 
            'normalizers', 'word_normals')
        read_only_fields = ('normalizers', 
                'word_normals')

class WordNormalSerializer(serializers.ModelSerializer):
    normalizer = serializers.SlugRelatedField(slug_field='name', 
        queryset=Normalizer.objects.all())
    word = WordInWordNormalSerializer()
    validator = serializers.SlugRelatedField(slug_field='name', 
            read_only=True)

    class Meta:
        model = WordNormal
        fields = ('id', 'created', 'content', 
            'is_valid', 'validator', 'normalizer', 'word')
        read_only_fields = ('validator', 'is_valid')

    def create(self, validated_data):
        word_data = validated_data.pop('word')
        word = None
        word_id = word_data.pop('id', None)
        if word_id:
            word = Word.objects.get(id=word_id)
        else:
            word = Word.objects.create(**word_data)
        word_normal = WordNormal.objects.create(word=word, **validated_data)
        return word_normal










# class SentenceInTaggedSentenceSerializer(serializers.Serializer):
#     id = serializers.UUIDField(required=False)
#     content = serializers.CharField(required=False)

#     class Meta:
#         fields = ('id', 'content',)

# class TaggedSentenceSerializer(serializers.ModelSerializer):
#     tagger = serializers.SlugRelatedField(slug_field='name', 
#             queryset=Tagger.objects.all())
#     sentence = SentenceInTaggedSentenceSerializer()
#     validator = serializers.SlugRelatedField(slug_field='name', 
#             read_only=True)
        
#     class Meta:
#         model = TaggedSentence
#         fields = ('id', 'created', 
#             'tagger', 'sentence', 
#             'tagged_tokens', 'validator', 'is_valid')
#         read_only_fields = ('validator', 'is_valid',)
    
#     def create(self, validated_data):
#         sentence_data = validated_data.pop('sentence')
#         sentence = None
#         sentence_id = sentence_data.pop('id', None)
#         if sentence_id:
#             sentence = Sentence.objects.get(id=sentence_id)
#         else:
#             sentence = Sentence.objects.create(**sentence_data)
#         tagged_sentence = TaggedSentence.objects.create(sentence=sentence, **validated_data)
#         return tagged_sentence


# class TextInSentenceSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Text
#         fields = ('id', 'normalizers_sequence', 'content')
#         read_only_fields = ('normalizers_sequence', )

# class SentenceSerializer(serializers.ModelSerializer):
#     text = TextInSentenceSerializer()
#     tagged_sentences = TaggedSentenceInSentenceSerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Sentence
#         fields = ('id', 'content', 'created', 
#             'normalizers_sequence', 'text', 'order', 
#             'tagged_sentences', 'normalizers')
#         read_only_fields = ('taggers', 'normalizers_sequence',
#                             'tagged_sentences', 'normalizers', 'normal_sentences')

#     def create(self, validated_data):
#         text_data = validated_data.pop('text')
#         text = None
#         text_id = text_data.pop('id', None)
#         if text_id:
#             text = Text.objects.get(id=text_id)
#         else:
#             text = Text.objects.create(**text_data)
#         sentence = Sentence.objects.create(text=text, **validated_data)
#         return sentence

# class NormalSentenceSerializer(serializers.ModelSerializer):
#     normalizer = serializers.SlugRelatedField(slug_field='name', 
#         queryset=Normalizer.objects.all())
#     sentence = SentenceSerializer()
#     validator = serializers.SlugRelatedField(slug_field='name', 
#             read_only=True)
        
#     class Meta:
#         model = NormalSentence
#         fields = ('id', 'created', 'content', 
#             'validator', 'is_valid', 'normalizer', 'sentence')
#         read_only_fields = ('validator', 'is_valid')

#     def create(self, validated_data):
#         sentence_data = validated_data.pop('sentence')
#         sentence = None
#         sentence_id = sentence_data.pop('id', None)
#         if sentence_id:
#             sentence = Sentence.objects.get(id=sentence_id)
#         else:
#             sentence = Sentence.objects.create(**sentence_data)
#         normal_sentence = NormalSentence.objects.create(sentence=sentence, **validated_data)
#         return normal_sentence

# class SentenceInTextSerializer(serializers.ModelSerializer):
#     tagged_sentences = TaggedSentenceInSentenceSerializer(many=True, read_only=True)
    
#     class Meta:
#         model = Sentence
#         fields = ('id', 'content', 'created', 
#             'tagged_sentences')
#         read_only_fields = ('taggers',
#                             'tagged_sentences')











    # def to_representation(self, instance):
    #     instance.sentences.set(instance.sentences.order_by('order'))
    #     data = super(TextSerializer, self).to_representation(instance)
    #     return data




# class TranslationCharacterSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = TranslationCharacter
#         fields = ('id', 'source', 'destination', 'description', 'owner', 'is_valid')
#         extra_kwargs = {
#             "source": {"trim_whitespace": False},
#             "destination": {"trim_whitespace": False},
#         }

# class RefinementPatternSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = RefinementPattern
#         fields = ('id', 'pattern', 'replacement', 'description', 'order', 'owner', 'is_valid')
#         extra_kwargs = {
#             "pattern": {"trim_whitespace": False},
#             "replacement": {"trim_whitespace": False},
#         }

def init():
    global logger
    logger = logging.getLogger(__name__)
