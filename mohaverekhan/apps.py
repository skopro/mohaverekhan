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
        
        models.normalizers.refinement.model.init()
        models.normalizers.replacement.model.init()
        models.normalizers.seq2seq.model.init()

        models.tokenizers.bitianist.model.init()

        models.taggers.formal.model.init()
        models.taggers.informal.model.init()

        cache.init()
        


        from mohaverekhan import serializers, views
        serializers.init()
        views.init()



        # normalizer.init()
        # tokenizer.init()
        # sentence_splitter.init()
        
        # from mohaverekhan.machine_learning_models.nltk_taggers import model as nltk_taggers_model
        # nltk_taggers_model.init()