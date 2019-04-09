from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count 

from .models import (
            Word, WordNormal,
            Text, TextNormal, TextTag,
            TagSet, Tag, Token, TokenTag,
            Normalizer,
            Tagger, Validator
            )

class WordNormalInline(admin.TabularInline):
    model = Word.normalizers.through
    fk_name = 'word'
    fields = ('content', 'word', 'normalizer', 
            'is_valid', 'validator', 'created', 'id')
    readonly_fields = ['content', 'is_valid', 'validator',
            'word', 'normalizer', 'created', 'id']
    extra = 0
    max_num = 25

class WordAdmin(admin.ModelAdmin):
    list_display = ('content', 'created',)
    search_fields = ['content', 'id']
    ordering = ('-created',)
    list_filter = []
    readonly_fields = ['created', 'id', 'normalizers',]
    
    fieldsets = (
        (None, {
            'fields': ('created', 'content')
        }),
    )

    inlines = [
        WordNormalInline
    ]

class WordNormalAdmin(admin.ModelAdmin):
    list_display = ('content', 'get_word_content', 'is_valid', 
            'get_normalizer_name', 'get_validator_name', 
            'created')
    search_fields = ['content', 'id']
    list_filter = ['is_valid', 'normalizer__name', 'validator__name']
    ordering = ('-created',)
    readonly_fields = ['created', 'id', 'validator']

    fieldsets = (
        (None, {
            'fields': ('id', 'created',
                'content', 'is_valid')
        }),
        ('Relations', {
            'fields': ('normalizer', 'word', 'validator'),
        }),
    )

    def get_validator_name(self, obj):
        if not obj.validator:
            return None
        return obj.validator.name
    get_validator_name.admin_order_field = 'created' 
    get_validator_name.short_description = 'Validator Name'

    def get_normalizer_name(self, obj):
        if not obj.normalizer:
            return None
        return obj.normalizer.name
    get_normalizer_name.admin_order_field = 'created' 
    get_normalizer_name.short_description = 'Normalizer Name'

    def get_word_content(self, obj):
        if not obj.word:
            return None
        return obj.word.content
    get_word_content.admin_order_field = 'created' 
    get_word_content.short_description = 'Word Content'


class TextTagAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('get_tagged_tokens_html', 'get_text_content', 'is_valid', 
                    'accuracy', 'get_tagger_name', 
                    'get_validator_name', 'true_text_tag', 'created')
    search_fields = ['text__content']
    list_filter = ['is_valid', 'tagger__name']
    ordering = ('-created',)
    readonly_fields = ['created', 'id', 'text', 'get_text_content', 
                'tagged_tokens_html', 'tags_string']

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'get_text_content',
             'tagged_tokens', 'tagged_tokens_html', 'is_valid', 'accuracy', 
             'tags_string')
        }),
        ('Relations', {
            'fields': ('text', 'tagger', 'validator'),
        }),
    )
    
    def get_tagged_tokens_html(self, obj):
        return format_html(obj.tagged_tokens_html)
        # return format_html(
        #     '''
        #     <div style="background-color: #44444e !important;">
        #         {}
        #     </div>
        #     ''', obj.tagged_tokens_html)
    get_tagged_tokens_html.admin_order_field = 'created' 
    get_tagged_tokens_html.short_description = 'Tagged Tokens HTML'

    def get_validator_name(self, obj):
        if not obj.validator:
            return None
        return obj.validator.name
    get_validator_name.admin_order_field = 'created' 
    get_validator_name.short_description = 'Validator Name'

    
    def get_text_content(self, obj):
        if not obj.text:
            return None
        # return obj.text.content
        html = format_html('''
            <div style="direction: rtl !important;text-align: right;padding: 0.2vh 1.0vw 0.2vh 1.0vw;">
                {}
            </div>
            ''', format_html(obj.text.content.replace('\n', format_html('<br />'))))
        return html
    get_text_content.admin_order_field = 'created' 
    get_text_content.short_description = 'Text Content'

    def get_tagger_name(self, obj):
        if not obj.tagger:
            return None
        return obj.tagger.name
    get_tagger_name.admin_order_field = 'created' 
    get_tagger_name.short_description = 'Tagger Name'

