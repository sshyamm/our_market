from djongo import models
from django.contrib.auth.models import User
import uuid
from django.core.exceptions import ValidationError
from decimal import Decimal
from bson.decimal128 import create_decimal128_context
import decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from django.db import transaction

D128_CTX = create_decimal128_context()

class Coin(models.Model):
    # Define choices for coin status
    STATUS_CHOICES = (
        ('Select', 'Select'),  # Placeholder option
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('pending', 'Pending'),
    )

    coin_name = models.CharField(max_length=100, null=True, blank=True)  # Char field for coin name
    coin_desc = models.TextField(null=True, blank=True)  # Text field for coin description
    coin_year = models.IntegerField(null=True, blank=True)  # Integer field for coin year
    coin_country = models.CharField(max_length=50, null=True, blank=True)  # Char field for coin country
    coin_material = models.CharField(max_length=50, null=True, blank=True)  # Char field for coin material
    coin_weight = models.FloatField(null=True, blank=True)  # Float field for coin weight
    starting_bid = models.FloatField(null=True, blank=True)
    rate = models.FloatField(null=True, blank=True)  # Float field for starting bid
    coin_status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)  # Char field with choices for coin status
    user = models.ArrayReferenceField(to=User, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.coin_name  # Return the coin name as its string representation

class CoinImage(models.Model):
    ROOT_IMAGE_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
    )

    coin = models.ArrayReferenceField(to=Coin, null=True, blank=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='coin_images/', null=True, blank=True)
    root_image = models.CharField(max_length=3, choices=ROOT_IMAGE_CHOICES, default='no')

    def __str__(self):
        return f"Coin: {self.coin.first()} on Root: {self.root_image}"
           
@receiver(post_save, sender=Coin)
def update_related_calculations(sender, instance, **kwargs):
    if kwargs.get('created', False):  # Check if a new instance of Coin is created
        return  # If it's a new instance, no need to update calculations
    else:
        # Update calculations related to OrderItem and CartItem
        for order_item in OrderItem.objects.filter(coin=instance):
            order_item.calculate_price()
            order_item.save()
        
        for cart_item in CartItem.objects.filter(coin=instance):
            cart_item.calculate_price()
            cart_item.save()

class Profile(models.Model):
    user = models.ArrayReferenceField(to=User, null=True, blank=True, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True) 
    website = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        if self.user.count() > 0:  # Check if there are any referenced users
            usernames = ', '.join([u.username for u in self.user.all()])
            return f"{usernames}"
        else:
            return "Empty Profile"
        
class SearchHistory(models.Model):
    user = models.ArrayReferenceField(to=User,null=True, blank=True, on_delete=models.CASCADE)
    search_text = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        user_str = ', '.join([str(u) for u in self.user.all()])
        return f"{user_str}"

class CartItem(models.Model):
    user = models.ArrayReferenceField(to=User, null=True, blank=True, on_delete=models.CASCADE)
    coin = models.ArrayReferenceField(to=Coin, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, null=True, blank=True)
    price = models.FloatField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def calculate_price(self):
        if self.coin and self.coin.first():
            coin_rate = self.coin.first().rate
            if coin_rate is not None:
                self.price = self.quantity * coin_rate
            else:
                raise ValueError("Coin rate is not defined.")
        else:
            raise ValueError("Coin is not selected.")
    
    def save(self, *args, **kwargs):
        self.calculate_price()  # Recalculate the price every time the object is saved
        super().save(*args, **kwargs)
    
    def __str__(self):
        coin_str = ', '.join([str(c) for c in self.coin.all()])
        return f"{coin_str}"

class ShippingAddress(models.Model):
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = CountryField()
    phone_no = models.CharField(max_length=20, null=True, blank=True) 
    user = models.ArrayReferenceField(to=User, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}, {self.postal_code}"

class Offer(models.Model):
    OFFER_TYPE_CHOICES = (
        ('TotalAmount', 'Total Amount Based'),
        ('LocationBased', 'Location Based'),
        ('UserBased', 'User Based'),
    )

    name = models.CharField(max_length=100)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    num_orders = models.IntegerField(null=True, blank=True)
    country = CountryField(null=True, blank=True)  # For location-based offers
    state = models.CharField(max_length=20, null=True, blank=True) 
        
    def __str__(self):
        return f"{self.name} ---- {self.discount_percentage}%"

