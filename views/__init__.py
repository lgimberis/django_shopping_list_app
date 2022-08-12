from django.contrib.auth.models import Group

from rest_framework import viewsets, permissions, renderers
from rest_framework.response import Response
from rest_framework.decorators import api_view, action

from ..serializers import GroupSerializer, CategorySerializer, ProductSerializer, RecipeSerializer, IngredientSerializer, UserSerializer

from ..models import Category, Ingredient, Recipe, Product
from ..util import get_shopping_list_group, generate_group_token, test_group_token


# ViewSets define the view behavior.
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_group(self) -> Group:
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
    def get_shopping_list_group(self, request, *args, **kwargs):
        return self.get_group_response()

    @action(detail=False, methods=['post'])
    def create_shopping_list_group(self, request, *args, **kwargs):
        if self.has_no_group():
            group = Group()
            group.save()
            group.name = f"shopping_group_{group.pk}"
            group.save()
            self.request.user.groups.add(group)
        return self.get_group_response()

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
            return Product.objects.filter(group=get_shopping_list_group(self.request.user))
        else:
            return Product.objects.filter(owner__is_staff=True)

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def exists_by_name(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            queryset = self.get_queryset().filter(name__iexact=request.query_params['name'])
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
        items = self.get_object().ingredient_set.all()
        for item in items:
            item.pk = None
            item.on_shopping_list = True
            print(repr(item))
            item.save()
        return Response({"status": 200})

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

    @action(detail=False, methods=['get'], renderer_classes=[renderers.JSONRenderer])
    def get_checklist_recipe_name(self, request, *args, **kwargs):
        return Response({"name": "auto"})

    @action(detail=False, methods=['post'])
    def add_checklist_to_shopping(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            items = self.get_queryset().get(name__iexact="Auto").ingredient_set.all()
            for item in items:
                item.recipe = None
                item.pk = None
                item.on_shopping_list = True
                item.save()
        return Response(None)

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
