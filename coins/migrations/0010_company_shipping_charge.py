# Generated by Django 4.1.13 on 2024-06-04 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coins', '0009_delete_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='shipping_charge',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
