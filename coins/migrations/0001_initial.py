# Generated by Django 4.1.13 on 2024-05-28 17:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import djongo.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coin_name', models.CharField(blank=True, max_length=100, null=True)),
                ('coin_desc', models.TextField(blank=True, null=True)),
                ('coin_year', models.IntegerField(blank=True, null=True)),
                ('coin_country', models.CharField(blank=True, max_length=50, null=True)),
                ('coin_material', models.CharField(blank=True, max_length=50, null=True)),
                ('coin_weight', models.FloatField(blank=True, null=True)),
                ('starting_bid', models.FloatField(blank=True, null=True)),
                ('rate', models.FloatField(blank=True, null=True)),
                ('coin_status', models.CharField(blank=True, choices=[('Select', 'Select'), ('available', 'Available'), ('sold', 'Sold'), ('pending', 'Pending')], max_length=50, null=True)),
                ('user', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=100)),
                ('postal_code', models.CharField(max_length=20)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('email', models.EmailField(max_length=255)),
                ('contact_no', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('offer_type', models.CharField(choices=[('TotalAmount', 'Total Amount Based'), ('LocationBased', 'Location Based'), ('UserBased', 'User Based')], max_length=20)),
                ('min_order_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('discount_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('max_discount_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('num_orders', models.IntegerField(blank=True, null=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('state', models.CharField(blank=True, max_length=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_no', models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True)),
                ('order_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Pending', max_length=20, null=True)),
                ('offer', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='coins.offer')),
            ],
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('phone_no', models.CharField(blank=True, max_length=20, null=True)),
                ('user', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('search_text', models.CharField(blank=True, max_length=255, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('user', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True, max_length=500, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('phone_no', models.CharField(blank=True, max_length=20, null=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('user', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(blank=True, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=10, null=True)),
                ('coin', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='coins.coin')),
                ('order', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='coins.order')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='shippingaddress',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='coins.shippingaddress'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='CoinImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to='coin_images/')),
                ('root_image', models.CharField(choices=[('yes', 'Yes'), ('no', 'No')], default='no', max_length=3)),
                ('coin', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='coins.coin')),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(blank=True, default=1, null=True)),
                ('price', models.FloatField(blank=True, editable=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('coin', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='coins.coin')),
                ('user', djongo.models.fields.ArrayReferenceField(blank=True, null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
