
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import Category, Product, Recipe, Ingredient


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ['url', 'id', 'name', 'group']


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Product
        fields = ['url', 'id', 'name', 'category', 'pluralised_name', 'group']


class RecipeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='added_by.username')

    class Meta:
        model = Recipe
        fields = ['url', 'id', 'name', 'owner', 'source', 'group']


class IngredientSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='added_by.username')
    name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = Ingredient
        fields = ['url', 'id', 'product', 'name', 'recipe', 'owner', 'on_shopping_list', 'amount']
