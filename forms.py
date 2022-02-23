from django import forms
from .models import Product, Category, Ingredient, Recipe
from django.core.exceptions import ValidationError
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, ButtonHolder
from django_select2 import forms as s2forms

import logging

logger = logging.getLogger(__name__)


class SingleTagWidget(s2forms.Select2Mixin, s2forms.Select2TagMixin, s2forms.forms.Select):
    queryset = None
    search_fields = [
        'name__icontains',
    ]

    def value_from_datadict(self, data, files, name):
        """Create objects for given non-pimary-key values. Return list of all primary keys.
        """

        cleaned_items = []
        value = super().value_from_datadict(data, files, name)
        # Values are either a number for a matched ID, or a string of user input.
        try:
            pk = int(value)
            return value
            #cleaned_items.append(value)
        except ValueError:
            if self.queryset.filter(name__iexact=value).count():
                pk = self.queryset.get(name__iexact=value).pk
            else:
                pk = self.queryset.create(name=value).pk
            #cleaned_items.append(pk)
            return pk


class ProductTagWidget(SingleTagWidget):
    queryset = Product.objects.all()


class CategoryTagWidget(SingleTagWidget):
    queryset = Category.objects.all()


class ProductForm(forms.ModelForm):
    """Product creation form.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pluralised_name'].label = "Plural Product Name (if different)"
        self.helper = FormHelper()
        self.helper.form_class = 'row row-cols-lg-4'
        self.helper.label_class = 'col'
        self.helper.field_class = 'col'
        self.helper.field_template = 'bootstrap5/layout/inline_field.html'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('product-create')
        self.helper.layout = Layout(
            Field('name', css_class="col", autocomplete="off"),
            Field('category', css_class="col", autocomplete="off"),
            Field('pluralised_name', css_class="col", autocomplete="off"),
            ButtonHolder(Submit('submit', 'Create'), css_class="col"),
        )

    class Meta:
        model = Product
        fields = ['name', 'category', 'pluralised_name']
        widgets = {
            'category': SingleTagWidget,
        }
        help_texts = {'category': ''}  # Remove category addition help


class ShoppingListIngredientForm(forms.ModelForm):
    """Ingredient creation form that adds ingredients to the main shopping list.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'row row-cols-lg-4'
        self.helper.label_class = 'col'
        self.helper.field_class = 'col'
        self.helper.field_template = 'bootstrap5/layout/inline_field.html'
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.layout = Layout(
            Field('product', css_class="col"),
            Field('amount', css_class="col", autocomplete="off"),
            ButtonHolder(Submit('submit', 'Add to list'), css_class="col"),
        )

    class Meta:
        model = Ingredient
        fields = ['product', 'amount']
        widgets = {
            'product': ProductTagWidget,
            'amount': forms.TextInput,
        }


class RecipeForm(forms.ModelForm):
    """Recipe creation forms consist of three elements:
    The name of the recipe, which must be confirmed as unique,
    The source containing the method, from which a list of ingredients could be populated in future,
    And the list of ingredients itself.

    Submitting this form creates the Recipe and all the Ingredients listed."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'row row-cols-lg-4'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('recipe-create')
        self.helper.field_template = 'bootstrap5/layout/inline_field.html'
        self.helper.add_input(Submit('create', 'Create'))

    class Meta:
        model = Recipe
        fields = ['name', 'source', ]
