from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.urls import reverse
from .models import *
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .forms import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST

@login_required
def checkout_view(request):
    if request.method == 'POST':
        user = request.user
        cart_items = CartItem.objects.filter(user=user)
        total_price = sum(item.price for item in cart_items)

        # Fetch all offers
        all_offers = Offer.objects.all()

        return render(request, 'checkout.html', {
            'cart_items': cart_items,
            'total_price': total_price,
            'all_offers': all_offers,
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
        # Create a CartItem object
        cart_item = CartItem(quantity=1)
        cart_item.coin.add(coin)  # Add the coin to the cart item
        cart_item.user.add(user)  # Add the user to the cart item
        cart_item.save()  # Save the cart item
        # Redirect to the cart page
        messages.success(request, 'Your item has been added to the cart!')
        return redirect('cart')
    else:
        # Handle GET request (if needed)
        pass
    
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
def remove_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    messages.success(request, 'Item removed successfully!')
    return redirect('cart')

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

    # Retrieve search history for the current user
    search_history = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')

    return render(request, 'dashboard.html', {'coins': coins, 'search_history': search_history})

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
    return render(request, 'registration/profile.html', {'profile': profile})

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
    coins = Coin.objects.all()  # Fetch all coins
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
    coins = Coin.objects.all()  # Fetch all coins
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
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

def contact(request):
    company = Company.objects.first()
    return render(request, 'contact.html', {'company': company})

def error(request):
    company = Company.objects.first()
    return render(request, 'error.html', {'company': company})