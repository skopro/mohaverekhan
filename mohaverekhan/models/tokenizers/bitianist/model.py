import logging
from mohaverekhan.models import Tagger, TextTag
from mohaverekhan import cache

logger = None

class BitianistTokenizer(Tagger):
    
    class Meta:
        proxy = True
    
    def train(self):
        pass
    
    def tokenize(self, text):
        token_contents = text.content.split(' ')
        text_tag_tokens = []
        for token_content in token_contents:
            text_tag_tokens.append({'content': token_content})
        text_tag = TextTag.objects.create(text=text, 
                Tokenizer=self, tokens=text_tag_tokens)
        return text_tag

def init():
    global logger
    logger = logging.getLogger(__name__)