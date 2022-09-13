from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category

def assign_order(sender, instance, created, **kwargs):
    if created:
        instance.sorting_weight = Category.objects.filter(group=instance.group).order_by('-sorting_weight')[0].sorting_weight + 1
        instance.save()
