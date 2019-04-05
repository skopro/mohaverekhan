from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class MohaverekhanConfig(AppConfig):
    name = 'mohaverekhan'
    verbose_name = "Informal Persian Part Of Speech Tagging"

    def ready(self):
        

        from mohaverekhan import utils, cache
        utils.init()

        from mohaverekhan import models
        models.base_models.init()
        
        models.normalizers.bitianist_informal_refinement_normalizer.model.init()
        models.normalizers.bitianist_informal_replacement_normalizer.model.init()
        models.normalizers.bitianist_informal_seq2seq_normalizer.model.init()

        models.tokenizers.bitianist_informal_tokenizer.model.init()

        models.taggers.bitianist_formal_nltk_tagger.model.init()
        models.taggers.bitianist_informal_nltk_tagger.model.init()

        cache.init()
        


        from mohaverekhan import serializers, views
        serializers.init()
        views.init()



        # normalizer.init()
        # tokenizer.init()
        # sentence_splitter.init()
        
        # from mohaverekhan.machine_learning_models.nltk_taggers import model as nltk_taggers_model
        # nltk_taggers_model.init()