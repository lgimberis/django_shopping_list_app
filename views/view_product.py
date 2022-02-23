from django.shortcuts import render
from django.views import generic
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from ..models import Product
from ..forms import ProductForm
from .view_recipe import *
from ..util import match_name


@login_required
def product_delete(request):
    if request.method == "POST":
        try:
            Product.objects.get(pk=request.POST['product-delete-id']).delete()
        except Product.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse('products'))


@login_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
    # Whether successful or not, because products are things you make once and then forget,
    # creating them should return to the product list.
    return HttpResponseRedirect(reverse('products'))


@login_required
def product_detail_view(request, product_name):
    # Convert name to actual recipe name
    product_name = product_name.replace('-', ' ')
    closest_model, good_match = match_name(product_name, Product.objects)

    if good_match:
        if request.method == 'POST':
            # Process existing form data
            bound_form = ProductForm(request.POST)

            if bound_form.is_valid():
                for key in ["name", "category"]:
                    setattr(closest_model, key, bound_form.cleaned_data[key])
                closest_model.save()
        else:
            # Create default form
            bound_form = ProductForm(initial={key: getattr(closest_model, key) for key in ["name", "category"]})

        context = {
            "form": bound_form,
            "product": closest_model
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


class ProductListView(generic.ListView):
    model = Product
    paginate_by = 100

    def get_queryset(self):
        return Product.objects.all().order_by('category__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductForm()
        return context
