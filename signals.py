from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category

def assign_order(sender, instance, created, **kwargs):
    if created:
        group_categories = Category.objects.filter(group=instance_group)
        if group_categories.count() > 1:
            # Only set this if another category exists. No 'else' block needed - default value 0 is correct.
            instance.sorting_weight = group_categories.order_by('-sorting_weight')[0].sorting_weight + 1
            instance.save()
