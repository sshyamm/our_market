# Generated by Django 4.1.13 on 2024-05-30 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coins', '0002_alter_cartitem_coin_alter_cartitem_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coin',
            name='featured_coin',
            field=models.CharField(choices=[('yes', 'Yes'), ('no', 'No')], default='no', max_length=3),
        ),
    ]
