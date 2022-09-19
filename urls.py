from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'groups', views.GroupViewSet, basename="group")
router.register(r'categories', views.CategoryViewSet, basename="category")
router.register(r'ingredients', views.IngredientViewSet, basename="ingredient")
router.register(r'products', views.ProductViewSet, basename="product")
router.register(r'recipes', views.RecipeViewSet, basename="recipe")

urlpatterns = [
    path("", include(router.urls)),
]

