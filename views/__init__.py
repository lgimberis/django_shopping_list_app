import logging
import re
from copy import deepcopy

from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from rest_framework import viewsets, permissions, renderers
from rest_framework.response import Response
from rest_framework.decorators import api_view, action

from ..serializers import GroupSerializer, CategorySerializer, ProductSerializer, RecipeSerializer, IngredientSerializer

from ..models import Category, Ingredient, Recipe, Product
from ..util import group_required, get_shopping_list_group
from .view_recipe import add_ingredient_from_form

logger = logging.getLogger(__name__)


# ViewSets define the view behavior.
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return self.request.user.groups.all()


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Category.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            return Category.objects.filter(owner__is_staff=True)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Product.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            return Product.objects.filter(owner__is_staff=True)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            response = { "exists": queryset.count() == 1 }
            if response["exists"]:
                response["url"] = ProductSerializer(queryset.all()[0], context={'request': request}).data['url']
            return Response(response)

    def perform_create(self, serializer):
        serializer.save(group=get_shopping_list_group(self.request.user))


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipe.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            return Recipe.objects.filter(owner__is_staff=True)

    @action(detail=True, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_recipe_items(self, request, *args, **kwargs):
        try:
            on_shopping_list = request.query_params['on_shopping_list'] == 'true'  # Ugh ... JS uses a lowercase 'true'.
        except KeyError:
            on_shopping_list = False

        items = self.get_object().ingredient_set.filter(on_shopping_list=on_shopping_list)
        return Response(IngredientSerializer(items, many=True, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def add_to_shopping(self, request, *args, **kwargs):
        items = self.get_object().ingredient_set.all()
        for item in items:
            item.pk = None
            item.on_shopping_list = True
            print(repr(item))
            item.save()
        return Response({"status": 200})

    @action(detail=True, methods=['get'], renderer_classes=[renderers.StaticHTMLRenderer])
    def get_recipe_items_in_shopping(self, request, *args, **kwargs):
        items = self.get_object().ingredient_set.filter(on_shopping_list=True)
        return Response(items)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            response = { "exists": queryset.count() == 1 }
            return Response(response)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            response = { "exists": queryset.count() == 1 }
            if response["exists"]:
                recipe_data = RecipeSerializer(queryset.all()[0], context={'request': request}).data
                response["recipe"] = recipe_data

            return Response(response)

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user, group=get_shopping_list_group(self.request.user))

class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Ingredient.objects.filter(product__group=get_shopping_list_group(self.request.user))
        else:
            return Ingredient.objects.filter(owner__is_staff=True)

    @action(detail=False)
    def get_shopping(self, request, *args, **kwargs):
        items = self.get_queryset().filter(on_shopping_list=True)
        return Response(IngredientSerializer(items, many=True, context={'request': request}).data)

    @action(detail=False)
    def get_recipe_items(self, request, *args, **kwargs):
        group = request.user.groups.get(name__icontains="shopping_list_family")
        if request.query_params['recipe'] != 'shopping':
            recipe = Recipe.objects.get(name__iexact=request.query_params['name'], group=group)
            on_shopping_list = request.query_params['on_shopping_list']
            items = Ingredient.objects.filter(recipe=recipe, on_shopping_list=on_shopping_list)
        else:
            items = Ingredient.objects.filter(on_shopping_list=True)
        return Response(IngredientSerializer(items, many=True, context={'request': request}).data)

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

@group_required
def index(request, group):
    """Show the current shopping list. Allow adding items or removing items.
    Also provide links to creating alternative lists."""

    form = add_ingredient_from_form(request, on_shopping_list=True, recipe=None)
    context = {
        "ingredient_list": Ingredient.objects.filter(
            on_shopping_list=True, product__group=group
        ).order_by(Lower("product__category__name"), Lower("product__name")),
        "form": form,
        "remove_item_url": reverse("remove-from-shopping-list"),
    }
    return render(request, "shopping_list/index.html", context=context)


@group_required
def index_refill(request, group):
    auto = Recipe.objects.filter(name__iexact="Auto", group=group)
    if auto.count() > 0:
        auto_recipe = auto[0]
        for ingredient in Ingredient.objects.filter(
            recipe=auto_recipe, product__group=group
        ):
            new_ingredient = deepcopy(ingredient)
            new_ingredient.id = None
            new_ingredient.recipe = None
            new_ingredient.on_shopping_list = True
            new_ingredient.save()
    return HttpResponseRedirect(reverse("shopping-index"))


@group_required
def remove_from_shopping_list(request, group):
    if request.method == "POST":
        for key in filter(lambda x: "ingredient-id" in x, request.POST.keys()):
            if request.POST[key] == "delete":
                pk = re.search(r"ingredient-id-(\d+)", key).group(1)
                try:
                    ingredient = Ingredient.objects.get(pk=pk)
                    name = ingredient.product.name
                    for same_named_ingredient in Ingredient.objects.filter(
                        on_shopping_list=True,
                        product__name__iexact=name,
                        product__group=group,
                    ):
                        same_named_ingredient.delete()
                except Ingredient.DoesNotExist:
                    pass  # We don't care, because we were going to delete it anyway
    return HttpResponseRedirect(request.POST["next"])


class CategoryCreate(generic.CreateView):
    model = Category
    fields = ["name"]


class CategoryUpdate(generic.UpdateView):
    model = Category
    fields = "__all__"


class CategoryDelete(generic.UpdateView):
    model = Category


def users(request):
    """Allows a look at different users with access."""
    return HttpResponse("")
