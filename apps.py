from django.apps import AppConfig
from django.dispatch import receiver
from django.db.models.signals import post_save

class ShoppingListConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shopping_list"

    def ready(self):
        from . import signals
        from .models import Category

        post_save.connect(signals.assign_order, sender=Category)


