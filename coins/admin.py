from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import *
from decimal import Decimal
from coins.forms import *

def display_username(obj):
    if obj.user:
        first_user = obj.user.first()
        if first_user:
            return first_user.username
    return "None"

def display_coin(obj):
    if obj:
        return str(obj)
    else:
        return "None"

def display_coin_image(obj):
    if obj.coin_image:
        return format_html('<img src="{}" style="max-width:100px; max-height:100px;">'.format(obj.coin_image.url))
    else:
        return "Null"

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = ('coin_name', 'display_coin_image', 'coin_desc', 'coin_year', 'coin_country', 'coin_material', 'coin_weight', 'rate', 'starting_bid', 'coin_status', display_username)
    form = CoinForm

    def display_coin_image(self, obj):
        return display_coin_image(obj)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (display_username, 'bio', 'location', 'phone_no', 'website')
    form = ProfileForm

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = (display_username, 'search_text', 'timestamp')
    form = SearchHistoryForm

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (display_username, 'display_coin', 'quantity', 'price', 'created_at')
    form = CartItemForm

    def display_coin(self, obj):
        return display_coin(obj)

    display_coin.short_description = 'Coin'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', display_username, 'order_date', 'get_shipping_address', 'status', 'get_offer', 'view_order_items', 'total_amount')
    form = OrderForm

    def get_shipping_address(self, obj):
        shipping_address = obj.shippingaddress.first()
        if shipping_address:
            return f"{shipping_address.address}, {shipping_address.city}, {shipping_address.state}, {shipping_address.postal_code}"
        return "None"
    
    def get_offer(self, obj):
        offers = obj.offer.all()  # Changed from .first() to .all()
        if offers:
            return ", ".join([offer.name for offer in offers])
        return "None"
    
    get_shipping_address.short_description = 'Shipping Address'

    def view_order_items(self, obj):
        return format_html('<a href="{}">View Order Items</a>', reverse('admin:%s_%s_changelist' % (OrderItem._meta.app_label, OrderItem._meta.model_name)) + f"?order__id__exact={obj.id}")

    view_order_items.short_description = 'Order Items'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if request.method == 'GET':
            order_items_url = reverse('admin:%s_%s_changelist' % (OrderItem._meta.app_label, OrderItem._meta.model_name))
            extra_context['order_items_url'] = f"{order_items_url}?order__id__exact={object_id}"
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    def total_amount(self, obj):
        return obj.calculate_discounted_total_amount()

    total_amount.short_description = 'Total Amount'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('get_invoice_no', 'display_coin', 'quantity', 'price')
    form = OrderItemForm

    def get_invoice_no(self, obj):
        order = obj.order.first()
        if order:
            return order.invoice_no
        return "None"

    def display_coin(self, obj):
        return display_coin(obj)

    display_coin.short_description = 'Coin'
    get_invoice_no.short_description = 'Invoice No'

    def has_module_permission(self, request):
        return False

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = (display_username, 'phone_no', 'address', 'state', 'city', 'postal_code', 'country')
    form = ShippingAddressForm

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'state', 'postal_code', 'country', 'email', 'contact_no')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_order_amount', 'discount_percentage')
    form = OfferForm
