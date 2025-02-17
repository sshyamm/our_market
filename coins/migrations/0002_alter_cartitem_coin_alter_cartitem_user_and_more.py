# Generated by Django 4.1.13 on 2024-05-29 16:17

from django.conf import settings
from django.db import migrations
import django.db.models.deletion
import djongo.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coins', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='coin',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coins.coin'),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='coin',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='coinimage',
            name='coin',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coins.coin'),
        ),
        migrations.AlterField(
            model_name='order',
            name='offer',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coins.offer'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='coin',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coins.coin'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='searchhistory',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='shippingaddress',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
