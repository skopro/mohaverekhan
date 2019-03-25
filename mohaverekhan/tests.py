from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
# from rest_framework.test import APIRequestFactory
from django.urls import reverse

from .models import (Normalizer, Text, NormalText, 
            TagSet, Tag, Tagger,
            Sentence, TaggedSentence, TranslationCharacter, 
            RefinementPattern)

import json
from mohaverekhan.core.tools import data_importer

base_api_url = r'http://127.0.0.1:8000/mohaverekhan/api'
normalizers_url = fr'{base_api_url}/normalizers'
texts_url = fr'{base_api_url}/texts'
normal_texts_url = fr'{base_api_url}/normal-texts'
tags_url = fr'{base_api_url}/tags'
tag_sets_url = fr'{base_api_url}/tag-sets'
taggers_url = fr'{base_api_url}/taggers'
sentences_url = fr'{base_api_url}/sentences'
tagged_sentences_url = fr'{base_api_url}/tagged-sentences'
translation_character_url = fr'{base_api_url}/rules/translation-characters'
refinement_pattern_url = fr'{base_api_url}/rules/refinement-patterns'


class NormalizerViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        model_details = {
            'state': 'not-trained'
        }
        refinement_normalizer = data_importer.generate_tagger_dictionary(
            'refinement-normalizer',
            owner='bitianist',
            model_type='rule-based',
            model_details=model_details
        )
        # data = json.dumps(refinement_normalizer).encode('utf-8')
        self.client.post(normalizers_url, refinement_normalizer, format='json')
        
    

    def test_refinement_normalizer(self):
        """
        If no questions exist, an appropriate message is displayed.
        """

        normal_text_equivalents = (
            (r'سلاااااااااااااااااااااااام چطوووووووووری؟؟', r'سلام چطوووووووووری ؟'),
            (r'باید بریم ... اوکی؟', r'باید بریم … اوکی ؟'),
            (r'0123456789 “كي”%?', r'۰۱۲۳۴۵۶۷۸۹ « کی » ٪ ؟')
        )

        text_content = ''
        normal_text_content = ''

        for text_content, normal_text_content in normal_text_equivalents:
            text = Text.objects.create(content=text_content)
            response = self.client.get(
                f'{normalizers_url}/refinement-normalizer/normalize?text-id={text.id}', 
                # {'name': 'refinement-normalizer', 'text-id': text.id},
                format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['content'], normal_text_content)
        # self.assertContains(response, "No polls are available.")
        # self.assertQuerysetEqual(response.context['latest_question_list'], [])

# class WordModelTestCase(TestCase):
#     def setUp(self):
#         self.word = Word(formal = 'نان', informal = 'نون')

#     def test_model_can_create(self):
#         old_count = Word.objects.count()
#         self.word.save()
#         new_count = Word.objects.count()
#         self.assertNotEqual(old_count, new_count)

# class WordViewTestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.word_json = {'formal': 'نان', 'informal': 'نون'}
#         self.response = self.client.post(
#             reverse('create'),
#             self.word_json,
#             format="json")
    
#     def test_api_can_create(self):
#         print('skoooooooooooooooooopro\n\n')
#         print('\n\ncontent : {}\n\n'.format(self.response.content))
#         self.assertLogs(self.response.content)
#         self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)

    # def test_api_can_get(self):
    #     word = Word.objects.get()
    #     response = self.client.get(
    #         reverse('details',
    #         kwargs={'pk': word.id}), format="json")
            
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertContains(response, word)

    # def test_api_can_delete(self):
    #     word = Word.objects.get()
    #     response = self.client.delete(
    #         reverse('details', kwargs={'pk': word.id}),
    #         format='json',
    #         follow=True)

    #     self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
    
    # def test_api_can_update(self):
    #     change_word = {'formal': 'میدان', 'informal': 'میدون'}
    #     word = Word.objects.get()
    #     res = self.client.put(
    #         reverse('details', kwargs={'pk': word.id}),
    #         change_word, format='json')
    
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
