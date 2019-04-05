import logging
from mohaverekhan.models import Tokenizer, TextTag
from mohaverekhan import cache

logger = None

class BitianistInformalTokenizer(Tokenizer):
    
    class Meta:
        proxy = True
    
    def train(self):
        pass
    
    def split_multi_token_word(self, token_content):
        fixed_token_content = [token_content]



        return fixed_token_content

    def split_multi_token_words(self, token_contents):
        fixed_token_contents = []
        for token_content in token_contents:
            fixed_token_contents += self.split_multi_token_word(token_content)

        return fixed_token_contents

    def tokenize(self, text):
        text_normal = cache.normalizers['bitianist-informal-refinement-normalizer']\
                            .normalize(text)
        token_contents = text.content.split(' ')
        token_contents = self.split_multi_token_words(token_contents)
        text_tag_tokens = []
        for token_content in token_contents:
            text_tag_tokens.append({'content': token_content})
        text_tag = TextTag.objects.create(text=text, 
                Tokenizer=self, tokens=text_tag_tokens)
        return text_tag

def init():
    global logger
    logger = logging.getLogger(__name__)