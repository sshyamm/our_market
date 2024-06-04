from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

class ShippingAddressWebForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['address', 'city', 'state', 'postal_code', 'country', 'phone_no']

class CoinImageForm(forms.ModelForm):
    class Meta:
        model = CoinImage
        fields = ['coin', 'image', 'root_image']

    def __init__(self, *args, **kwargs):
        super(CoinImageForm, self).__init__(*args, **kwargs)
        if 'coin' in self.fields:
            self.fields['coin'].widget.attrs['style'] = 'display: none;'
            self.fields['coin'].label = ''
            self.fields['coin'].widget.can_add_related = False

class CoinWebForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Remove 'user' from kwargs
        super(CoinWebForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['user'].initial = user  # Set initial value for 'user' field
            # Hide the user field
            self.fields['user'].widget.attrs['style'] = 'display: none;'
            # Hide the user field's label
            self.fields['user'].label = ''

    class Meta:
        model = Coin
        fields = ['coin_name', 'coin_desc', 'coin_year', 'coin_country', 'coin_material', 'coin_weight', 'starting_bid', 'rate', 'coin_status', 'featured_coin', 'is_deleted', 'user']

class EditUserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    state = forms.CharField(max_length=100, required=False)
    country = CountryField(blank=True)  # Use blank=True to allow empty values
    phone_no = forms.CharField(max_length=20, required=False)
    website = forms.URLField(max_length=200, required=False)

    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'last_name', 'email', 'bio', 'state', 'country', 'phone_no', 'website']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data['username']
        # Check for other users with the same username
        if User.objects.filter(username=username).count() > 0:
            if self.user.username != username:
                raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        # Check for other users with the same email
        if User.objects.filter(email=email).count() > 0:
            if self.user.email != email:
                raise ValidationError("This email is already taken.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = self.user

        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        
        return profile

class SignUpForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).count() > 0:
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create the Profile instance
            profile = Profile.objects.create()
            profile.user.add(user)
            profile.save()
        return user

class UserValidationMixin:
    def clean_user(self):
        users = self.cleaned_data['user']
        if len(users) > 1:
            raise forms.ValidationError("Only one user can be selected.")
        return users
    
class CoinValidationMixin:
    def clean_coin(self):
        coins = self.cleaned_data['coin']
        if len(coins) > 1:
            raise forms.ValidationError("Only one coin can be selected.")
        return coins
    
