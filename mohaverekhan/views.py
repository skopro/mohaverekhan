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
from joblib import Parallel, delayed
import random
import time

from .serializers import (
            WordSerializer, WordNormalSerializer,
            TextSerializer, TextNormalSerializer, TextTagSerializer,
            TagSetSerializer, TagSerializer, TokenSerializer,
            TokenTagSerializer,
            NormalizerSerializer,
            TaggerSerializer, ValidatorSerializer,
            )

from .models import (
            Word, WordNormal,
            Text, TextNormal, TextTag,
            TagSet, Tag, Token, TokenTag,
            Normalizer,
            Tagger, Validator
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

    @action(detail=True, methods=['get',], url_name='evaluate')
    @csrf_exempt
    def evaluate(self, request, pk=None):
        true_text_tag = self.get_object()

        predicted_text_id = request.GET.get('text-id', None)
        if not predicted_text_id:
            raise ParseError(detail="Error 400, predicted text-id not found", code=400)

        predicted_text_tag = TextTag.objects.filter(id=predicted_text_id).first()
        if not predicted_text_tag:
            raise NotFound(detail="Error 404, text tag not found", code=404)

        predicted_text_tag = true_text_tag.evaluate(predicted_text_tag)
        serializer = TextTagSerializer(predicted_text_tag)
        return Response(serializer.data)

class TagSetViewSet(viewsets.ModelViewSet):
    queryset = TagSet.objects.all()
    serializer_class = TagSetSerializer
    lookup_field = 'name'

class TokenViewSet(viewsets.ModelViewSet):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    lookup_field = 'content'

class TokenTagViewSet(viewsets.ModelViewSet):
    queryset = TokenTag.objects.all()
    serializer_class = TokenTagSerializer

    i = 0
    def update_token_tag_rank(self, token_tag_update):
        


        token_tag = TokenTag.objects.filter(
                        token__content=token_tag_update[0],
                        tag__name=token_tag_update[1],
                        tag__tag_set__name=token_tag_update[2]
                        ).first()
        if token_tag:
            token_tag.number_of_repetitions=token_tag_update[3]
            token_tag.save(update_fields=['number_of_repetitions']) 
        else:
            token, created = Token.objects.get_or_create(content=token_tag_update[0])
            tag = Tag.objects.get(name=token_tag_update[1], tag_set__name=token_tag_update[2])
            
            TokenTag.objects.create(
                token=token,
                tag=tag,
                number_of_repetitions=token_tag_update[3]
            )
        


        if self.i % 1000 == 0:
            logger.info(f'>> Updating token[{self.i}] : {token_tag_update[0]}')
        self.i += 1

    def update_rank_in_another_thread(self):
        beg_ts = time.time()
        cache.cache_token_tags_dic()

        self.i = 0
        token_tag_update_list = []
        for tag_set_name, token_tags in cache.tag_set_token_tags.items():
            logger.info(f'>>> Updating tag set {tag_set_name}')
            for token_content, tags in token_tags.items():
                for tag_name, tag_count in tags.items():
                    token_tag_update_list.append((token_content, tag_name, tag_set_name, tag_count))
        logger.info(f'> len token_tag_update_list : {len(token_tag_update_list)}')
        Parallel(n_jobs=96, verbose=20, backend='threading')(delayed(self.update_token_tag_rank)(token_tag_update) for token_tag_update in token_tag_update_list)
        end_ts = time.time()
        logger.info(f"> (Time)(Update repetitions)({end_ts - beg_ts:.6f})")
        

        # for text_tag_tokens in text_tag_tokens_list:
        #     for text_tag_token in text_tag_tokens:
        #         if text_tag_token['tag']['name'] == self.name:
        #             examples.add(text_tag_token['content'])
        #             if len(examples) >= 40:
        #                 break

        # tags = Tag.objects.all()
        # [tag.update_examples() for tag in tags]
        # Parallel(n_jobs=2, verbose=20, backend='threading')(delayed(tag.update_examples)() for tag in tags)

    @action(detail=False, methods=['get',], url_name='update_ranks')
    @csrf_exempt
    def update_ranks(self, request):
        # logger.debug(f'> Start update_examples of tags in parallel ...')
        # Parallel(n_jobs=-1, verbose=20)(delayed(tag.update_examples)() for tag in tags)
        thread = threading.Thread(target=self.update_rank_in_another_thread)
        logger.debug(f'> Start update_ranks of token tags in parallel ...')
        thread.start()
        return Response(status=200)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    # def update_examples_in_another_thread(self):
    #     text_tag_tokens_list = TextTag.objects.filter(is_valid=True)\
    #         .values_list('tagger__tag_set__name', 'tagged_tokens')

    #     logger.debug(f'> {self.name} text_tag_tokens_list.count() : {text_tag_tokens_list.count()} {type(text_tag_tokens_list)}')

    #     if not text_tag_tokens_list:
    #         return
        
    #     text_tag_tokens_list = list(text_tag_tokens_list)
    #     text_tag_tokens_list = random.sample(text_tag_tokens_list, int(len(text_tag_tokens_list)/2))
    #     [tag.update_examples(text_tag_tokens_list) for tag in Tag.objects.all()]
        

        # for text_tag_tokens in text_tag_tokens_list:
        #     for text_tag_token in text_tag_tokens:
        #         if text_tag_token['tag']['name'] == self.name:
        #             examples.add(text_tag_token['content'])
        #             if len(examples) >= 40:
        #                 break

        # tags = Tag.objects.all()
        # [tag.update_examples() for tag in tags]
        # Parallel(n_jobs=2, verbose=20, backend='threading')(delayed(tag.update_examples)() for tag in tags)

    # @action(detail=False, methods=['get',], url_name='update_examples')
    # @csrf_exempt
    # def update_examples(self, request):
    #     # logger.debug(f'> Start update_examples of tags in parallel ...')
    #     # Parallel(n_jobs=-1, verbose=20)(delayed(tag.update_examples)() for tag in tags)
    #     thread = threading.Thread(target=self.update_examples_in_another_thread)
    #     logger.debug(f'> Start update_examples of tags in parallel ...')
    #     thread.start()
        
        
    #     # for tag in tags:
    #         # thread = threading.Thread(target=tag.update_examples)
    #     #     logger.debug(f'> Start update_examples of tag {tag.name} in parallel ...')
    #     #     thread.start()
    #     return Response(status=200)

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

    # , renderer_classes=[renderers.JSONRenderer,]

    @action(detail=True, methods=['get',], url_name='train')
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

    @action(detail=True, methods=['get',], url_name='normalize')
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

        text_id = request.GET.get('text-id', None)
        if not text_id:
            raise ParseError(detail="Error 400, text-id not found", code=400)

        logger.debug(f'text_id : {text_id}')
        text = Text.objects.filter(id=text_id).first()
        if not text:
            raise NotFound(detail="Error 404, text not found", code=404)

        text_tag = tagger.tag(text)
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