class TextTagInTextInline(admin.TabularInline):
    model = TextTag
    fields = ('id', 'tagged_tokens', 'is_valid', 'accuracy', 'true_text_tag',
        'tagger', 'validator', 'created')
    readonly_fields = ['created', 'id', 'tagger', 'validator']
    extra = 0
    max_num = 25

class TextNormalInTextInline(admin.TabularInline):
    model = Text.normalizers.through
    fk_name = 'text'
    fields = ('id', 'content', 'is_valid', 'validator',
            'normalizer', 'created')
    readonly_fields = ['created', 'id', 'validator']
    extra = 0
    max_num = 25

class TextAdmin(admin.ModelAdmin):
    list_display = ('content', 'normalizers_sequence', 'created',
                    'total_text_tag_count', 'total_text_normal_count')
    search_fields = ['content', 'id']
    ordering = ('-created',)
    list_filter = ['normalizers_sequence',]
    readonly_fields = ['created', 'id', 'normalizers', 'normalizers_sequence',
        'total_text_tag_count', 'total_text_normal_count']
    # exclude = ('normalizers',)

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'content', 'normalizers_sequence',
            'total_text_tag_count', 'total_text_normal_count')
        }),
    )

    inlines = [
        TextTagInTextInline,
        TextNormalInTextInline
    ]

class TextNormalAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_valid', 'get_normalizer_name', 
            'get_text_content', 'get_validator_name', 
            'normalizers_sequence', 'total_text_tag_count', 
            'total_text_normal_count', 'created')
    search_fields = ['content', 'id']
    list_filter = ['is_valid', 'normalizer__name', 'validator__name', 
        'normalizers_sequence']
    ordering = ('-created',)
    readonly_fields = ['created', 'id', 'validator', 'normalizers_sequence']

    fieldsets = (
        (None, {
            'fields': ('id', 'created',
                'content', 'is_valid', 'normalizers_sequence',
                'total_text_tag_count', 'total_text_normal_count')
        }),
        ('Relations', {
            'fields': ('normalizer', 'text', 'validator'),
        }),
    )

    inlines = [
        TextTagInTextInline,
        TextNormalInTextInline
    ]

    def get_validator_name(self, obj):
        if not obj.validator:
            return None
        return obj.validator.name
    get_validator_name.admin_order_field = 'created' 
    get_validator_name.short_description = 'Validator Name'

    def get_normalizer_name(self, obj):
        if not obj.normalizer:
            return None
        return obj.normalizer.name
    get_normalizer_name.admin_order_field = 'created' 
    get_normalizer_name.short_description = 'Normalizer Name'

    # def get_text_content(self, obj):
    #     if not obj.text:
    #         return None
    #     return obj.text.content
    # get_text_content.admin_order_field = 'created' 
    # get_text_content.short_description = 'Text Content'

    def get_text_content(self, obj):
        if not obj.text:
            return None
        # return obj.text.content
        html = format_html('''
            <div style="direction: rtl !important;text-align: right;padding: 0.2vh 1.0vw 0.2vh 1.0vw;">
                {}
            </div>
            ''', format_html(obj.text.content.replace('\n', format_html('<br />'))))
        return html
    get_text_content.admin_order_field = 'created' 
    get_text_content.short_description = 'Text Content'


