from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class MohaverekhanConfig(AppConfig):
    name = 'mohaverekhan'
    verbose_name = "Informal Persian Part Of Speech Tagging"

    def ready(self):
        

        from mohaverekhan.core.tools import utils, normalizer, tokenizer, sentence_splitter, cache
        utils.init()
        cache.init()
        
        from mohaverekhan import serializers, models, views
        serializers.init()
        models.init()
        views.init()

        # normalizer.init()
        # tokenizer.init()
        # sentence_splitter.init()
        
        # from mohaverekhan.core.nltk_taggers import model as nltk_taggers_model
        # nltk_taggers_model.init()