from django import template

register = template.Library()

@register.filter
def get_from_dict(dictionary, key):
    """
    Safely get a value from a dictionary using a key.
    """
    if dictionary and key in dictionary:
        return dictionary[key]
    return []