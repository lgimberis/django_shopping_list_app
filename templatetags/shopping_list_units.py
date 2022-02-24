from django import template
import re

register = template.Library()


@register.filter(name='shopping_list_units')
def shopping_list_units(ingredient_list):
    amount_tracker = {}
    final_amount = ""
    for ingredient in ingredient_list:
        amount = ingredient.amount
        if not amount:
            final_amount = "Some"
        if match := re.match(r'(\d+)(\s*)(\w*)', amount):
            key = (" " if len(match.group(2)) > 0 else "") + match.group(3)
            try:
                amount_tracker[key] += int(match.group(1))
            except KeyError:
                amount_tracker[key] = int(match.group(1))
    addition = "+".join([f"{v}{k}" for k, v in amount_tracker.items()])
    if final_amount and addition:
        final_amount = f"{final_amount}+{addition}"
    else:
        final_amount = addition
    product = ingredient_list[0].product
    if final_amount == "1" or not product.pluralised_name:
        return f"{final_amount} {product.name}"
    else:
        return f"{final_amount} {product.pluralised_name}"