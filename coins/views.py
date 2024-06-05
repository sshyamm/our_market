from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse
from .models import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from decimal import Decimal
from bson.decimal128 import create_decimal128_context
import decimal
from django.utils import timezone
from bson.decimal128 import Decimal128

@login_required
def select_shipping(request):
    user = request.user
    shipping_addresses = ShippingAddress.objects.filter(user=user)
    
    form = ShippingAddressWebForm()

    return render(request, 'select_shipping.html', {
        'shipping_addresses': shipping_addresses,
        'form': form,
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    company = Company.objects.first()
    shipping_address = order.shippingaddress.first

    context = {
        'order': order,
        'order_items': order_items,
        'company': company,
        'shipping_address': shipping_address
    }
    return render(request, 'order_details.html', context)

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    # Annotate each order with its discounted total amount
    orders_with_amounts = []
    for order in orders:
        order.discounted_total_amount = order.calculate_discounted_total_amount()
        orders_with_amounts.append(order)

    return render(request, 'my_orders.html', {'orders': orders_with_amounts})


def thankyou(request, order_id):
    if request.session.get('order_placed') or request.GET.get('order_placed'):
        order = get_object_or_404(Order, id=order_id)
        context = {
            'order': order,
        }
        request.session.pop('order_placed', None)
        return render(request, 'thankyou.html', context)
    else:
        return redirect(reverse('home'))

@login_required
def place_order(request):
    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address_id')
        eligible_offers_ids = request.POST.getlist('eligible_offers')
        eligible_offers = Offer.objects.filter(id__in=eligible_offers_ids)
            
        selected_address = ShippingAddress.objects.get(pk=selected_address_id)

        # Create order with the address and eligible offers
        order = Order.objects.create(status='Pending')
        order.user.add(request.user)
        order.shippingaddress.add(selected_address)

        for offer in eligible_offers:
            order.offer.add(offer)

        # Fetch all cart items for the current user
        cart_items = CartItem.objects.filter(user=request.user)

        # Create order items based on cart items
        for cart_item in cart_items:
            order_item = OrderItem()
            order_item.order.add(order)
            order_item.coin.add(*cart_item.coin.all())
            order_item.quantity = cart_item.quantity
            order_item.save()
        cart_items.delete()
        request.session['order_placed'] = True

        # Redirect to the cart page
        return HttpResponseRedirect(reverse('thankyou', kwargs={'order_id': order.id}))

    # If the request method is not POST or if an error occurs, redirect back to the checkout page
    return redirect('cart')

@login_required
def checkout_view(request):
    user = request.user
    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address_id')
        if selected_address_id :
            address_id = request.POST.get('selected_address_id')
        else :
            form = ShippingAddressWebForm(request.POST)
            if form.is_valid():
                shipping = form.save(commit=False)
                shipping.user.add(request.user)  # Link the address to the current user
                shipping.save()
                address_id = shipping.id
        
        shipping_address = get_object_or_404(ShippingAddress, id=address_id, user=user)
        
        # Retrieve shipping charge based on address state and country
        shipping_charge = None
        try:
            shipping_charge = ShippingCharge.objects.get(state__iexact=shipping_address.state, country=shipping_address.country)
        except ShippingCharge.DoesNotExist:
            # Apply default shipping charge from the Company model
            company = Company.objects.first()  # Assuming there is only one company record
            default_shipping_charge = company.shipping_charge
            # Convert Decimal128 to Decimal
            default_shipping_charge = default_shipping_charge.to_decimal()

        cart_items = CartItem.objects.filter(user=user)
        total_price = sum(Decimal(item.price) for item in cart_items)  # Convert prices to Decimal

        cart_items_with_images = [
            (item, CoinImage.objects.filter(coin=item.coin.first(), root_image='yes').first())
            for item in cart_items
        ]

        # Retrieve eligible offers
        eligible_offers = {}
        current_time = timezone.now()  # Get the current date and time

        for offer in Offer.objects.all():
            if (offer.offer_type == 'TotalAmount' and total_price >= Decimal(str(offer.min_order_amount))) or \
            (offer.offer_type == 'UserBased'):
                if offer.offer_type == 'UserBased':
                    recent_order_with_user_based_offer = Order.objects.filter(
                        user=user,
                        offer__offer_type='UserBased',  # Filter by 'UserBased' offer type
                        order_date__lt=current_time
                    ).order_by('-order_date').first()

                    if recent_order_with_user_based_offer:
                        num_previous_orders = Order.objects.filter(
                            user=user,
                            order_date__gt=recent_order_with_user_based_offer.order_date,
                            order_date__lt=current_time
                        ).count()
                    else:
                        num_previous_orders = Order.objects.filter(
                            user=user,
                            order_date__lt=current_time
                        ).count()

                    if num_previous_orders >= offer.num_orders:
                        offer_discount_percentage = Decimal(offer.discount_percentage.to_decimal())
                        if (offer.offer_type not in eligible_offers) or (offer_discount_percentage > Decimal(eligible_offers[offer.offer_type].discount_percentage.to_decimal())):
                            # Check if the 'TotalAmount' offer's discount percentage is less than or equal to the 'UserBased' offer's max_discount_percentage
                            if 'TotalAmount' not in eligible_offers or eligible_offers['TotalAmount'].discount_percentage.to_decimal() < offer.max_discount_percentage.to_decimal():
                                eligible_offers[offer.offer_type] = offer
                else:
                    offer_discount_percentage = Decimal(offer.discount_percentage.to_decimal())
                    if (offer.offer_type not in eligible_offers) or (offer_discount_percentage > Decimal(eligible_offers[offer.offer_type].discount_percentage.to_decimal())):
                        eligible_offers[offer.offer_type] = offer

        # Apply eligible offers to total price
        final_price = total_price
        revised_discount_percentage = Decimal('0')  # Initialize revised discount percentage for UserBased offer
        for offer in eligible_offers.values():
            discount_percentage = Decimal(str(offer.discount_percentage))
            if offer.offer_type == 'TotalAmount':
                discount_amount = (final_price * discount_percentage) / Decimal('100')
                final_price -= discount_amount
            elif offer.offer_type == 'UserBased':
                if 'TotalAmount' in eligible_offers:  # If both offer types are applied
                    total_discount_percentage = discount_percentage + Decimal(eligible_offers['TotalAmount'].discount_percentage.to_decimal())
                    max_discount_percentage = Decimal(eligible_offers['UserBased'].max_discount_percentage.to_decimal())
                    if total_discount_percentage > max_discount_percentage:
                        revised_discount_percentage = max_discount_percentage - Decimal(eligible_offers['TotalAmount'].discount_percentage.to_decimal())
                else:
                    discount_amount = (final_price * discount_percentage) / Decimal('100')
                    final_price -= discount_amount

        # Adjust final price if revised discount percentage is calculated
        if revised_discount_percentage:
            user_based_offer_discount = (final_price * revised_discount_percentage) / Decimal('100')
            final_price -= user_based_offer_discount

        # Apply shipping charge to the total price
        if shipping_charge:
            shipping_charge_decimal = shipping_charge.charge.to_decimal()
            final_price += shipping_charge_decimal
        else:
            final_price += default_shipping_charge

        return render(request, 'checkout.html', {
            'cart_items': cart_items,
            'cart_items_with_images': cart_items_with_images,
            'total_price': total_price.quantize(Decimal('0.01')),  # Pass original total price to the template
            'final_price': final_price.quantize(Decimal('0.01')),  # Pass final price to the template
            'shipping_address': shipping_address,
            'eligible_offers': list(eligible_offers.values()),  # Pass eligible offers to the template
            'revised_discount_percentage': revised_discount_percentage,
            'applied_shipping_charge': shipping_charge_decimal if shipping_charge else default_shipping_charge,
        })
    else:
        return redirect('cart')
    
@login_required
def add_to_cart(request, coin_id):
    if request.method == 'POST':
        # Get the selected coin
        coin = get_object_or_404(Coin, pk=coin_id)
        # Get the current user
        user = request.user
        
        # Check if the coin is already in the user's cart
        existing_cart_item = CartItem.objects.filter(coin=coin, user=user).first()
        if existing_cart_item:
            # If the coin is already in the cart, increase its quantity by 1
            existing_cart_item.quantity += 1
            existing_cart_item.save()
            messages.success(request, f'Another {coin.coin_name} has been added to your cart!')
        else:
            # If the coin is not in the cart, create a new CartItem object
            cart_item = CartItem(quantity=1)
            cart_item.coin.add(coin)  # Add the coin to the cart item
            cart_item.user.add(user)  # Add the user to the cart item
            cart_item.save()  # Save the cart item
            messages.success(request, 'Your item has been added to the cart!')
        
        # Redirect to the cart page
        return redirect('cart')
    else:
        return redirect('cart')
    
from django.http import JsonResponse
   
@login_required
@require_POST
def update_cart_item(request):
    item_id = request.POST.get('item_id')
    new_quantity = request.POST.get('quantity')

    try:
        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        new_quantity = int(new_quantity)
        
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            response = {
                'status': 'success',
                'item_id': item_id,
                'new_price': cart_item.coin.first().rate * new_quantity,
                'total_price': sum(item.coin.first().rate * item.quantity for item in CartItem.objects.filter(user=request.user))
            }
        else:
            cart_item.delete()
            response = {
                'status': 'deleted',
                'item_id': item_id,
                'total_price': sum(item.coin.first().rate * item.quantity for item in CartItem.objects.filter(user=request.user))
            }
    except (CartItem.DoesNotExist, ValueError):
        response = {'status': 'error'}

    return JsonResponse(response)

@login_required
@require_POST
def remove_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id, user=request.user)
        item.delete()
        response = {'status': 'success'}
    except CartItem.DoesNotExist:
        response = {'status': 'error', 'message': 'Item not found.'}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}

    return JsonResponse(response)

