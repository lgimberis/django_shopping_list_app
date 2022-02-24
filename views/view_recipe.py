import logging
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic import ListView

from ..models import Recipe, Ingredient
from ..forms import RecipeForm
from ..util import match_name, add_ingredient_from_form

logger = logging.getLogger(__name__)


class RecipeListView(ListView):
    model = Recipe
    paginate_by = 100

    def get_queryset(self):
        return Recipe.objects.exclude(name__iexact="Auto")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RecipeForm()
        return context


@login_required
def recipe_detail_view(request, recipe_name):
    if recipe_name.lower() == "auto":
        closest_recipe, _ = Recipe.objects.get_or_create(
            name='Auto'
        )
        good_match = True
        template_name = "shopping_list/auto_shopping.html"
    else:
        recipe_name = recipe_name.replace('-', ' ')
        closest_recipe, good_match = match_name(recipe_name, Recipe.objects)
        template_name = "shopping_list/recipe_detail.html"

    if good_match:
        form = add_ingredient_from_form(request, on_shopping_list=False, recipe=closest_recipe)
        context = {"form": form, "recipe": closest_recipe}
        return render(request, template_name, context=context)
    else:
        # Return recipe no result view
        error_context = {
            "error": f"No such recipe '{recipe_name}' found.",
            "best_guess_name": closest_recipe.name,
            "best_guess_slug": closest_recipe.name.replace(" ", "-").lower(),
        }
        best_guess_slug = closest_recipe.name.replace(" ","-").lower()
        messages.error(request, f"No such recipe '{recipe_name}' found. Did you mean <a href=\"{reverse('recipe-detail', args=[best_guess_slug])}\">{closest_recipe.name}</a>?", extra_tags="safe")
        return RecipeListView.as_view()(request)


@login_required
def auto_shopping(request):
    """Show the auto-shopping list."""
    return recipe_detail_view(request, "Auto")


@login_required
def recipe_create(request):
    """Create a new recipe.

    The relevant form is placed within the RecipeListView, because its footprint is very small.
    """
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe_name = form.cleaned_data['name']
            if not Recipe.objects.filter(name__iexact=recipe_name).exists():
                recipe = form.save()
                return HttpResponseRedirect(reverse('recipe-detail', args=[recipe.name.replace(" ", "-")]))
            else:
                messages.error(request, f"The recipe {recipe_name} already exists!")
    return HttpResponseRedirect(reverse('recipes'))


@login_required
def recipe_delete(request, pk):
    """Deletes the recipe with id 'pk' and returns the user to the recipe list view.
    """
    if request.method == "POST":
        try:
            recipe = Recipe.objects.get(pk=pk)
            if recipe.name != "Auto":
                recipe.delete()
        except Recipe.DoesNotExist:
            logger.error(f"Remove recipe called for id {pk} which cannot be found.")
    return HttpResponseRedirect(reverse('recipes'))


def recipe_to_shopping_list(request, pk):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            recipe = Recipe.objects.get(pk=pk)

            for ingredient in recipe.ingredient_set.all():
                list_ingredient = Ingredient()
                list_ingredient.product = ingredient.product
                list_ingredient.amount = ingredient.amount
                list_ingredient.on_shopping_list = True
                list_ingredient.recipe = recipe
                list_ingredient.added_by = request.user
                list_ingredient.save()
            return HttpResponseRedirect(reverse("shopping-index"))
        except Recipe.DoesNotExist:
            logger.error(f"Recipe with id {pk} not found")


def remove_from_recipe(request, pk=None, on_shopping_list=False):
    if request.method == "POST":
        if pk:
            recipe = Recipe.objects.get(pk=pk)
        else:
            recipe = None

        for key in filter(lambda x: "ingredient-id" in x, request.POST.keys()):
            if request.POST[key] == "delete":
                ingredient_pk = re.search(r"ingredient-id-(\d+)", key).group(1)
                try:
                    ingredient = Ingredient.objects.get(pk=ingredient_pk)
                    name = ingredient.product.name
                    if recipe:
                        base_set = recipe.ingredient_set  # Only delete ingredients from this recipe
                    else:
                        base_set = Ingredient.objects.all()  # No recipe -> Delete from all recipes (dangerous!)
                    for same_named_ingredient in base_set.filter(on_shopping_list=on_shopping_list, 
                                                                           product__name__iexact=name):
                        same_named_ingredient.delete()
                except Ingredient.DoesNotExist:
                    pass  # We don't care, because we were going to delete it anyway
    return HttpResponseRedirect(request.POST['next'])


class UserRecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    paginate_by = 100
    template_name = "shopping_list/recipe_list.html"

    def get_queryset(self):
        return Recipe.objects.filter(added_by=self.request.user)
