from fuzzywuzzy import fuzz, process

from .models import Ingredient
from .forms import ShoppingListIngredientForm

def match_name(name, objects):
    matched_objects = objects.filter(name__iexact=name)
    if matched_objects.count():
        return matched_objects[0], True
    else:
        # No matching results - return a list ordered with Levenshtein Distance
        best_name, best_score = process.extractOne(name, [trial.name for trial in objects.all()])
        return objects.get(name=best_name), best_score > 90

def add_ingredient_from_form(request, on_shopping_list=False, recipe=None):
    if request.method == "POST":
        # Try to add the item to the shopping list
        form = ShoppingListIngredientForm(request.POST)
        if form.is_valid():
            shopping_list_item = Ingredient()

            shopping_list_item.product = form.cleaned_data['product']
            shopping_list_item.on_shopping_list = on_shopping_list
            shopping_list_item.added_by = request.user
            if recipe:
                shopping_list_item.recipe = recipe
            shopping_list_item.amount = form.cleaned_data['amount']
            shopping_list_item.save()
            form = ShoppingListIngredientForm()
    else:
        # Create a blank form
        form = ShoppingListIngredientForm()
    return form