@login_required
@require_POST
def clear_cart(request):
    try:
        CartItem.objects.filter(user=request.user).delete()
        response = {'status': 'success'}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}

    return JsonResponse(response)

@login_required
def create_coin(request):
    if request.method == 'POST':
        form = CoinWebForm(request.POST, request.FILES, user=request.user)  # Pass current user to form
        if form.is_valid():
            form.save()
            messages.success(request, 'Coin created successfully!')
            return redirect(reverse('coin-details', kwargs={'coin_id': form.instance.pk}))
    else:
        form = CoinWebForm(user=request.user)  # Pass current user to form
    return render(request, 'create_coin.html', {'form': form})

@login_required
def edit_coin(request, coin_id):
    coin = get_object_or_404(Coin, id=coin_id)
    if request.method == 'POST':
        form = CoinWebForm(request.POST, request.FILES, instance=coin, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coin updated successfully!')
            return redirect(reverse('coin-details', kwargs={'coin_id': coin.id}))
    else:
        form = CoinWebForm(instance=coin, user=request.user)
    return render(request, 'edit_coin.html', {'form': form, 'coin': coin})

@login_required
def dashboard(request):
    search_params = {}
    coins_list = Coin.objects.all().order_by('-id')  # Initialize coins_list here

    if request.method == 'POST':
        # Handle search functionality and store search history
        for key in request.POST:
            if key != 'csrfmiddlewaretoken':
                value = request.POST[key]
                if value:
                    # Get the field object from the Coin model
                    field_object = Coin._meta.get_field(key)
                    # Check if the field is an integer or number field
                    if isinstance(field_object, (models.IntegerField, models.DecimalField, models.FloatField)):
                        try:
                            # Convert the value to the appropriate type
                            value = field_object.to_python(value)
                            # For integer and number fields, perform exact match
                            search_params[key] = value
                        except ValueError:
                            # Handle the case where the value cannot be converted to the appropriate type
                            messages.error(request, f'Invalid value for {key}. Please enter a valid number.')
                            return redirect('coins:home')
                    else:
                        # Use __icontains for partial matching for non-integer fields
                        search_params[key + '__icontains'] = value
                    
                    # Save search history to the database
                    search_history = SearchHistory.objects.create(search_text=f'{key.capitalize()}: {value}')
                    search_history.user.add(request.user)  # Add the current user to the user field
                    search_history.save()

        # Filter coins based on search parameters
        coins_list = coins_list.filter(**search_params)

    paginator = Paginator(coins_list, 10)  # Change 10 to the desired number of items per page

    page = request.GET.get('page')
    try:
        coins = paginator.page(page)
    except PageNotAnInteger:
        coins = paginator.page(1)
    except EmptyPage:
        coins = paginator.page(paginator.num_pages)

    coins_with_images = []
    for coin in coins:
        root_image = CoinImage.objects.filter(coin=coin, root_image='yes').first()
        coins_with_images.append((coin, root_image))

    # Retrieve search history for the current user
    search_history = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')

    return render(request, 'dashboard.html', {'coins_with_images': coins_with_images, 'coins': coins, 'search_history': search_history})

@login_required
def soft_delete_coin(request, coin_id):
    coin = get_object_or_404(Coin, pk=coin_id)
    coin.is_deleted = 'yes'
    coin.save()
    messages.success(request, f'{coin.coin_name} has been deleted.')
    return redirect('dashboard')

@login_required
def clear_search_history(request, search_history_id):
    # Retrieve the search history item to delete
    search_history_item = get_object_or_404(SearchHistory, pk=search_history_id)

    # Check if the search history item belongs to the current user
    if request.user in search_history_item.user.all():
        # Delete the search history item
        search_history_item.delete()
    else:
        messages.error(request, 'You do not have permission to delete this search history item.')

    # Redirect back to the dashboard page
    return redirect('dashboard')

@login_required
def view_profile(request):
    profile = Profile.objects.filter(user=request.user).first()
    shipping_addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, 'registration/profile.html', {'profile': profile, 'shipping_addresses': shipping_addresses})

