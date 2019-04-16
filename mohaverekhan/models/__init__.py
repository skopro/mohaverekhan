from .base_models import (
    Word, WordNormal,
    Text, TextNormal, TextTag,
    TagSet, Tag, Token, TokenTag,
    Normalizer,
    Tagger, Validator,
    UTF8JSONField, UTF8JSONFormField,
)
from .normalizers.mohaverekhan_basic_normalizer.model \
    import MohaverekhanBasicNormalizer
from .normalizers.mohaverekhan_correction_normalizer.model \
    import MohaverekhanCorrectionNormalizer
from .normalizers.mohaverekhan_replacement_normalizer.model \
    import MohaverekhanReplacementNormalizer
from .normalizers.mohaverekhan_seq2seq_normalizer.model \
    import MohaverekhanSeq2SeqNormalizer

from .taggers.mohaverekhan_correction_tagger.model \
    import MohaverekhanCorrectionTagger
from .taggers.mohaverekhan_seq2seq_tagger.model \
    import MohaverekhanSeq2SeqTagger
