from rest_framework.response import Response
from rest_framework.exceptions import ParseError
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

from .serializers import (NormalizerSerializer, TextSerializer,
            NormalTextSerializer, TagSetSerializer,
            TagSerializer, TaggerSerializer, SentenceSerializer,
            TaggedSentenceSerializer, TranslationCharacterSerializer,
            RefinementPatternSerializer)
from .models import (Normalizer, Text, NormalText, 
            TagSet, Tag, Tagger, Sentence, TaggedSentence, 
            TranslationCharacter, RefinementPattern,
            RefinementNormalizer, NLTKTagger)
from django.views.decorators.csrf import csrf_exempt
import threading 
import json


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

class NormalizerViewSet(viewsets.ModelViewSet):
    queryset = Normalizer.objects.all()
    serializer_class = NormalizerSerializer
    lookup_field = 'name'
    # filterset_fields = ('is_manual',)

    @action(detail=False, methods=['get',], url_name='train')
    @csrf_exempt
    def train(self, request):
        logger.debug('train')
        text = Text()
        thread = threading.Thread(target=text.learn_model)
        logger.debug('start parallel')
        thread.start()  
        logger.debug('next line after thread.start()')
        
        content = {'state': 'finished'}
        return Response(content)

    @action(detail=True, methods=['get',], url_name='normalize', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def normalize(self, request, name=None):
        normalizer = None
        if name == 'refinement-normalizer':
            normalizer = RefinementNormalizer.objects.get(name=name)
        else:
            normalizer = self.get_object()
        text_id = request.GET.get('text-id', None)
        text = Text.objects.get(id=text_id)
        normal_text = normalizer.normalize(text)
        serializer = NormalTextSerializer(normal_text)
        return Response(serializer.data)
       

class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    filterset_fields = ('id',)

class NormalTextViewSet(viewsets.ModelViewSet):
    queryset = NormalText.objects.all()
    serializer_class = NormalTextSerializer

class TagSetViewSet(viewsets.ModelViewSet):
    queryset = TagSet.objects.all()
    serializer_class = TagSetSerializer
    lookup_field = 'name'

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class TaggerViewSet(viewsets.ModelViewSet):
    queryset = Tagger.objects.all()
    serializer_class = TaggerSerializer
    lookup_field = 'name'
    filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('is_manual', 'model_name')

    @action(detail=True, methods=['get',], url_name='train')
    @csrf_exempt
    def train(self, request, name=None):
        tagger = None
        if name == 'nltk-tagger':
            tagger = NLTKTagger.objects.get(name=name)
        else:
            tagger = self.get_object()

        tagger.model_details['state'] = 'training'
        tagger.save(update_fields=['model_details'])
        thread = threading.Thread(target=tagger.train)
        logger.debug(f'> Start training tagger {name} in parallel ...')
        thread.start()  
        logger.debug(f'> End training tagger {name} in parallel.')
        
        serializer = TaggerSerializer(tagger)
        return Response(serializer.data)

    @action(detail=True, methods=['get',], url_name='tag')
    @csrf_exempt
    def tag(self, request, name=None):
        tagger = None
        if name == 'nltk-tagger':
            tagger = NLTKTagger.objects.get(name=name)
        else:
            tagger = self.get_object()

        text_id = request.GET.get('text-id', None)
        logger.debug(f'text_id : {text_id}')
        text = Text.objects.get(id=text_id)
        # if tagger not in text.sentences[0].taggers:
        text = tagger.tag(text)
        serializer = TextSerializer(text)
        return Response(serializer.data)

    @action(detail=True, methods=['get',], url_name='tag2', renderer_classes=[renderers.JSONRenderer,])
    @csrf_exempt
    def tag2(self, request, name=None):
        tagger = self.get_object()
        logger.debug(f'>> name {name} ')
        text_id = request.GET.get('text-id', None)
        logger.debug(f'>> text_id {text_id} ')
        if text_id:
            text = Text.objects.get(id=text_id) 
            tagger.tag_text(text)
            serializer = TextSerializer(text)
            return Response(serializer.data)

        normal_text_id = request.GET.get('normal-text-id', None)
        logger.debug(f'>> normal_text_id {normal_text_id} ')
        if normal_text_id:
            normal_text = NormalText.objects.get(id=text_id) 
            tagger.tag_normal_text(normal_text)
            serializer = NormalTextSerializer(normal_text)
            return Response(serializer.data)

        raise ParseError(detail='Query parameters [text-id] or [normal-text-id] is required.')
        # return Response(f'text_id : {text_id}\nnormal_text_id : {normal_text_id}')

        # tagger = Tagger.objects.get(name=name)
        # text = tagger.tag(request.data['text'])

        # serializer = TextSerializer(instance=text)
        # logger.info(f'> Serializer.data : {serializer.data}')
        # return Response(serializer.data)

    @action(detail=False, methods=['get',], url_name='learn_model')
    @csrf_exempt
    def learn_model(self, request):
        logger.debug('learn_model')
        text = Text()
        thread = threading.Thread(target=text.learn_model)
        logger.debug('start parallel')
        thread.start()  
        logger.debug('next line after thread.start()')
        
        content = {'state': 'finished'}
        return Response(content)
        
class SentenceViewSet(viewsets.ModelViewSet):
    queryset = Sentence.objects.all()
    serializer_class = SentenceSerializer

class TaggedSentenceViewSet(viewsets.ModelViewSet):
    queryset = TaggedSentence.objects.all()
    serializer_class = TaggedSentenceSerializer

class TranslationCharacterViewSet(viewsets.ModelViewSet):
    queryset = TranslationCharacter.objects.all()
    serializer_class = TranslationCharacterSerializer

class RefinementPatternViewSet(viewsets.ModelViewSet):
    queryset = RefinementPattern.objects.all()
    serializer_class = RefinementPatternSerializer

 # content = {'normal_content': text.normal_content}
        # content = {'normal_content': text.normal_content}

        # return Response(content)

def init():
    global logger
    logger = logging.getLogger(__name__)
