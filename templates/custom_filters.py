from django import template

register = template.Library()

@register.filter
def map_attribute(queryset, attribute):
    return [getattr(obj, attribute) for obj in queryset]