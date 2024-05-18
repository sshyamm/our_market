from django import forms
from .models import *

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
                        raise forms.ValidationError("Only one base offer (either 'TotalAmount' or 'LocationBased') can be selected.")
                    other_offer_selected = True
        
        order = self.instance  # Get the order instance
        
        if order:
            calculated_total_amount = order.calculate_total_amount() or 0  # Get calculated total amount or assume as 0 if not found
            
            for offer in selected_offers:
                if offer.offer_type == 'TotalAmount':
                    min_order_amount_decimal = offer.min_order_amount.to_decimal()  # Convert Decimal128 to Decimal
                    if calculated_total_amount < min_order_amount_decimal:
                        raise forms.ValidationError(f"The offer '{offer}' is not eligible because the order's total amount is less than the minimum order amount required for this offer.")
                elif offer.offer_type == 'LocationBased':
                    # Fetch necessary data for validation
                    order_shipping_address = ShippingAddress.objects.filter(order=order).first()
                    if not order_shipping_address:
                        raise forms.ValidationError("Order does not have a shipping address.")
                    
                    order_country = order_shipping_address.country
                    order_state = order_shipping_address.state.lower()
                    
                    if order_country != offer.country or order_state != offer.state.lower():
                        raise forms.ValidationError(f"The offer '{offer}' is not eligible because the order's shipping address does not match the offer's location criteria.")
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
        fields = '__all__'

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
            if cleaned_data.get('country') or cleaned_data.get('state') or max_discount_percentage or cleaned_data.get('num_orders'):
                self.add_error('country', 'This field is not applicable for TotalAmount offers.')
                self.add_error('state', 'This field is not applicable for TotalAmount offers.')
                self.add_error('max_discount_percentage', 'This field is not applicable for TotalAmount offers.')
                self.add_error('num_orders', 'This field is not applicable for TotalAmount offers.')
        elif offer_type == 'LocationBased':
            if cleaned_data.get('min_order_amount') or max_discount_percentage or cleaned_data.get('num_orders'):
                self.add_error('min_order_amount', 'This field is not applicable for LocationBased offers.')
                self.add_error('max_discount_percentage', 'This field is not applicable for TotalAmount offers.')
                self.add_error('num_orders', 'This field is not applicable for TotalAmount offers.')
        elif offer_type == 'UserBased':
            if cleaned_data.get('country') or cleaned_data.get('state') or cleaned_data.get('min_order_amount'):
                self.add_error('country', 'This field is not applicable for UserBased offers.')
                self.add_error('state', 'This field is not applicable for UserBased offers.')
                self.add_error('min_order_amount', 'This field is not applicable for UserBased offers.')

        if discount_percentage is not None and max_discount_percentage is not None:
            if discount_percentage > max_discount_percentage:
                self.add_error('discount_percentage', 'Discount percentage cannot be greater than the maximum discount percentage.')

        return cleaned_data