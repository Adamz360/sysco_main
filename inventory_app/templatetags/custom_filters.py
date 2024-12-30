from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def add_class(value, class_name):
    return value.as_widget(attrs={'class': class_name})