class TagAdmin(admin.ModelAdmin):

    def get_color_html(self, obj):
        return format_html(
            f'''
            <div class="color-outer">
                <div class="color-text" >{obj.color}</div>
                <div class="color-box" style="background-color: {obj.color};"></div>
            </div>
            ''')
    get_color_html.admin_order_field = 'created' 
    get_color_html.short_description = 'Color'

    list_display = ('name', 'persian', 
                'get_color_html', 'tag_set', 'get_number_of_tokens', 
                'created')
    ordering = ('-tag_set', '-created')
    readonly_fields = ['created', 'id']
    list_filter = ['tag_set', 'name', 'persian']
    search_fields = ['persian']

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'name', 
                'persian', 'color', 'number_of_tokens')
        }),
        ('Relation', {
            'fields': ('tag_set',),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _number_of_tokens=Count("token", distinct=True),
        ).order_by('-_number_of_tokens')
        return queryset

    def get_number_of_tokens(self, obj):
        return obj.number_of_tokens
    get_number_of_tokens.admin_order_field = '-_number_of_tokens' 
    get_number_of_tokens.short_description = 'Number Of Tokens'

class TokenTagInTokenInline(admin.TabularInline):
    model = Token.tags.through
    fk_name = 'token'
    fields = ('token', 'tag', 
            'created', 'id')
    readonly_fields = ['created', 'id', 'tag']
    extra = 0
    max_num = 25

    def get_token_content(self, obj):
        if not obj.token:
            return None
        # return obj.token.content
        html = format_html('''
            <div style="direction: rtl !important;text-align: right;padding: 0.2vh 1.0vw 0.2vh 1.0vw;">
                {}
            </div>
            ''', format_html(obj.token.content))
        return html
    get_token_content.admin_order_field = 'created' 
    get_token_content.short_description = 'Token Content'

    def get_tag_name(self, obj):
        if not obj.tag:
            return None
        # return obj.token.content
        return obj.tag.name
    get_tag_name.admin_order_field = 'created' 
    get_tag_name.short_description = 'Tag Name'

    def get_tag_set_name(self, obj):
        if not obj.tag:
            return None
        # return obj.token.content
        return obj.tag.tag_set.name
    get_tag_set_name.admin_order_field = 'created' 
    get_tag_set_name.short_description = 'Tag Set Name'

class TokenAdmin(admin.ModelAdmin):
    list_display = ('content', 'get_number_of_tags', 'created')
    search_fields = ['content', 'id']
    ordering = ('-created',)
    list_filter = []
    readonly_fields = ['created', 'id', 'number_of_tags']
    # exclude = ('normalizers',)

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'content', 'number_of_tags',
                )
        }),
    )

    inlines = [
        TokenTagInTokenInline,
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _number_of_tags=Count("tags", distinct=True),
        ).order_by('-_number_of_tags')
        return queryset

    def get_number_of_tags(self, obj):
        return obj.number_of_tags
    get_number_of_tags.admin_order_field = '-_number_of_tags' 
    get_number_of_tags.short_description = 'Number Of Tags'

class TokenTagAdmin(admin.ModelAdmin):
    list_display = ('get_token_content', 'get_tag_name', 'get_tag_set_name',
                'number_of_repetitions', 'created')
    search_fields = ['token__content', 'id']
    ordering = ('-created', 'number_of_repetitions')
    list_filter = ['tag__tag_set__name', 'tag__name']
    readonly_fields = ['created', 'id', 'number_of_repetitions']
    # exclude = ('normalizers',)

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 
                'token', 'tag', 'number_of_repetitions',
                )
        }),
    )

    def get_token_content(self, obj):
        if not obj.token:
            return None
        # return obj.token.content
        html = format_html('''
            <div style="direction: rtl !important;text-align: right;padding: 0.2vh 1.0vw 0.2vh 1.0vw;">
                {}
            </div>
            ''', format_html(obj.token.content))
        return html
    get_token_content.admin_order_field = 'created' 
    get_token_content.short_description = 'Token Content'

    def get_tag_name(self, obj):
        if not obj.tag:
            return None
        # return obj.token.content
        return obj.tag.name
    get_tag_name.admin_order_field = 'created' 
    get_tag_name.short_description = 'Tag Name'

    def get_tag_set_name(self, obj):
        if not obj.tag:
            return None
        # return obj.token.content
        return obj.tag.tag_set.name
    get_tag_set_name.admin_order_field = 'created' 
    get_tag_set_name.short_description = 'Tag Set Name'

    def get_number_of_repetitions(self, obj):
        return obj.number_of_repetitions
    get_number_of_repetitions.admin_order_field = '-created' 
    get_number_of_repetitions.short_description = 'Number Of Repetitions'

class TagInLine(admin.TabularInline):
    model = Tag
    fields = ('name', 'persian', 'color', 'number_of_tokens',
    'id', 'created')
    readonly_fields = ['created', 'id']
    extra = 0
    max_num = 25



