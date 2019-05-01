from django.apps import AppConfig
import logging
logger = logging.getLogger(__name__)

class MohaverekhanConfig(AppConfig):
    name = 'mohaverekhan'
    verbose_name = "Informal Persian Part Of Speech Tagging"

    def ready(self):
        
        from mohaverekhan import cache, utils
        cache.init()

        from mohaverekhan import serializers, views
        serializers.init()
        views.init()
