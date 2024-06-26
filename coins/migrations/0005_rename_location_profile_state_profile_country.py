# Generated by Django 4.1.13 on 2024-06-01 18:04

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('coins', '0004_coin_is_deleted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='location',
            new_name='state',
        ),
        migrations.AddField(
            model_name='profile',
            name='country',
            field=django_countries.fields.CountryField(default=1, max_length=2),
            preserve_default=False,
        ),
    ]
