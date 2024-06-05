from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import *
from decimal import Decimal
from coins.forms import *
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.templatetags.static import static

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
    if obj.image:
        return format_html('<img src="{}" style="max-width:100px; max-height:100px;">'.format(obj.image.url))
    else:
        return "Null"
        

@admin.register(Coin)
class CoinAdmin(admin.ModelAdmin):
    list_display = (
        'coin_name', 'display_root_image', 'coin_desc', 'coin_year', 'coin_country', 
        'coin_material', 'coin_weight', 'rate', 'starting_bid', 
        'coin_status', display_username, 'featured_coin', 'view_images', 'is_deleted'
    )
    form = CoinForm

    def display_root_image(self, obj):
        # Fetch the root image for the coin
        root_image = CoinImage.objects.filter(coin=obj, root_image='yes').first()
        if root_image and root_image.image:
            return format_html('<img src="{}" style="max-width:100px; max-height:100px;">', root_image.image.url)
        else:
            default_image_url = static('img/default.jpg')
            return format_html('<img src="{}" style="max-width:100px; max-height:100px;" alt="{}">', default_image_url, obj.coin_name)

    display_root_image.short_description = 'Root Image'

    def view_images(self, obj):
        view_url = reverse('admin:coins_coinimage_changelist') + f'?coin__id__exact={obj.id}'
        return format_html('<a href="{}">View Images</a>', view_url)

    view_images.short_description = 'Images'

@admin.register(CoinImage)
class CoinImageAdmin(admin.ModelAdmin):
    form = CoinImageForm
    list_display = ('display_coin', display_coin_image, 'root_image')

    def display_coin(self, obj):
        return display_coin(obj.coin.first())

    display_coin.short_description = 'Coin'

    def add_view(self, request, form_url='', extra_context=None):
        coin_id = request.GET.get('coin_id')
        if coin_id:
            coin = get_object_or_404(Coin, pk=coin_id)
            request.POST = request.POST.copy()
            request.POST['coin'] = coin.id
        return super().add_view(request, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        coin_id = request.GET.get('coin__id__exact')
        if coin_id:
            add_url = reverse('admin:coins_coinimage_add') + f'?coin_id={coin_id}'
            if extra_context is None:
                extra_context = {}
            extra_context['add_url'] = add_url
        return super().changelist_view(request, extra_context=extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        coin_id = obj.coin.first().id
        if "_continue" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse('admin:coins_coinimage_changelist') + f'?coin__id__exact={coin_id}')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'coin' in form.base_fields:
            form.base_fields['coin'].widget.attrs['style'] = 'display:none;'
        return form
    
    def has_module_permission(self, request):
        return False

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (display_username, 'bio', 'state', 'country', 'phone_no', 'website')
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
        view_url = reverse('admin:coins_orderitem_changelist') + f'?order__id__exact={obj.id}'
        return format_html('<a href="{}">View Orders</a>', view_url)
    
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

    def add_view(self, request, form_url='', extra_context=None):
        order_id = request.GET.get('order_id')
        if order_id:
            order = get_object_or_404(Order, pk=order_id)
            request.POST = request.POST.copy()
            request.POST['order'] = order.id
        return super().add_view(request, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        order_id = request.GET.get('order__id__exact')
        if order_id:
            add_url = reverse('admin:coins_orderitem_add') + f'?order_id={order_id}'
            if extra_context is None:
                extra_context = {}
            extra_context['add_url'] = add_url
        return super().changelist_view(request, extra_context=extra_context)

    def response_add(self, request, obj, post_url_continue=None):
        order_id = obj.order.first().id
        if "_continue" in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse('admin:coins_orderitem_changelist') + f'?order__id__exact={order_id}')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'order' in form.base_fields:
            form.base_fields['order'].widget.attrs['style'] = 'display:none;'
        return form
    
    def has_module_permission(self, request):
        return False

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = (display_username, 'phone_no', 'address', 'state', 'city', 'postal_code', 'country')
    form = ShippingAddressForm

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'state', 'postal_code', 'country', 'email', 'contact_no', 'shipping_charge')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'offer_type', 'discount_percentage', 'min_order_amount', 'max_discount_percentage', 'num_orders', 'discount_percentage')
    form = OfferForm

@admin.register(ShippingCharge)
class ShippingChargeAdmin(admin.ModelAdmin):
    list_display = ('state', 'country', 'charge')

@admin.register(CartItemLog)
class CartItemLogAdmin(admin.ModelAdmin):
    list_display = ('get_cart', display_username, 'action', 'timestamp', 'changes')

    def get_cart(self, obj):
        cart = obj.cart_item.first()
        if cart:
            coin = cart.coin.first()  # Assuming coin is an ArrayReferenceField containing one item
            if coin:
                return coin.coin_name
        return "None"
    get_cart.short_description = 'Cart Coin Name'