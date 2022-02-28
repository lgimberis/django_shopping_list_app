from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
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
        group = get_shopping_list_group(request.user)
        if group:
            return login_required(function(request, group, *args, **kwargs))
        else:
            messages.error(
                request,
                "To access the shopping list app, you must either create or join a group.",
            )
            return HttpResponseRedirect(reverse("manage"))

    return wrapper
