import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView

from ..forms import RecipeForm, ShoppingListIngredientForm
from ..models import Ingredient, Recipe
from ..util import get_shopping_list_group, group_required, match_name

logger = logging.getLogger(__name__)


class RecipeListView(LoginRequiredMixin, ListView):
    login_url = reverse("account_login")
    model = Recipe
    paginate_by = 100

    def get_queryset(self):
        return Recipe.objects.filter(
            group=get_shopping_list_group(self.request.user)
        ).exclude(name__iexact="Auto")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = RecipeForm()
        return context


def add_ingredient_from_form(request, on_shopping_list=False, recipe=None):
    if request.method == "POST":
        # Try to add the item to the shopping list
        form = ShoppingListIngredientForm(request.POST)
        if form.is_valid():
            shopping_list_item = Ingredient()

            shopping_list_item.product = form.cleaned_data["product"]
            shopping_list_item.on_shopping_list = on_shopping_list
            shopping_list_item.added_by = request.user
            if recipe:
                shopping_list_item.recipe = recipe
            shopping_list_item.amount = form.cleaned_data["amount"]
            shopping_list_item.save()
            form = ShoppingListIngredientForm()
    else:
        # Create a blank form
        form = ShoppingListIngredientForm()
    return form


@group_required
def recipe_detail_view(request, group, recipe_name):
    if recipe_name.lower() == "auto":
        closest_recipe, _ = Recipe.objects.get_or_create(
            name="Auto",
            group=group,
        )
        good_match = True
        template_name = "shopping_list/auto_shopping.html"
    else:
        recipe_name = recipe_name.replace("-", " ")
        closest_recipe, good_match = match_name(
            recipe_name, Recipe.objects.filter(group=group)
        )
        template_name = "shopping_list/recipe_detail.html"

    if good_match:
        form = add_ingredient_from_form(
            request, on_shopping_list=False, recipe=closest_recipe
        )
        context = {
            "form": form,
            "recipe": closest_recipe,
            "ingredient_list": closest_recipe.ingredient_set.filter(
                on_shopping_list=False
            ).order_by(Lower("product__category__name"), Lower("product__name")),
        }
        return render(request, template_name, context=context)
    else:
        # Return recipe no result view
        best_guess_slug = closest_recipe.name.replace(" ", "-").lower()
        best_guess_url = reverse("recipe-detail", args=[best_guess_slug])
        messages.error(
            request,
            (
                f'No such recipe "{recipe_name}" found. Did you mean '
                f'<a href="{best_guess_url}">{closest_recipe.name}</a>?)'
            ),
            extra_tags="safe",
        )
        return RecipeListView.as_view()(request)


def auto_shopping(request):
    """Show the auto-shopping list."""
    return recipe_detail_view(request, "Auto")


@group_required
def recipe_create(request, group):
    """Create a new recipe.

    The relevant form is placed within the RecipeListView, because its footprint is very small.
    """
    if request.method == "POST":
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe_name = form.cleaned_data["name"]
            if not Recipe.objects.filter(
                name__iexact=recipe_name, group=group
            ).exists():
                recipe = form.save(commit=False)
                recipe.group = group
                recipe.added_by = request.user
                recipe.save()
                return HttpResponseRedirect(
                    reverse("recipe-detail", args=[recipe.name.replace(" ", "-")])
                )
            else:
                messages.error(request, f"The recipe {recipe_name} already exists!")
    return HttpResponseRedirect(reverse("recipes"))


@group_required
def recipe_delete(request, group, pk):
    """Deletes the recipe with id 'pk' and returns the user to the recipe list view."""
    if request.method == "POST":
        try:
            recipe = Recipe.objects.get(pk=pk, group=group)
            if recipe.name != "Auto":
                recipe.delete()
        except Recipe.DoesNotExist:
            logger.error(f"Remove recipe called for id {pk} which cannot be found.")
    return HttpResponseRedirect(reverse("recipes"))


@group_required
def recipe_to_shopping_list(request, group, pk):
    if request.method == "POST":
        try:
            recipe = Recipe.objects.get(pk=pk, group=group)

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


@group_required
def remove_from_recipe(request, group, pk=None, on_shopping_list=False):
    if request.method == "POST":
        if pk:
            recipe = Recipe.objects.get(pk=pk, group=group)
        else:
            recipe = None

        for key in filter(lambda x: "ingredient-id" in x, request.POST.keys()):
            if request.POST[key] == "delete":
                ingredient_pk = re.search(r"ingredient-id-(\d+)", key).group(1)
                try:
                    ingredient = Ingredient.objects.get(pk=ingredient_pk)
                    name = ingredient.product.name
                    if recipe:
                        base_set = (
                            recipe.ingredient_set
                        )  # Only delete ingredients from this recipe
                    else:
                        base_set = Ingredient.objects.filter(
                            product__group=group
                        )  # No recipe -> Delete from all recipes (dangerous!)
                    for same_named_ingredient in base_set.filter(
                        on_shopping_list=on_shopping_list, product__name__iexact=name
                    ):
                        same_named_ingredient.delete()
                except Ingredient.DoesNotExist:
                    pass  # We don't care, because we were going to delete it anyway
    return HttpResponseRedirect(request.POST["next"])


class UserRecipeListView(LoginRequiredMixin, ListView):
    model = Recipe
    paginate_by = 100
    template_name = "shopping_list/recipe_list.html"

    def get_queryset(self):
        return Recipe.objects.filter(added_by=self.request.user)