class OrderForm(UserValidationMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'

    def clean_shippingaddress(self):
        shipping_addresses = self.cleaned_data['shippingaddress']
        if len(shipping_addresses) > 1:
            raise forms.ValidationError("Only one shipping address can be selected.")
        return shipping_addresses
    
    def clean_offer(self):
        selected_offers = self.cleaned_data['offer']
        user_based_offer_selected = False  # Flag to check if a 'UserBased' offer is selected
        other_offer_selected = False  # Flag to check if a non 'UserBased' offer is selected
        total_amount = self.instance.calculate_total_amount()

        # Check if total amount is zero
        if total_amount == 0 and selected_offers:
            raise forms.ValidationError("No offers can be selected when the total amount is zero.")
        
        if len(selected_offers) > 1:  # Check if more than one offer is selected
            # Loop through the selected offers to check the types of offers selected
            for offer in selected_offers:
                if offer.offer_type == 'UserBased':
                    if user_based_offer_selected:
                        # Raise ValidationError if more than one 'UserBased' offer is selected
                        raise forms.ValidationError("Only one 'UserBased' offer can be selected.")
                    user_based_offer_selected = True
                else:
                    if other_offer_selected:
                        # Raise ValidationError if more than one non 'UserBased' offer is selected
                        raise forms.ValidationError("Only one base offer (either 'TotalAmount') can be selected.")
                    other_offer_selected = True
        
        order = self.instance  # Get the order instance
        
        if order:
            calculated_total_amount = order.calculate_total_amount() or 0  # Get calculated total amount or assume as 0 if not found
            
            for offer in selected_offers:
                if offer.offer_type == 'TotalAmount':
                    min_order_amount_decimal = offer.min_order_amount.to_decimal()  # Convert Decimal128 to Decimal
                    if calculated_total_amount < min_order_amount_decimal:
                        raise forms.ValidationError(f"The offer '{offer}' is not eligible because the order's total amount is less than the minimum order amount required for this offer.")
                elif offer.offer_type == 'UserBased':
                    order_user = order.user.first()
                    if order_user:
                        # Get the most recent order where 'UserBased' offer was applied
                        recent_order_with_user_based_offer = Order.objects.filter(
                            user=order_user,
                            offer__offer_type='UserBased',  # Filter by 'UserBased' offer type
                            order_date__lt=order.order_date
                        ).order_by('-order_date').first()

                        if recent_order_with_user_based_offer:
                            # Count the number of orders since the most recent order with 'UserBased' offer
                            num_previous_orders = Order.objects.filter(
                                user=order_user,
                                order_date__gt=recent_order_with_user_based_offer.order_date,  # Change to greater than
                                order_date__lt=order.order_date
                            ).count()
                        else:
                            # Count all orders placed by the user if no previous order with 'UserBased' offer found
                            num_previous_orders = Order.objects.filter(
                                user=order_user,
                                order_date__lt=order.order_date
                            ).count()

                        if num_previous_orders < offer.num_orders:
                            raise forms.ValidationError(f"The offer '{offer}' is not eligible because the user has not placed enough orders to meet the eligibility criteria.")
                else:
                    raise forms.ValidationError(f"The offer '{offer}' is not a valid offer type.")

                # Check if other offer's discount percentage is greater than the max_discount_percentage of the selected UserBased offer
                if user_based_offer_selected and other_offer_selected:
                    user_based_offer = [o for o in selected_offers if o.offer_type == 'UserBased'][0]
                    if offer.discount_percentage.to_decimal() >= user_based_offer.max_discount_percentage.to_decimal():
                        raise forms.ValidationError(f"The discount percentage of '{offer}' cannot be greater than the maximum discount percentage allowed by the selected UserBased offer '{user_based_offer}'.")
        
        return selected_offers
    
class CoinForm(UserValidationMixin, forms.ModelForm):
    class Meta:
        model = Coin
        fields = '__all__'
    
class ProfileForm(UserValidationMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'
    
class SearchHistoryForm(UserValidationMixin, forms.ModelForm):
    class Meta:
        model = SearchHistory
        fields = '__all__'
    
class CartItemForm(UserValidationMixin, CoinValidationMixin, forms.ModelForm):
    class Meta:
        model = CartItem
        fields = '__all__'
    
class ShippingAddressForm(UserValidationMixin, forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = '__all__'
    
class OrderItemForm(CoinValidationMixin, forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order', 'coin', 'quantity']

    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        if 'order' in self.fields:
            self.fields['order'].widget.attrs['style'] = 'display: none;'
            self.fields['order'].label = ''
            self.fields['order'].widget.can_add_related = False

    def clean_order(self):
        orders = self.cleaned_data['order']
        if len(orders) > 1:
            raise forms.ValidationError("Only one order can be selected.")
        return orders
    
class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add onchange event to offer_type field
        self.fields['offer_type'].widget.attrs['onchange'] = 'toggleFields()'

    def clean(self):
        cleaned_data = super().clean()
        offer_type = cleaned_data.get('offer_type')
        discount_percentage = cleaned_data.get('discount_percentage')
        max_discount_percentage = cleaned_data.get('max_discount_percentage')

        if offer_type == 'TotalAmount':
            if max_discount_percentage or cleaned_data.get('num_orders'):
                self.add_error('max_discount_percentage', 'This field is not applicable for TotalAmount offers.')
                self.add_error('num_orders', 'This field is not applicable for TotalAmount offers.')
        elif offer_type == 'UserBased':
            if cleaned_data.get('min_order_amount'):
                self.add_error('min_order_amount', 'This field is not applicable for UserBased offers.')

        if discount_percentage is not None and max_discount_percentage is not None:
            if discount_percentage > max_discount_percentage:
                self.add_error('discount_percentage', 'Discount percentage cannot be greater than the maximum discount percentage.')

        return cleaned_data