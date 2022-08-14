import base64
from os import urandom
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.auth.mixins import AccessMixin
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.urls import reverse
from fuzzywuzzy import process


SECONDS_IN_DAY = 86400


def update_shopping_hash(user: User):
    group = get_shopping_list_group(user)
    hash_key = f"md5-shopping-{group.pk}"
    if hash := cache.get(hash_key):
        new_hash = hash + 1 if hash < 1E+9 else 1
    else:
        new_hash = 1
    cache.set(hash_key, new_hash, SECONDS_IN_DAY)
    return new_hash

def read_shopping_hash(user: User):
    """Read the MD5 hash of the current shopping list state."""

    group = get_shopping_list_group(user)
    if hash := cache.get(f"md5-shopping-{group.pk}"):
        return hash
    # If there is no MD5 hash in storage, generate one
    return update_shopping_hash(user)


def generate_group_token(group: Group) -> str:
    """Generate a random invitation link and put it in our cache."""

    pk = group.pk
    random_bytes = urandom(32)
    key = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    full_key = f"{pk}-{key}"
    cache.set(full_key, pk, SECONDS_IN_DAY)
    return full_key


def test_group_token(key: str) -> Group:
    """If the given key is in our cache, return the group it corresponds to."""
    if pk := cache.get(key):
        return Group.objects.get(pk=pk)

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
        return user.groups.get(name__icontains="shopping_group")
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