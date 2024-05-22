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
def dashboard(request):
    coins_list = Coin.objects.all().order_by('-id')  # Use 'id' instead of 'coin_id'
    paginator = Paginator(coins_list, 10)  # Change 10 to the desired number of items per page

    page = request.GET.get('page')
    try:
        coins = paginator.page(page)
    except PageNotAnInteger:
        coins = paginator.page(1)
    except EmptyPage:
        coins = paginator.page(paginator.num_pages)

    return render(request, 'dashboard.html', {'coins': coins})

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
    return render(request, 'home.html', {'coins': coins, 'company': company})

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
    return render(request, 'auctions.html', {'coins': coins, 'company': company})

def coin_details(request, coin_id):
    coin = get_object_or_404(Coin, id=coin_id)
    company = Company.objects.first()
    return render(request, 'coin-details.html', {'coin': coin, 'company': company})

def cart(request):
    company = Company.objects.first()
    return render(request, 'cart.html', {'company': company})

def checkout(request):
    company = Company.objects.first()
    return render(request, 'checkout.html', {'company': company})

def contact(request):
    company = Company.objects.first()
    return render(request, 'contact.html', {'company': company})

def error(request):
    company = Company.objects.first()
    return render(request, 'error.html', {'company': company})