class Order(models.Model):
    # Define choices for order status
    ORDER_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    invoice_no = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    user = models.ArrayReferenceField(to=User, null=True, blank=True, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    shippingaddress = models.ArrayReferenceField(to=ShippingAddress, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending', null=True, blank=True)
    offer = models.ArrayReferenceField(to=Offer, null=True, blank=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            # Generate invoice number
            self.invoice_no = 'INV' + str(uuid.uuid4().hex)[:6].upper()  # Generating a unique invoice number
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_no
    
    def calculate_total_amount(self):
        total_amount = Decimal(0)
        order_items = self.orderitem_set.all()  # Assuming the related name for OrderItem is 'orderitem_set'
        for order_item in order_items:
            # Convert Decimal128 to Decimal
            order_item_price_decimal = Decimal(str(order_item.price))
            total_amount += order_item_price_decimal
        return total_amount
        
    def is_user_based_offer_eligible(self, offer):
        if offer.offer_type != 'UserBased':
            return False
        
        recent_order_with_user_based_offer = Order.objects.filter(
            user=self.user.first(),
            offer__offer_type='UserBased',  # Filter by 'UserBased' offer type
            order_date__lt=self.order_date
        ).order_by('-order_date').first()

        if recent_order_with_user_based_offer:
            num_previous_orders = Order.objects.filter(
                user=self.user.first(),
                order_date__gt=recent_order_with_user_based_offer.order_date,
                order_date__lt=self.order_date
            ).count()
        else:
            num_previous_orders = Order.objects.filter(
                user=self.user.first(),
                order_date__lt=self.order_date
            ).count()

        return num_previous_orders >= offer.num_orders

    def calculate_discounted_total_amount(self):
        total_amount = self.calculate_total_amount()
        discounted_total_amount = total_amount
        
        if self.offer:
            for offer in self.offer.all(): 
                if offer.offer_type == 'TotalAmount': 
                    min_order_amount = offer.min_order_amount
                    min_order_amount_decimal = min_order_amount.to_decimal().quantize(decimal.Decimal('0.01'))
                    if discounted_total_amount >= min_order_amount_decimal:
                        discount_amount = (discounted_total_amount * decimal.Decimal(str(offer.discount_percentage))) / 100
                        discounted_total_amount -= discount_amount  # Apply discount
                elif offer.offer_type == 'LocationBased':
                    # Check if the order's shipping address matches the offer's country and state
                    if self.shippingaddress and self.shippingaddress.first():
                        order_country = self.shippingaddress.first().country
                        order_state = self.shippingaddress.first().state.lower()
                        if order_country == offer.country and order_state == offer.state.lower():
                            discount_amount = (discounted_total_amount * decimal.Decimal(str(offer.discount_percentage))) / 100
                            discounted_total_amount -= discount_amount  # Apply discount
                elif offer.offer_type == 'UserBased':
                    if self.user.first() and self.is_user_based_offer_eligible(offer):
                        other_offer_discount = Decimal(0)
                        for other_offer in self.offer.exclude(id=offer.id):  # Exclude the current UserBased offer
                            other_offer_discount += other_offer.discount_percentage.to_decimal() 

                        combined_discount_percentage = offer.discount_percentage.to_decimal() + other_offer_discount

                        if other_offer_discount > offer.max_discount_percentage.to_decimal():
                            revised_discount_percentage = Decimal(0)
                        elif combined_discount_percentage > offer.max_discount_percentage.to_decimal():
                            revised_discount_percentage = offer.max_discount_percentage.to_decimal() - other_offer_discount
                        else:
                            revised_discount_percentage = offer.discount_percentage.to_decimal()

                        discount_amount = (discounted_total_amount * decimal.Decimal(str(revised_discount_percentage))) / 100
                        discounted_total_amount -= discount_amount  # Apply discount

        return discounted_total_amount.quantize(decimal.Decimal('0.01'))

    def get_revised_user_based_discount_percentage(self):
        revised_discount_percentage = Decimal(0)
        for offer in self.offer.all():
            if offer.offer_type == 'UserBased' and self.is_user_based_offer_eligible(offer):
                other_offer_discount = Decimal(0)
                for other_offer in self.offer.exclude(id=offer.id):
                    other_offer_discount += other_offer.discount_percentage.to_decimal() 

                combined_discount_percentage = offer.discount_percentage.to_decimal()  + other_offer_discount

                if other_offer_discount > offer.max_discount_percentage.to_decimal() :
                    revised_discount_percentage = Decimal(0)
                elif combined_discount_percentage > offer.max_discount_percentage.to_decimal() :
                    revised_discount_percentage = offer.max_discount_percentage.to_decimal() - other_offer_discount
                else:
                    revised_discount_percentage = offer.discount_percentage.to_decimal() 

        return revised_discount_percentage
    
    def is_offer_eligible(self, offer):
        if offer.offer_type == 'TotalAmount':
            min_order_amount_decimal = decimal.Decimal(str(offer.min_order_amount))
            return self.calculate_total_amount() >= min_order_amount_decimal
        elif offer.offer_type == 'LocationBased':
            if self.shippingaddress and self.shippingaddress.first():
                order_country = self.shippingaddress.first().country
                order_state = self.shippingaddress.first().state.lower()
                return order_country == offer.country and order_state == offer.state.lower()
        elif offer.offer_type == 'UserBased':
            return self.is_user_based_offer_eligible(offer)
        return False

@receiver(post_save, sender=Order)
@receiver(post_save, sender=Offer)
def remove_zero_revised_discount_offers(sender, instance, **kwargs):
    if sender == Order:
        # If an Order instance is updated
        if kwargs.get('created', False):  # If it's a new instance, do nothing
            return
        else:
            for offer in instance.offer.all():
                if offer.offer_type == 'UserBased':
                    # Check if the revised discount percentage is 0
                    if instance.get_revised_user_based_discount_percentage() == 0:
                        # Remove the offer from the order
                        instance.offer.remove(offer)
                        # Save the order
                        instance.save()
    
    elif sender == Offer:
        # If an Offer instance is updated, check all related orders
        related_orders = instance.order_set.all()
        for order in related_orders:
            for offer in order.offer.all():
                if offer.offer_type == 'UserBased':
                    # Check if the revised discount percentage is 0
                    if order.get_revised_user_based_discount_percentage() == 0:
                        # Remove the offer from the order
                        order.offer.remove(offer)
                        # Save the order
                        order.save()

@receiver(post_save, sender=Order)
def handle_order_change(sender, instance, **kwargs):
    with transaction.atomic():
        for user in User.objects.all():
            for order in user.order_set.all():
                for offer in order.offer.all():
                    # Check if the offer is eligible
                    if not order.is_offer_eligible(offer):
                        # Remove the offer from the order
                        order.offer.remove(offer)
                        # Save the order
                        order.save() 

@receiver(post_save, sender=Offer)
def handle_offer_change(sender, instance, **kwargs):
    with transaction.atomic():
        for order in Order.objects.all():
            # Check if the offer is in the order's offer array
            if instance in order.offer.all():
                # Check eligibility
                if not order.is_offer_eligible(instance):
                    # Remove the offer from the order
                    order.offer.remove(instance)
                    # Save the order
                    order.save()        

class OrderItem(models.Model):
    order = models.ArrayReferenceField(to=Order, null=True, blank=True, on_delete=models.CASCADE)
    coin = models.ArrayReferenceField(to=Coin, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, editable=False)  # Add price field

    def calculate_price(self):
        if self.coin and self.coin.first():
            coin_rate = self.coin.first().rate
            if coin_rate is not None:
                self.price = Decimal(self.quantity) * Decimal(coin_rate)
            else:
                raise ValueError("Coin rate is not defined.")
        else:
            raise ValueError("Coin is not selected.")

    def save(self, *args, **kwargs):
        self.calculate_price()  # Recalculate the price every time the object is saved
        super().save(*args, **kwargs)

    def __str__(self):
        coin_str = ', '.join([str(c) for c in self.coin.all()])
        return f"{coin_str}"
        
class Company(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = CountryField()
    email = models.EmailField(max_length=255)
    contact_no = models.CharField(max_length=20)

    def __str__(self):
        return self.name