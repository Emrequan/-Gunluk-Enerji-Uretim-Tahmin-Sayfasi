from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the arg.
    """
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """
    Adds the arg to the value.
    """
    try:
        if isinstance(value, str):
            return str(value) + str(arg)
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except:
        return 0

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def stringformat(value, arg):
    """
    Formats the value according to the arg, a string formatting specifier.
    """
    try:
        return format(int(value), arg)
    except (ValueError, TypeError):
        return value 