class TagSetAdmin(admin.ModelAdmin):
    list_display = ('name',
            'number_of_tags', 'number_of_taggers',
            'total_text_tag_count',
            'total_valid_text_tag_count', 'created', 'last_update')
    ordering = ('-created',)
    readonly_fields = ['created', 'id', 'number_of_tags', 'number_of_taggers',
            'total_text_tag_count',
            'total_valid_text_tag_count']

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 
                'name')
        }),
        ('Rank', {
            'fields': ('number_of_tags', 'number_of_taggers',
                'total_text_tag_count',
                'total_valid_text_tag_count'),
        }),
    )

    inlines = [
        TagInLine
    ]


class NormalizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'show_name', 'owner', 'is_automatic', 
                'total_text_normal_count', 
                'total_valid_text_normal_count',
                'total_word_normal_count',
                'total_valid_word_normal_count',
                'get_model_details', 'last_update', 'created')
    ordering = ('-is_automatic', '-created')
    readonly_fields = ['created', 'id', 'texts', 'last_update',
                'total_text_normal_count', 
                'total_valid_text_normal_count',
                'total_word_normal_count',
                'total_valid_word_normal_count',
                ]
    list_filter = ['owner', 'is_automatic']

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'last_update', 'name', 'show_name', 
                'owner', 'is_automatic', 'model_details' )
        }),
        ('Rank', {
            'fields': (
                'total_text_normal_count', 
                'total_valid_text_normal_count',
                'total_word_normal_count',
                'total_valid_word_normal_count'
                ),
        }),
    )

    def get_model_details(self, obj):
        model_details = ''
        for key, value in obj.model_details.items():
            model_details += f'> {key} = {value}<br>'
        return format_html(model_details)
    get_model_details.admin_order_field = 'created' 
    get_model_details.short_description = 'Model Details'


class TaggerAdmin(admin.ModelAdmin):
    list_display = ('name', 'show_name', 'owner', 'is_automatic', 'tag_set', 
                'total_text_tag_count', 
                'total_valid_text_tag_count', 
                'get_model_details', 'last_update', 'created')
    ordering = ('-is_automatic', 'tag_set', '-created')
    readonly_fields = ['created', 'id', 'last_update',
                'total_text_tag_count', 
                'total_valid_text_tag_count', 
                ]
    list_filter = ['owner', 'is_automatic', 'tag_set']

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'last_update', 'name', 'show_name',
                    'owner', 'is_automatic', 'model_details', 'tag_set')
        }),
        ('Rank', {
            'fields': (
                'total_text_tag_count', 
                'total_valid_text_tag_count', 
            ),
        }),
    )

    # inlines = [
    #     TaggedSentenceInline
    # ]

    def get_model_details(self, obj):
        model_details = ''
        for key, value in obj.model_details.items():
            model_details += f'> {key} = {value}<br>'
        return format_html(model_details)
    get_model_details.admin_order_field = 'created' 
    get_model_details.short_description = 'Model Details'

class ValidatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'show_name', 'owner',
                'total_text_normal_count', 
                'total_word_normal_count',
                'total_text_tag_count',
                'created')
    ordering = ('-created',)
    readonly_fields = ['created', 'id',
                'total_text_normal_count', 
                'total_word_normal_count',
                'total_text_tag_count',
                ]
    list_filter = ['name', 'show_name',]

    fieldsets = (
        (None, {
            'fields': ('id', 'created', 'name', 'show_name',
                    )
        }),
        ('Rank', {
            'fields': (
                'total_text_normal_count', 
                'total_word_normal_count',
                'total_text_tag_count',
                ),
        }),
    )


admin.site.register(Word, WordAdmin)
admin.site.register(WordNormal, WordNormalAdmin)

admin.site.register(Text, TextAdmin)
admin.site.register(TextNormal, TextNormalAdmin)
admin.site.register(TextTag, TextTagAdmin)

admin.site.register(Tag, TagAdmin)
admin.site.register(TagSet, TagSetAdmin)
admin.site.register(Token, TokenAdmin)
admin.site.register(TokenTag, TokenTagAdmin)

admin.site.register(Normalizer, NormalizerAdmin)
admin.site.register(Tagger, TaggerAdmin)
admin.site.register(Validator, ValidatorAdmin)

