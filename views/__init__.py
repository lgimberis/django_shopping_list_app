from copy import deepcopy
import itertools
import logging
import re

from django.db.models.functions import Lower
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.views import generic
from django.urls import reverse

from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory, BaseInlineFormSet

from ..models import Recipe, Ingredient, Category

from .view_recipe import *
from .view_product import *
from ..util import add_ingredient_from_form, group_required

logger = logging.getLogger(__name__)


@login_required
def manage(request):
    """Allow the user to manage their group.
    
    """
    # If in a group,
    # Show the button to invite others
    # Show a button for leaving the group
    # Show a button for destroying/deleting the group

    # If not in a group,
    # Show the button to create a group
    # Show the button to create a temporary group from an example
    # Show an input to join a group
    return HttpResponse("")


@group_required
def index(request, group):
    """Show the current shopping list. Allow adding items or removing items.
    Also provide links to creating alternative lists."""

    form = add_ingredient_from_form(request, on_shopping_list=True, recipe=None)
    context = {
        "ingredient_list": Ingredient.objects.filter(on_shopping_list=True, product__group=group).order_by(Lower('product__category__name'), Lower('product__name')),
        "form": form,
        "remove_item_url": reverse('remove-from-shopping-list'),
    }
    return render(request, "shopping_list/index.html", context=context)


@group_required
def index_refill(request, group):
    auto = Recipe.objects.filter(name__iexact="Auto", group=group)
    if auto.count() > 0:
        auto_recipe = auto[0]
        for ingredient in Ingredient.objects.filter(recipe=auto_recipe, product__group=group):
            new_ingredient = deepcopy(ingredient)
            new_ingredient.id = None
            new_ingredient.recipe = None
            new_ingredient.on_shopping_list = True
            new_ingredient.save()
    return HttpResponseRedirect(reverse('shopping-index'))


@group_required
def remove_from_shopping_list(request, group):
    if request.method == "POST":
        for key in filter(lambda x: "ingredient-id" in x, request.POST.keys()):
            if request.POST[key] == "delete":
                pk = re.search(r"ingredient-id-(\d+)", key).group(1)
                try:
                    ingredient = Ingredient.objects.get(pk=pk)
                    name = ingredient.product.name
                    for same_named_ingredient in Ingredient.objects.filter(on_shopping_list=True, product__name__iexact=name, product__group=group):
                        same_named_ingredient.delete()
                except Ingredient.DoesNotExist:
                    pass  # We don't care, because we were going to delete it anyway
    return HttpResponseRedirect(request.POST['next'])


class CategoryCreate(generic.CreateView):
    model = Category
    fields = ['name']


class CategoryUpdate(generic.UpdateView):
    model = Category
    fields = '__all__'


class CategoryDelete(generic.UpdateView):
    model = Category


def users(request):
    """Allows a look at different users with access.
    """
    return HttpResponse("")
