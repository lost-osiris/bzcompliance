from django.template.defaultfilters import stringfilter
from django import template
register = template.Library()

@register.filter
@stringfilter
def get_item(dictionary, key):
    return dictionary.get(key)