@login_required
def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingAddressWebForm(request.POST)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user.add(request.user)  # Link the address to the current user
            shipping_address.save()
            messages.success(request, 'Shipping address added successfully.')
            return redirect('view_profile')
    else:
        form = ShippingAddressWebForm()
    return render(request, 'registration/edit_shipping_address.html', {'form': form})

@login_required
def edit_shipping_address(request, address_id):
    shipping_address = ShippingAddress.objects.get(id=address_id, user=request.user)
    if not shipping_address:
        return redirect('add_shipping_address')

    if request.method == 'POST':
        form = ShippingAddressWebForm(request.POST, instance=shipping_address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Shipping address updated successfully.')
            return redirect('view_profile')
    else:
        form = ShippingAddressWebForm(instance=shipping_address)
    return render(request, 'registration/edit_shipping_address.html', {'form': form})

@login_required
def delete_shipping_address(request, address_id):
    shipping_address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    shipping_address.delete()
    messages.success(request, 'Shipping address deleted successfully.')
    return redirect('view_profile')

@login_required
def edit_profile(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)

    if request.method == 'POST':
        form = EditUserProfileForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Profile details successfully updated !!')
            return redirect('view_profile')  # Redirect to the profile page after saving
    else:
        form = EditUserProfileForm(instance=profile, user=user)

    return render(request, 'registration/edit_profile.html', {'form': form})

class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

@login_required
def custom_password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            request.session['password_changed'] = True
            return redirect(reverse('password_change_done'))
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change-password.html', {'form': form})

@login_required
def custom_password_change_done(request):
    if request.session.get('password_changed') or request.GET.get('password_changed'):
        request.session.pop('password_changed', None)
        return render(request, 'registration/password-done.html')
    else:
        return redirect(reverse('home'))
            
# Create your views here.
def home(request):
    coins = Coin.objects.filter(is_deleted='no')  # Fetch all coins
    company = Company.objects.first()  # Fetch the first company record
    
    # Fetch the root images for each coin
    coins_with_images = []
    for coin in coins:
        root_image = CoinImage.objects.filter(coin=coin, root_image='yes').first()
        coins_with_images.append((coin, root_image))
    
    return render(request, 'home.html', {'coins_with_images': coins_with_images, 'company': company})

def signup(request):
    if request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created successfully. Please log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    company = Company.objects.first()
    return render(request, 'registration/signup.html', {'form': form, 'company': company})

def auctions(request):
    coins = Coin.objects.filter(is_deleted='no')   # Fetch all coins
    company = Company.objects.first()

    coins_with_images = []
    for coin in coins:
        root_image = CoinImage.objects.filter(coin=coin, root_image='yes').first()
        coins_with_images.append((coin, root_image))
    return render(request, 'auctions.html', {'coins': coins, 'coins_with_images': coins_with_images, 'company': company})

def coin_details(request, coin_id):
    coin = get_object_or_404(Coin, id=coin_id)
    company = Company.objects.first()
    
    # Fetch the root image for the coin
    root_image = CoinImage.objects.filter(coin=coin, root_image='yes').first()
    
    # Fetch all images for the coin
    coin_images = CoinImage.objects.filter(coin=coin)
    
    return render(request, 'coin-details.html', {
        'coin': coin,
        'company': company,
        'root_image': root_image,
        'coin_images': coin_images
    })

def cart(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_price = sum(item.price for item in cart_items)

    # Fetch the root images for each coin in the cart items
    cart_items_with_images = []
    for item in cart_items:
        coin = item.coin.first()  # Get the coin associated with the cart item
        root_image = CoinImage.objects.filter(coin=coin, root_image='yes').first()
        cart_items_with_images.append((item, root_image))

    return render(request, 'cart.html', {'cart_items': cart_items, 'cart_items_with_images': cart_items_with_images, 'total_price': total_price})

def contact(request):
    company = Company.objects.first()
    return render(request, 'contact.html', {'company': company})

def error(request):
    company = Company.objects.first()
    return render(request, 'error.html', {'company': company})