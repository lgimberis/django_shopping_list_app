from django.urls import path, include

from rest_framework import routers

from . import views

"""
from .views.view_manage import (
    manage,
    manage_create,
    manage_delete,
    manage_join,
    manage_leave,
)
from .views.view_product import (
    ProductListView,
    product_create,
    product_delete,
    product_detail_view,
)
from .views.view_recipe import (
    RecipeListView,
    auto_shopping,
    recipe_create,
    recipe_delete,
    recipe_detail_view,
    recipe_to_shopping_list,
    remove_from_recipe,
)"""

router = routers.DefaultRouter()
router.register(r'groups', views.GroupViewSet, basename="group")
router.register(r'categories', views.CategoryViewSet, basename="category")
router.register(r'ingredients', views.IngredientViewSet, basename="ingredient")
router.register(r'products', views.ProductViewSet, basename="product")
router.register(r'recipes', views.RecipeViewSet, basename="recipe")

urlpatterns = [
    path("", include(router.urls)),
]

"""
    path("", views.index, name="shopping-index"),
    path("index-refill", views.index_refill, name="shopping-index-refill"),
    path("recipes/", RecipeListView.as_view(), name="recipes"),
    path("recipes/<str:recipe_name>", recipe_detail_view, name="recipe-detail"),
    path("recipe-delete/<int:pk>", recipe_delete, name="recipe-delete"),
    path("recipe-remove/<int:pk>", remove_from_recipe, name="recipe-remove"),
    path(
        "recipe-to-shopping-list/<int:pk>",
        recipe_to_shopping_list,
        name="recipe-to-shopping-list",
    ),
    path("recipe-create", recipe_create, name="recipe-create"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/<str:product_name>", product_detail_view, name="product-detail"),
    path("product-create", product_create, name="product-create"),
    path("product-delete/<int:pk>", product_delete, name="product-delete"),
    path("users/", views.users, name="users"),
    path("automatic-shopping/", auto_shopping, name="auto"),
    path(
        "remove-from-shopping-list/",
        views.remove_from_shopping_list,
        name="remove-from-shopping-list",
    ),
    path("manage/", manage, name="manage"),
    path("manage/create", manage_create, name="manage-create"),
    path("manage/delete", manage_delete, name="manage-delete"),
    path("manage/join", manage_join, name="manage-join"),
    path("manage/leave", manage_leave, name="manage-leave"),"""

