from django.contrib.auth.models import Group

from rest_framework import viewsets, permissions, renderers
from rest_framework.response import Response
from rest_framework.decorators import action

from .serializers import GroupSerializer, CategorySerializer, ProductSerializer, RecipeSerializer, IngredientSerializer, UserSerializer
from .models import Category, Ingredient, Recipe, Product
from .util import (
    get_shopping_list_group, 
    generate_group_token, 
    test_group_token, 
    read_shopping_hash, 
    update_shopping_hash
)


def _get_or_create_checklist(queryset, group):
    try:
        recipe = queryset.get(name__exact="Auto", group=group)
    except Recipe.DoesNotExist:
        # For the first time viewing the checklist we may need to create it
        recipe = Recipe(name="Auto", group=group)
        recipe.save()
    return recipe

# ViewSets define the view behavior.
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_group(self):
        """Get our user's group."""
        if self.request.user.is_authenticated :
            return get_shopping_list_group(self.request.user)

    def has_no_group(self) -> bool:
        """Return whether our user has a group. If not authed, return False."""
        return self.request.user.is_authenticated and not self.get_group()

    def get_group_response(self):
        """To be returned following each group operation."""
        if group := self.get_group():
            response = {'name': group.name, 'users': [UserSerializer(user).data for user in group.user_set.all()]}
            return Response(response)
        return Response({})

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_shopping_list_group(self, request, *args, **kwargs) -> Response:
        return self.get_group_response()

    def __create_group(self):
        if self.has_no_group():
            group = Group()
            group.save()
            group.name = f"shopping_group_{group.pk}"
            group.save()
            self.request.user.groups.add(group)
            return group

    @action(detail=False, methods=['post'])
    def create_shopping_list_group(self, request, *args, **kwargs):
        self.__create_group()
        return self.get_group_response()

    @action(detail=False, methods=['post'])
    def create_shopping_list_group_from_template(self, request, *args, **kwargs):
        if self.has_no_group():
            group = self.__create_group()
            
            # Load data files containing 'Template Group' data
            import json
            from pathlib import Path
            with open(Path(__file__).parent.parent / 'template_group.json') as file:
                template_data = json.load(file)

                # Add categories first
                if "categories" in template_data:
                    for category in template_data["categories"]:
                        _category = Category(name=category, group=group)
                        _category.save()

                # Add products
                if "products" in template_data:
                    for product in template_data["products"]:
                        plural_name = (product["pluralised_name"] 
                                if "pluralised_name" in product else product["name"])
                        if "category" in product:
                            try:
                                category = Category.objects.get(group=group, name__exact=product["category"])
                            except Category.DoesNotExist as e:
                                print(f"Category {product['category']} of product {product['name']} ({product}) does not exist")
                                continue
                        else:
                            category = None
                        _product = Product(name=product["name"], pluralised_name=plural_name, 
                                group=group, category=category)
                        _product.save()

                # Small helper function for ingredient addition
                def _add_ingredient(ingredient, _recipe=None, on_list=False):
                    try:
                        _product = Product.objects.get(group=group, name__exact=ingredient["name"])
                        amount = ingredient["amount"] if "amount" in ingredient else ""
                        _ingredient = Ingredient(product=_product, recipe=_recipe, amount=amount, on_shopping_list=on_list)
                        _ingredient.save()
                    except Product.DoesNotExist:
                        print(f"Product {ingredient['name']} of ingredient {ingredient} does not exist")

                # Add recipes
                if "recipes" in template_data:
                    for recipe in template_data["recipes"]:
                        _recipe = Recipe(name=recipe["name"], source=recipe["source"], group=group)
                        _recipe.save()

                        for ingredient in recipe["ingredients"]:
                            _add_ingredient(ingredient, _recipe)

                # Add checklist
                if "checklist" in template_data:
                    _checklist = _get_or_create_checklist(Recipe.objects.filter(group=group), group)
                    for ingredient in template_data["checklist"]:
                        _add_ingredient(ingredient, _checklist)

                # Add shopping
                if "shopping" in template_data:
                    for ingredient in template_data["shopping"]:
                        _add_ingredient(ingredient, on_list=True)
            
            return self.get_group_response()
        return Response({})

    @action(detail=False, methods=['post'])
    def leave(self, request, *args, **kwargs):
        if group := self.get_group():
            self.request.user.groups.remove(group)
            if group.user_set.count() == 0:
                group.delete()
        return self.get_group_response()

    @action(detail=False, methods=['post'])
    def get_join_code(self, request, *args, **kwargs):
        if group := self.get_group():
            token = generate_group_token(group)
            return Response({'token': token})
        return Response({})

    @action(detail=False, methods=['post'])
    def test_join_code(self, request, *args, **kwargs):
        if self.has_no_group():
            if group := test_group_token(request.data['token']):
                self.request.user.groups.add(group)
        return self.get_group_response()

    def get_queryset(self):
        return self.request.user.groups.all()


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Category.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            # Show anonymous/unauthenticated users a preview using staff data
            return Category.objects.filter(owner__is_staff=True)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            response = { "exists": queryset.count() == 1 }
            if response["exists"]:
                response["data"] = ProductSerializer(queryset.all()[0], context={'request': request}).data
            return Response(response)

    def perform_create(self, serializer):
        serializer.save(group=get_shopping_list_group(self.request.user))

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Product.objects.filter(group=get_shopping_list_group(self.request.user)).order_by('name')
        else:
            return Product.objects.filter(owner__is_staff=True)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            if queryset.count() == 0 and 'pluralised_name' in request.query_params:
                queryset = self.get_queryset().filter(pluralised_name__iexact=request.query_params['pluralised_name'])
            response = { "exists": queryset.count() == 1 }
            if response["exists"]:
                response["data"] = ProductSerializer(queryset.all()[0], context={'request': request}).data
            return Response(response)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_sorted_by_category(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('category')
        return Response(ProductSerializer(queryset.all(), many=True, context={'request': request}).data)

    def perform_create(self, serializer):
        serializer.save(group=get_shopping_list_group(self.request.user))


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def list(self, request):
        queryset = self.get_queryset().exclude(name__exact="Auto")
        serializer = RecipeSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipe.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            return Recipe.objects.filter(added_by__is_staff=True)

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
        items = self.get_object().ingredient_set.filter(on_shopping_list=False)
        for item in items:
            item.pk = None
            item.on_shopping_list = True
            item.save()
        update_shopping_hash(self.request.user)
        return Response({"status": 200})

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            name = request.query_params['name'].strip()
            queryset = self.get_queryset().filter(name__iexact=name)
            response = { "exists": queryset.count() == 1 }
            return Response(response)

    @action(detail=False, methods=['get'])
    def get_checklist(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            group = get_shopping_list_group(self.request.user)
            recipe = _get_or_create_checklist(self.get_queryset(), group)
            recipe_data = RecipeSerializer(recipe, context={'request': request}).data
            return Response({"exists": True, "recipe": recipe_data})

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
            response = { "exists": queryset.count() == 1 }
            if response["exists"]:
                recipe_data = RecipeSerializer(queryset.all()[0], context={'request': request}).data
                response["recipe"] = recipe_data

            return Response(response)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_checklist_recipe_name(self, request, *args, **kwargs):
        return Response({"name": "auto"})

    @action(detail=False, methods=['post'])
    def add_checklist_to_shopping(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            items = self.get_queryset().get(name__iexact="Auto").ingredient_set.filter(on_shopping_list=False)
            for item in items:
                item.recipe = None
                item.pk = None
                item.on_shopping_list = True
                item.save()
            update_shopping_hash(self.request.user)
        return Response(None)

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user, group=get_shopping_list_group(self.request.user))


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def destroy(self, request, pk=None):
        if self.request.user.is_authenticated:
            try:
                ingredient = self.get_queryset().get(pk=pk)
                if ingredient.on_shopping_list:
                    update_shopping_hash(self.request.user)
            except Ingredient.DoesNotExist:
                pass # Don't care
        return super().destroy(request, pk)

    def create(self, request):
        if self.request.user.is_authenticated:
            update_shopping_hash(self.request.user)
        return super().create(request)

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
    def get_shopping_hash(self, request, *args, **kwargs):
        return Response({'hash': read_shopping_hash(self.request.user)})

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
