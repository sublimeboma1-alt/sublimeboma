from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attribute):
    """Somme un attribut sur un queryset"""
    if not queryset:
        return 0
    total = 0
    for item in queryset:
        try:
            # Accéder à l'attribut via getattr
            value = getattr(item, attribute)
            if value:
                total += value
        except:
            pass
    return total