from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from ..forms import ProductForm
from ..models import Product
from ..util import get_shopping_list_group, group_required, match_name


@group_required
def product_delete(request, group, pk):
    if request.method == "POST":
        try:
            Product.objects.get(pk=pk, group=group).delete()
        except Product.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse("products"))


@group_required
def product_create(request, group):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = Product.objects.get(
                    name__iexact=form.cleaned_data["name"], group=group
                )
                messages.add_message(
                    request, messages.ERROR, f"{product.name} already exists!"
                )
            except Product.DoesNotExist:
                product = form.save(commit=False)
                if not product.pluralised_name:
                    product.pluralised_name = product.name
                product.group = group
                product.save()
    # Whether successful or not, because products are things you make once and then forget,
    # creating them should return to the product list.
    return HttpResponseRedirect(reverse("products"))


@group_required
def product_detail_view(request, group, product_name):
    # Convert name to actual recipe name
    product_name = product_name.replace("-", " ")
    closest_model, good_match = match_name(
        product_name, Product.objects.filter(group=group)
    )

    if good_match:
        if request.method == "POST":
            # Process existing form data
            bound_form = ProductForm(request.POST)

            if bound_form.is_valid():
                for key in ["name", "category", "pluralised_name"]:
                    setattr(closest_model, key, bound_form.cleaned_data[key])
                closest_model.save()
        else:
            # Create default form
            bound_form = ProductForm(
                initial={
                    key: getattr(closest_model, key)
                    for key in ["name", "category", "pluralised_name"]
                }
            )

        recipes = [
            ingredient.recipe
            for ingredient in closest_model.ingredient_set.filter(
                on_shopping_list=False
            )
        ]
        context = {
            "form": bound_form,
            "product": closest_model,
            "copies_on_shopping_list": closest_model.ingredient_set.filter(
                on_shopping_list=True
            ),
            "number_of_recipes": len(recipes),
            "recipes": recipes,
        }

        return render(request, "shopping_list/product_detail.html", context=context)
    else:
        # Return recipe no result view
        error_context = {
            "error": f"No such product {product_name} found.",
            "best_guess_name": closest_model.name,
            "best_guess_slug": closest_model.name.replace(" ", "-").lower(),
        }
        return ProductListView.as_view(extra_context=error_context)(request)


class ProductListView(LoginRequiredMixin, generic.ListView):
    model = Product
    paginate_by = 100
    login_url = reverse("account_login")

    def get_queryset(self):
        return Product.objects.filter(
            group=get_shopping_list_group(self.request.user)
        ).order_by(Lower("category__name"), Lower("name"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProductForm()
        return context
