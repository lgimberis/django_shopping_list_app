from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', views.index, name='shopping-index'),
    path('index-refill', views.index_refill, name='shopping-index-refill'),
    path('recipes/', views.RecipeListView.as_view(), name='recipes'),  # Overview of recipes
    path('my_recipes/', views.UserRecipeListView.as_view(), name='user-recipes'),  # User's recipes
    path('recipes/<str:recipe_name>', views.recipe_detail_view, name='recipe-detail'),
    path('recipe-delete/<int:pk>', views.recipe_delete, name='recipe-delete'),
    path('recipe-remove/<int:pk>', views.remove_from_recipe, name='recipe-remove'),
    path('recipe-to-shopping-list/<int:pk>', views.recipe_to_shopping_list, name='recipe-to-shopping-list'),
    path('recipe-create', views.recipe_create, name='recipe-create'),
    path('products/', views.ProductListView.as_view(), name='products'),  # Complete list of products
    path('products/<str:product_name>', views.product_detail_view, name='product-detail'),
    path('product-create', views.product_create, name='product-create'),
    path('product-delete/<int:pk>', views.product_delete, name='product-delete'),
    path('users/', views.users, name='users'),  # Complete list of users
    path('automatic-shopping/', views.auto_shopping, name='auto'),  # Complete specification for auto-shopping
    path('remove-from-shopping-list/', views.remove_from_shopping_list, name='remove-from-shopping-list'),
]
