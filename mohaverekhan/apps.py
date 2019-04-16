from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class MohaverekhanConfig(AppConfig):
    name = 'mohaverekhan'
    verbose_name = "Informal Persian Part Of Speech Tagging"

    def ready(self):
        

        from mohaverekhan import cache
        cache.init()

        # from mohaverekhan.models.

        from mohaverekhan import serializers, views
        serializers.init()
        views.init()

        # models.normalizers.mohaverekhan_seq2seq_normalizer.model.init()
