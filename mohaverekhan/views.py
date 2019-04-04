from rest_framework.response import Response
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.request import Request
from django.views.generic.base import TemplateView
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework import renderers
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse

from .serializers import (
            WordSerializer, WordNormalSerializer,
            TextSerializer, TextNormalSerializer, TextTagSerializer,
            TagSetSerializer, TagSerializer,
            NormalizerSerializer, TokenizerSerializer,
            TaggerSerializer, ValidatorSerializer,
            )

from .models import (
            Word, WordNormal,
            Text, TextNormal, TextTag,
            TagSet, Tag,
            Normalizer, Tokenizer,
            Tagger, Validator
            )

from .models import (
            RefinementNormalizer,
            ReplacementNormalizer,
            NLTKTagger
            )

from django.views.decorators.csrf import csrf_exempt
import threading 
import json
from . import cache


import logging
logger = None

class HomePageView(TemplateView):
    """
    This is home page
    """
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'mohaverekhan/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['latest_articles'] = Article.objects.all()[:5]
        return context

class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer

class WordNormalViewSet(viewsets.ModelViewSet):
    queryset = WordNormal.objects.all()
    serializer_class = WordNormalSerializer

class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer

class TextNormalViewSet(viewsets.ModelViewSet):
    queryset = TextNormal.objects.all()
    serializer_class = TextNormalSerializer

class TextTagViewSet(viewsets.ModelViewSet):
    queryset = TextTag.objects.all()
    serializer_class = TextTagSerializer

class TagSetViewSet(viewsets.ModelViewSet):
    queryset = TagSet.objects.all()
    serializer_class = TagSetSerializer
    lookup_field = 'name'

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ValidatorViewSet(viewsets.ModelViewSet):
    queryset = Validator.objects.all()
    serializer_class = ValidatorSerializer
    lookup_field = 'name'


class NormalizerViewSet(viewsets.ModelViewSet):
    queryset = Normalizer.objects.all()
    serializer_class = NormalizerSerializer
    lookup_field = 'name'
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_automatic',)

    @action(detail=True, methods=['get',], url_name='train', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def train(self, request, name=None):
        normalizer = cache.normalizers.get(name, None)
        if not normalizer:
            raise NotFound(detail="Error 404, normalizer not found", code=404)
        normalizer.model_details['state'] = 'training'
        normalizer.save(update_fields=['model_details'])
        thread = threading.Thread(target=normalizer.train)
        logger.debug(f'> Start training normalizer {name} in parallel ...')
        thread.start()
        serializer = NormalizerSerializer(normalizer)
        return Response(serializer.data)

    @action(detail=True, methods=['get',], url_name='normalize', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def normalize(self, request, name=None):
        normalizer = cache.normalizers.get(name, None)
        if not normalizer:
            raise NotFound(detail="Error 404, normalizer not found", code=404)

        text_id = request.GET.get('text-id', None)
        if not text_id:
            raise ParseError(detail="Error 400, text-id not found", code=400)

        text = Text.objects.filter(id=text_id).first()
        if not text:
            raise NotFound(detail="Error 404, text not found", code=404)
        text_normal = normalizer.normalize(text)
        serializer = TextNormalSerializer(text_normal)
        return Response(serializer.data)

class TokenizerViewSet(viewsets.ModelViewSet):
    queryset = Tokenizer.objects.all()
    serializer_class = TokenizerSerializer
    lookup_field = 'name'
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_automatic',)

    @action(detail=True, methods=['get',], url_name='train', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def train(self, request, name=None):
        tokenizer = cache.tokenizers.get(name, None)
        if not tokenizer:
            raise NotFound(detail="Error 404, tokenizer not found", code=404)
        tokenizer.model_details['state'] = 'training'
        tokenizer.save(update_fields=['model_details'])
        thread = threading.Thread(target=tokenizer.train)
        logger.debug(f'> Start training tokenizer {name} in parallel ...')
        thread.start()
        serializer = TokenizerSerializer(tokenizer)
        return Response(serializer.data)

    @action(detail=True, methods=['get',], url_name='tokenize', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def tokenize(self, request, name=None):
        tokenizer = cache.tokenizers.get(name, None)
        if not tokenizer:
            raise NotFound(detail="Error 404, tokenizer not found", code=404)

        text_id = request.GET.get('text-id', None)
        if not text_id:
            raise ParseError(detail="Error 400, text-id not found", code=400)

        text = Text.objects.filter(id=text_id).first()
        if not text:
            raise NotFound(detail="Error 404, text not found", code=404)
        text_tag = tokenizer.tokenize(text)
        serializer = TextTagSerializer(text_tag)
        return Response(serializer.data)

class TaggerViewSet(viewsets.ModelViewSet):
    queryset = Tagger.objects.all()
    serializer_class = TaggerSerializer
    lookup_field = 'name'
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_automatic',)

    @action(detail=True, methods=['get',], url_name='train')
    @csrf_exempt
    def train(self, request, name=None):
        tagger = cache.taggers.get(name, None)
        if not tagger:
            raise NotFound(detail="Error 404, tagger not found", code=404)

        tagger.model_details['state'] = 'training'
        tagger.save(update_fields=['model_details'])
        thread = threading.Thread(target=tagger.train)
        logger.debug(f'> Start training tagger {name} in parallel ...')
        thread.start()  
        serializer = TaggerSerializer(tagger)
        return Response(serializer.data)

    @action(detail=True, methods=['get',], url_name='tag')
    @csrf_exempt
    def tag(self, request, name=None):
        tagger = cache.taggers.get(name, None)
        if not tagger:
            raise NotFound(detail="Error 404, tagger not found", code=404)

        text_tag_id = request.GET.get('text-tag-id', None)
        if not text_tag_id:
            raise ParseError(detail="Error 400, text-tag-id not found", code=400)

        logger.debug(f'text_tag_id : {text_tag_id}')
        text_tag = TextTag.objects.filter(id=text_tag_id).first()
        if not text_tag:
            raise NotFound(detail="Error 404, text tag not found", code=404)

        text_tag = tagger.tag(text_tag)
        serializer = TextTagSerializer(text_tag)
        return Response(serializer.data)





 # if name == 'refinement-normalizer':
        #     normalizer = RefinementNormalizer.objects.get(name=name)
        # elif name == 'replacement-normalizer':
        #     normalizer = ReplacementNormalizer.objects.get(name=name)
        # else:
        #     normalizer = self.get_object()
# class SentenceViewSet(viewsets.ModelViewSet):
#     queryset = Sentence.objects.all()
#     serializer_class = SentenceSerializer

# class NormalSentenceViewSet(viewsets.ModelViewSet):
#     queryset = NormalSentence.objects.all()
#     serializer_class = NormalSentenceSerializer

# class TaggedSentenceViewSet(viewsets.ModelViewSet):
#     queryset = TaggedSentence.objects.all()
#     serializer_class = TaggedSentenceSerializer

# class TranslationCharacterViewSet(viewsets.ModelViewSet):
#     queryset = TranslationCharacter.objects.all()
#     serializer_class = TranslationCharacterSerializer

# class RefinementPatternViewSet(viewsets.ModelViewSet):
#     queryset = RefinementPattern.objects.all()
#     serializer_class = RefinementPatternSerializer

 # content = {'normal_content': text.normal_content}
        # content = {'normal_content': text.normal_content}

        # return Response(content)

def init():
    global logger
    logger = logging.getLogger(__name__)
