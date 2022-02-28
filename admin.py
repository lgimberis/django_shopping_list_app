from django.contrib import admin

from .models import Category, Ingredient, Product, Rating, Recipe

admin.site.register(Category)
admin.site.register(Rating)


class CategoryInline(admin.TabularInline):
    model = Category


class RecipeInline(admin.TabularInline):
    model = Recipe


class IngredientInline(admin.TabularInline):
    model = Ingredient


class RatingInline(admin.TabularInline):
    model = Rating


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    # We want to be able to add categories or shopping lists from new products
    inlines = [IngredientInline]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline, RatingInline]
    list_display = ("name", "added_by")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "recipe")
    list_filter = ("product", "recipe", "added_by")
    inlines = []
