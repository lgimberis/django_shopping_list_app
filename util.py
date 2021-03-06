from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from fuzzywuzzy import process


def match_name(name, objects):
    matched_objects = objects.filter(name__iexact=name)
    if matched_objects.count():
        return matched_objects[0], True
    else:
        # No matching results - return a list ordered with Levenshtein Distance
        best_name, best_score = process.extractOne(
            name, [trial.name for trial in objects.all()]
        )
        return objects.get(name=best_name), best_score > 90


def get_shopping_list_group(user):
    """Get the 'Shopping List Group' of the user.

    Models can only be seen, modified, and deleted if they belong to the user's group.
    """
    try:
        return user.groups.get(name__icontains="shopping_list_family")
    except Group.DoesNotExist:
        return None


def group_required(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            group = get_shopping_list_group(request.user)
            if group:
                return function(request, group, *args, **kwargs)
            else:
                messages.error(
                    request,
                    "To access the shopping list app, you must either create or join a group.",
                )
                return HttpResponseRedirect(reverse("manage"))
        else:
            messages.error(
                request,
                "To access the shopping list app, you must be logged in.",
            )
            return HttpResponseRedirect(reverse("account_login"))

    return wrapper

class GroupRequiredMixin(AccessMixin):
    """Verify that the current user is in a group."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(
                request,
                "To access the shopping list app, you must be logged in.",
            )
            return HttpResponseRedirect(reverse("account_login"))
        group = get_shopping_list_group(request.user)
        if not group:
            messages.error(
                request,
                "To access the shopping list app, you must either create or join a group.",
            )
            return HttpResponseRedirect(reverse("manage"))
        return super().dispatch(request, *args, **kwargs)