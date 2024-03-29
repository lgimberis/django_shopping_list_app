
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import Category, Product, Recipe, Ingredient


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CategorySerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Category
        fields = ['url', 'id', 'name', 'group']


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Product
        fields = ['url', 'id', 'name', 'category', 'pluralised_name', 'group']


class RecipeSerializer(serializers.HyperlinkedModelSerializer):
    added_by = serializers.PrimaryKeyRelatedField(read_only=True)
    group = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Recipe
        fields = ['url', 'id', 'name', 'added_by', 'source', 'group']


class IngredientSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.ReadOnlyField(source='product.name')
    pluralised_name = serializers.ReadOnlyField(source='product.pluralised_name')
    added_by = serializers.PrimaryKeyRelatedField(read_only=True)
    category = serializers.ReadOnlyField(source='product.category.name')

    class Meta:
        model = Ingredient
        fields = ['url', 'id', 'product', 'name', 'pluralised_name', 'recipe', 'category', 'added_by', 'added_time', 'on_shopping_list', 'amount']