# admin.site.register(Sentence, SentenceAdmin)
# admin.site.register(NormalSentence, NormalSentenceAdmin)
# admin.site.register(TaggedSentence, TaggedSentenceAdmin)
# admin.site.register(TranslationCharacter, TranslationCharacterAdmin)
# admin.site.register(RefinementPattern, RefinementPatternsAdmin)




# class TextSentenceInline(admin.TabularInline):
#     model = Sentence
#     fields = ('content', 'text', 'order', 'id', 'created')
#     readonly_fields = ['created', 'id']
#     extra = 0
#     max_num = 25


# class TranslationCharacterAdmin(admin.ModelAdmin):
#     list_display = ('source', 'destination', 'description', 'owner', 'is_valid', 'created')
#     list_filter = ('owner', 'is_valid')
#     ordering = ('is_valid', 'owner')
#     readonly_fields = ['created',]

# class RefinementPatternsAdmin(admin.ModelAdmin):
#     list_display = ('pattern', 'replacement', 'description', 'order', 'owner', 'is_valid', 'created')
#     list_filter = ('owner', 'is_valid')
#     ordering = ('order', 'is_valid', 'owner')
#     readonly_fields = ['created',]

# class SentenceAdmin(admin.ModelAdmin):
#     list_display = ('content', 'get_text_id', 'normalizers_sequence',
#                     'created',)
#     search_fields = ['content', 'id']
#     ordering = ('-created', 'text__id')
#     list_filter = ['normalizers_sequence',]
#     readonly_fields = ['created', 'id', 'normalizers', 'taggers', 'normalizers_sequence']
#     # exclude = ('taggers',)
    
#     fieldsets = (
#         (None, {
#             'fields': ('created', 'content', 'taggers', 'normalizers_sequence')
#         }),
#         ('Relations', {
#             'fields': ('text',),
#         }),
#     )

#     inlines = [
#         TaggedSentenceInline,
#         NormalSentenceInline
#     ]

#     def get_text_id(self, obj):
#         if not obj.text:
#             return None
#         return obj.text.id
#     get_text_id.admin_order_field = 'created' 
#     get_text_id.short_description = 'Text ID'

# class NormalSentenceAdmin(admin.ModelAdmin):
#     list_display = ('content', 'is_valid', 'normalizers_sequence', 'get_normalizer_name', 
#             'get_sentence_id', 'get_validator_name', 'created')
#     search_fields = ['content', 'id']
#     list_filter = ['is_valid', 'normalizer__name', 'validator__name', 'normalizers_sequence']
#     ordering = ('-created',)
#     readonly_fields = ['created', 'id', 'taggers', 'normalizers_sequence']

#     fieldsets = (
#         (None, {
#             'fields': ('id', 'created',
#                 'content', 'is_valid', 'taggers', 'normalizers_sequence')
#         }),
#         ('Relations', {
#             'fields': ('normalizer', 'sentence', 'validator'),
#         }),
#     )

#     inlines = [
#         TaggedSentenceInline
#     ]

#     def get_validator_name(self, obj):
#         if not obj.validator:
#             return None
#         return obj.validator.name
#     get_validator_name.admin_order_field = 'created' 
#     get_validator_name.short_description = 'Validator Name'

#     def get_normalizer_name(self, obj):
#         if not obj.normalizer:
#             return None
#         return obj.normalizer.name
#     get_normalizer_name.admin_order_field = 'created' 
#     get_normalizer_name.short_description = 'Normalizer Name'

#     def get_sentence_id(self, obj):
#         if not obj.sentence:
#             return None
#         return obj.sentence.id
#     get_sentence_id.admin_order_field = 'created' 
#     get_sentence_id.short_description = 'Sentence ID'



# class NormalSentenceInline(admin.TabularInline):
#     model = Sentence.normalizers.through
#     fk_name = 'sentence'
#     fields = ('id', 'content', 'is_valid', 'validator',
#             'sentence', 'normalizer', 'created')
#     readonly_fields = ['created', 'id', 'validator']
#     extra = 0
#     max_num = 25


# class TextNormalSentenceInline(admin.TabularInline):
#     model = Sentence
#     fields = ('content', 'order', 'id', 'created')
#     readonly_fields = ['created', 'id']
#     extra = 0
#     max_num = 25