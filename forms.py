import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout, Submit
from django import forms
from django.urls import reverse
from django_select2 import forms as s2forms

from .models import Category, Ingredient, Product, Recipe
from .util import get_shopping_list_group

logger = logging.getLogger(__name__)


class SingleTagWidget(
    s2forms.Select2Mixin, s2forms.Select2TagMixin, s2forms.forms.Select
):
    queryset = None
    group = None
    search_fields = [
        "name__icontains",
    ]

    def get_queryset(self):
        return self.queryset

    def value_from_datadict(self, data, files, name):
        """Create objects for given non-pimary-key values.

        Return list of all primary keys.
        """

        value = super().value_from_datadict(data, files, name)
        # Return value is either a number (matched to PK), or a string (direct user input)
        try:
            pk = int(value)
            if self.get_queryset().filter(pk=pk, group=self.group).count():
                return value
        except ValueError:
            if self.get_queryset().filter(name__iexact=value, group=self.group).count():
                pk = self.get_queryset().get(name__iexact=value, group=self.group).pk
            else:
                pk = self.create_and_get_instance(value).pk
            return pk

    def create_and_get_instance(self, value):
        return self.queryset.create(name=value)


def targeted_product_tag_widget(group):
    class ProductTagWidget(SingleTagWidget):
        group = group
        queryset = Product.objects.filter(group=group)

        def create_and_get_instance(self, value):
            product = Product(name=value, group=self.group, pluralised_name=value)
            product.save()
            return product

    return ProductTagWidget


def targeted_category_tag_widget(group):
    class CategoryTagWidget(SingleTagWidget):
        group = group
        queryset = Category.objects.filter(group=group)

        def create_and_get_instance(self, value):
            category = Category(name=value, group=group)
            category.save()
            return category

    return CategoryTagWidget


def product_form_builder(user):
    group = get_shopping_list_group(user)

    class ProductForm(forms.ModelForm):
        """Product creation form."""

        category = forms.ModelChoiceField(
            queryset=Category.objects.filter(group=group),
            widget=targeted_category_tag_widget(group),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["pluralised_name"].label = "Plural Product Name (if different)"
            self.fields["category"].required = True
            self.helper = FormHelper()
            self.helper.form_class = "row row-cols-lg-4"
            self.helper.label_class = "col"
            self.helper.field_class = "col"
            self.helper.field_template = "bootstrap5/layout/inline_field.html"
            self.helper.form_method = "post"
            self.helper.form_action = reverse("product-create")
            self.helper.layout = Layout(
                Field("name", css_class="col", autocomplete="off"),
                Field("category", css_class="col", autocomplete="off"),
                Field("pluralised_name", css_class="col", autocomplete="off"),
                ButtonHolder(Submit("submit", "Create"), css_class="col"),
            )

        class Meta:
            model = Product
            fields = ["name", "category", "pluralised_name"]
            help_texts = {"category": ""}  # Remove category addition help

    return ProductForm


def shopping_list_ingredient_form_builder(user):
    group = get_shopping_list_group(user)

    class ShoppingListIngredientForm(forms.ModelForm):
        """Ingredient creation form that adds ingredients to the main shopping list."""

        product = forms.ModelChoiceField(
            queryset=Product.objects.filter(group=group),
            widget=targeted_product_tag_widget(group),
        )

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_class = "row row-cols-lg-4"
            self.helper.label_class = "col"
            self.helper.field_class = "col"
            self.helper.field_template = "bootstrap5/layout/inline_field.html"
            self.helper.form_method = "post"
            self.helper.form_action = ""
            self.helper.layout = Layout(
                Field("product", css_class="col"),
                Field("amount", css_class="col", autocomplete="off"),
                ButtonHolder(Submit("submit", "Add to list"), css_class="col"),
            )

        class Meta:
            model = Ingredient
            fields = ["product", "amount"]
            widgets = {
                "amount": forms.TextInput,
            }

    return ShoppingListIngredientForm


class RecipeForm(forms.ModelForm):
    """Recipe creation forms consist of three elements:
    The name of the recipe, which must be confirmed as unique,
    The source containing the method, from which a list of ingredients could be populated in future,
    And the list of ingredients itself.

    Submitting this form creates the Recipe and all the Ingredients listed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "row row-cols-lg-4"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("recipe-create")
        self.helper.field_template = "bootstrap5/layout/inline_field.html"
        self.helper.add_input(Submit("create", "Create"))

    class Meta:
        model = Recipe
        fields = [
            "name",
            "source",
        ]
