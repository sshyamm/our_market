# Generated by Django 4.1.13 on 2024-06-02 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coins', '0005_rename_location_profile_state_profile_country'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='offer',
            name='country',
        ),
        migrations.RemoveField(
            model_name='offer',
            name='state',
        ),
        migrations.AlterField(
            model_name='offer',
            name='offer_type',
            field=models.CharField(choices=[('TotalAmount', 'Total Amount Based'), ('UserBased', 'User Based')], max_length=20),
        ),
    ]