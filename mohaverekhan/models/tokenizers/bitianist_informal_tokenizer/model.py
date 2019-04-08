import logging
from mohaverekhan.models import Tokenizer, TextTag
from mohaverekhan import cache
import re

logger = None

class BitianistInformalTokenizer(Tokenizer):
    
    class Meta:
        proxy = True
    
    def train(self):
        pass

    pattern1 = re.compile(rf".+یه$") 
    pattern2 = re.compile(rf".+و$") 
    pattern3 = re.compile(rf".+شو$") 
    pattern4 = re.compile(rf".+ش$") 
    pattern41 = re.compile(rf".+هاش$") 
    pattern5 = re.compile(rf".+ه$")
    pattern6 = re.compile(rf".+ست$")
    pattern7 = re.compile(rf".+م$")
    
    def split_multi_token_word(self, token_content):
        # غذاش | 1 عالیه | 1 خفست | پیتزاهاش | بازم | 1 ازش | 1 منطقست | 1 مشتریش | 1 کتابه | 1 همونو | 1 درسته |
        # کتابارو | کتاباشو
        # شلوغیه 1
        logger.info(f'>> split_multi_token_word : {token_content}')
        if token_content in cache.token_set:
            logger.info(f'> {token_content} in cache')
            return [token_content]
        else:
            logger.info(f'> pattern1')
            if self.pattern1.match(token_content): # شلوغیه | عالیه
                logger.info(f'> token_content[0:-1] : {token_content[0:-1]}')
                if token_content[0:-1] in cache.token_set: # شلوغی | عالی
                    if token_content[0:-2] in cache.token_set: # شلوغ
                        return [token_content[0:-1]] # شلوغی
                    return [token_content[0:-1], 'ه'] # عالی ه

            logger.info(f'> pattern2')
            if self.pattern2.match(token_content): # همونو | اونو | کتابو | 
                if token_content[0:-1] in cache.token_set: # کتاب
                        return [token_content[0:-1], 'و'] # کتاب و
                elif token_content[0:-1].replace('و', 'ا') in cache.token_set: # همان
                        return [token_content[0:-1], 'و'] # همون و
                elif token_content[0:-1].replace('او', 'آ') in cache.token_set: # ان
                        return [token_content[0:-1], 'و'] # اون و
            
            logger.info(f'> pattern3')
            if self.pattern3.match(token_content): # کتابشو | خریدشو | میدونشو
                if token_content[0:-2] in cache.token_set: # کتاب | خرید
                        return [token_content[0:-2], 'ش', 'و'] # کتاب ش و | خرید ش و
                elif token_content[0:-2].replace('و', 'ا') in cache.token_set: # میدان
                        return [token_content[0:-2], 'ش', 'و'] # میدون ش و |
                elif token_content[0:-2].replace('او', 'آ') in cache.token_set:
                        return [token_content[0:-2], 'ش', 'و'] 
            
            logger.info(f'> pattern4')
            if self.pattern4.match(token_content): # کتابش | میدونش | مشتریش | ازش | 
                if token_content[0:-1] in cache.token_set: # کتاب | مشتری | از
                        return [token_content[0:-1], 'ش'] # کتاب ش | مشتری ش | از ش
                elif token_content[0:-1].replace('و', 'ا') in cache.token_set: # میدان
                        return [token_content[0:-1], 'ش'] # میدون ش
                elif token_content[0:-1].replace('او', 'آ') in cache.token_set: # 
                        return [token_content[0:-1], 'ش'] #
            
            logger.info(f'> pattern41')
            if self.pattern41.match(token_content): # پیتزاهاش | میدونهاش |
                if token_content[0:-3] in cache.token_set: # پیتزا
                        return [token_content[0:-1], 'ش'] # پیتزاها ش
                elif token_content[0:-3].replace('و', 'ا') in cache.token_set: # میدان
                        return [token_content[0:-1], 'ش'] # میدونها ش
                elif token_content[0:-3].replace('او', 'آ') in cache.token_set: # 
                        return [token_content[0:-1], 'ش'] #
                        

            logger.info(f'> pattern5')
            if self.pattern5.match(token_content): # کتابه | درسته | خوبه | میدونه | اونه
                if token_content == 'آخه':
                    return [token_content]
                if token_content[0:-1] in cache.token_set: # کتاب | درست | خوب
                        return [token_content[0:-1], 'ه'] # کتاب ه | درست ه | خوب ه
                elif token_content[0:-1].replace('و', 'ا') in cache.token_set: # میدون
                        return [token_content[0:-1], 'ه'] # میدون ه
                elif token_content[0:-1].replace('او', 'آ') in cache.token_set: # ان
                        return [token_content[0:-1], 'ه'] # اون ه
            
            logger.info(f'> pattern6')
            if self.pattern6.match(token_content): # بستست | منطقست | موندست
                if token_content[0:-2] + 'ه' in cache.token_set: # بسته | منطقه
                        return [token_content[0:-2], 'ست'] # بست ست | منطق است
                elif token_content[0:-2].replace('و', 'ا') + 'ه' in cache.token_set: # مانده
                        return [token_content[0:-2], 'ست'] # موند ست
                elif token_content[0:-2].replace('او', 'آ') + 'ه' in cache.token_set:
                        return [token_content[0:-2], 'ست'] # 

            logger.info(f'> pattern7')
            if self.pattern7.match(token_content): # بازم | کتابم | همونم |
                if token_content[0:-1] in cache.token_set: # باز | کتاب
                        return [token_content[0:-1], 'م'] # باز م | کتاب م
                elif token_content[0:-1].replace('و', 'ا') in cache.token_set: # همان
                        return [token_content[0:-1], 'م'] # همون م
                elif token_content[0:-1].replace('او', 'آ') in cache.token_set: #
                        return [token_content[0:-1], 'م'] #


        return [token_content]

    def split_multi_token_words(self, token_contents):
        fixed_token_contents = []
        for token_content in token_contents:
            fixed_token_contents += self.split_multi_token_word(token_content)

        logger.info(f'> fixed_token_contents : {fixed_token_contents}')
        return fixed_token_contents

    def tokenize(self, text):
        text_normal = cache.normalizers['bitianist-informal-refinement-normalizer']\
                            .normalize(text)
        text_tag, created = TextTag.objects.get_or_create(
            text=text_normal, 
            tokenizer=self
            )
        token_contents = text_normal.content.replace('\n', ' \\n ').split(' ')
        token_contents = self.split_multi_token_words(token_contents)
        text_tag_tokens = []
        for token_content in token_contents:
            text_tag_tokens.append({'content': token_content})
        text_tag.tokens = text_tag_tokens
        text_tag.save()
        return text_tag

def init():
    global logger
    logger = logging.getLogger(__name__)