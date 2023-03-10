from django.contrib.auth.models import Group, User
from django.db import models
from django.urls import reverse


class Category(models.Model):
    """Type of product. Typically related to aisle."""

    name = models.CharField(max_length=80)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    sorting_weight = models.IntegerField(default=0)
    
    def sorting_weight_default():
        pass

    def __str__(self):
        return self.name

class Product(models.Model):
    """Product that can be found in a shop."""

    name = models.CharField(max_length=80, verbose_name="Product Name")
    category = models.ForeignKey(
        Category,
        help_text="This should indicate a type of product",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    pluralised_name = models.CharField(
        max_length=80,
        verbose_name="Pluralised Product Name",
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        slugged_name = self.name.replace(" ", "-").lower()
        return reverse("product-detail", args=[slugged_name])

    class Meta:
        ordering = ["category"]


class Recipe(models.Model):
    """A collection of ingredients."""

    name = models.CharField(max_length=80)
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=200, blank=True, null=True, default="")
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        slugged_name = self.name.replace(" ", "-").lower()
        return reverse("recipe-detail", args=[slugged_name])

    def get_remove_url(self):
        """Returns the relevant url to the view that will remove items from this recipe."""
        return reverse("recipe-remove", args=[self.pk])


class Rating(models.Model):
    """A rating of a recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)


class Ingredient(models.Model):
    """A product with a specific amount, added by a person, related to a recipe."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, blank=True, null=True)
    added_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    added_time = models.DateTimeField(auto_now_add=True)
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
