from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from ..util import get_shopping_list_group

@login_required
def manage(request):
    """Allow the user to manage their group.
    
    """
    group = get_shopping_list_group(request.user)
    context = ["group": group]
    if group:
        members = group.user_set.all()
        context["members"] = members
        # If in a group,
        # Show the button to invite others
    else:
        # If not in a group,
        # Show the button to create a group
        # Show the button to create a temporary group from an example
        # Show an input to join a group
    return HttpResponse("")