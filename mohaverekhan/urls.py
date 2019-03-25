from django.urls import path, include
from django.conf.urls import url, re_path
#from rest_framework.urlpatterns import format_suffix_patterns
from .views import (HomePageView, 
        NormalizerViewSet, TextViewSet, NormalTextViewSet, 
        TagViewSet, TagSetViewSet,
        TaggerViewSet, SentenceViewSet, TaggedSentenceViewSet, 
        TranslationCharacterViewSet, RefinementPatternViewSet)
from rest_framework.routers import DefaultRouter, SimpleRouter

# class OptionalSlashRouter(SimpleRouter):

#     def __init__(self):
#         self.trailing_slash = '/?'
#         super().__init__()
#         # super(SimpleRouter, self).__init__()

class OptionalSlashRouter(DefaultRouter): 
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        # super(DefaultRouter, self).__init__(*args, **kwargs) 
        self.trailing_slash = '/?'

router = OptionalSlashRouter()
# router.register(r'', HomeViewSet, basename='home')
# router.register(r'api', router.APIRootView, basename='api')
# router.register(r'schema', router.APISchemaView, basename='schema')
router.register(r'normalizers', NormalizerViewSet)
router.register(r'texts', TextViewSet)
router.register(r'normal-texts', NormalTextViewSet)
router.register(r'tags', TagViewSet)
router.register(r'tag-sets', TagSetViewSet)
router.register(r'taggers', TaggerViewSet)
router.register(r'sentences', SentenceViewSet)
router.register(r'tagged-sentences', TaggedSentenceViewSet)
router.register(r'rules/translation-characters', TranslationCharacterViewSet)
router.register(r'rules/refinement-patterns', RefinementPatternViewSet)

urlpatterns = [
    re_path(r'^$', HomePageView.as_view(), name='home'),
    re_path(r'^api/', include(router.urls)),
]

# urlpatterns = [
# #    url('', HomePageView.as_view(), name = 'home'),
#     path('', views.index, name='home'),
#     path('word/', WordCreateView.as_view(), name="words"),
#     path('word/<int:pk>/', WordDetailsView.as_view(), name="word"),
#     path('text/fix/', views.fix_text, name="fix_text"),
# ]

#urlpatterns = format_suffix_patterns(urlpatterns)

