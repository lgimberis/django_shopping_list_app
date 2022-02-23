from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):
    """Type of product. Typically related to aisle."""
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product that can be found in a shop."""
    name = models.CharField(max_length=80, verbose_name="Product Name")
    category = models.ForeignKey(Category, help_text="This should indicate a type of product", blank=True, null=True,
                                 on_delete=models.SET_NULL)
    pluralised_name = models.CharField(max_length=80, verbose_name="Pluralised Product Name", blank=True, null=True, default="")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        slugged_name = self.name.replace(" ", "-").lower()
        return reverse('product-detail', args=[slugged_name])

    def copies_on_shopping_list(self):
        return self.ingredient_set.filter(on_shopping_list=True)

    def number_of_relevant_recipes(self):
        return self.ingredient_set.filter(on_shopping_list=False).count()

    def relevant_recipes(self):
        for ingredient in self.ingredient_set.filter(on_shopping_list=False):
            yield ingredient.recipe

    class Meta:
        ordering = ['category']


class Recipe(models.Model):
    """A collection of ingredients.
    """
    name = models.CharField(max_length=80)
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=200, blank=True, null=True, default="")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        slugged_name = self.name.replace(" ", "-").lower()
        return reverse('recipe-detail', args=[slugged_name])

    def get_ingredient_count(self):
        return self.ingredient_set.all().count()

    def get_ingredients_by_category(self):
        """Returns ingredients of this Recipe.
        
        Ignores items on the shopping list, which are copies of the others."""
        products_by_category = {}
        for ingredient in self.ingredient_set.all():
            if not ingredient.on_shopping_list:
                category = ingredient.product.category
                if category in products_by_category:
                    products_by_category[category].append(ingredient)
                else:
                    products_by_category[category] = [ingredient]
        return products_by_category

    def get_ingredient_list(self):
        """Returns ingredients of this Recipe, ordered by category name.
        """
        return self.ingredient_set.filter(on_shopping_list=False).order_by('product__category__name')

    def get_remove_url(self):
        """Returns the relevant url to the view that will remove items from this recipe.
        """
        return reverse("recipe-remove", args=[self.pk])


class Rating(models.Model):
    """A rating of a recipe.
    """
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)


class Ingredient(models.Model):
    """A product with a specific amount, added by a person, related to a recipe.

    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, blank=True, null=True)
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    on_shopping_list = models.BooleanField(default=False)

    amount = models.TextField(max_length=40, default="", blank=True, null=True)

    def name(self):
        return self.product.name

    @property
    def category(self):
        return self.product.category

    def __str__(self):
        amount = f"{self.amount}" if self.amount else ""
        return f"{amount} {self.product.name}".strip()
