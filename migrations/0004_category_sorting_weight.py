# Generated by Django 4.0.3 on 2022-09-13 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopping_list', '0003_remove_category_sorting_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='sorting_weight',
            field=models.IntegerField(default=0),
        ),
    ]