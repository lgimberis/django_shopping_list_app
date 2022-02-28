import base64
from os import urandom

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from ..util import get_shopping_list_group

SECONDS_IN_DAY = 86400


def encrypt(pk: int) -> None:
    """Generate a random invitation link and put it in our cache."""
    random_bytes = urandom(32)
    key = base64.urlsafe_b64encode(random_bytes)
    key = f"group-{pk}-{key.decode('utf-8')}"
    cache.set(key, pk, SECONDS_IN_DAY)
    return key


def decrypt(key: str) -> int:
    return cache.get(key)


class InviteEntryForm(forms.Form):
    link = forms.CharField(label="Invite key")


@login_required
def manage(request):
    """Allow the user to manage their group."""
    group = get_shopping_list_group(request.user)
    context = {"group": group}
    if group:
        # User is in a group.
        # Generate an invite link for the group
        invite_link = encrypt(group.pk)
        context["invite_link"] = invite_link
        # Show a list of group members
        members = group.user_set.all()
        context["members"] = members
        # Functionality to leave or delete group implemented in template
    else:
        # User is not in a group.
        # Allow to join or create a group.
        invite_form = InviteEntryForm()
        context["invite_form"] = invite_form
    return render(request, "shopping_list/manage.html", context=context)


@login_required
def manage_join(request):
    """Attempt to join a group."""
    if request.method == "POST":
        form = InviteEntryForm(request.POST)
        if form.is_valid():
            uuid = form.cleaned_data["link"]
            new_group = decrypt(uuid)
            if new_group:
                group = get_shopping_list_group(request.user)
                if group:
                    # If user is already in a group
                    if group == new_group:
                        messages.error(request, "You are already in this group")
                    else:
                        messages.error(
                            request,
                            "You are already in a group, leave before joining another",
                        )
                else:
                    # User is not in a group, and should join this group
                    request.user.groups.add(group)
                    messages.info(request, "Successfully joined group! Welcome")
            else:
                # User followed a bad link
                messages.error(request, "Invalid or expired invite link")
    return HttpResponseRedirect(reverse("manage"))


@login_required
def manage_create(request):
    """Create a group."""
    group = get_shopping_list_group(request.user)
    if group:
        messages.error(
            request, "You are already in a group, leave before creating another"
        )
    else:
        new_group = Group(name="shopping_list_family")
        new_group.name = f"{new_group.name}_{new_group.pk}"
        request.user.groups.add(new_group)
        messages.info(
            request,
            "Group successfully created! You may now use the shopping list app.",
        )
    return HttpResponseRedirect(reverse("manage"))


@login_required
def manage_leave(request):
    """Leave a group. TODO reassign 'owner' to a remaining user."""
    group = get_shopping_list_group(request.user)
    if group:
        request.user.groups.remove(group)
    return HttpResponseRedirect(reverse("manage"))


@login_required
def manage_delete(request):
    """Delete a group. TODO restrict to group owner."""
    group = get_shopping_list_group(request.user)
    if group:
        group.delete()
    return HttpResponseRedirect(reverse("manage"))
