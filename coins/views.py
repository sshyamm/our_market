from django.shortcuts import render, get_object_or_404
from .models import *

# Create your views here.
def home(request):
    coins = Coin.objects.all()  # Fetch all coins
    company = Company.objects.first()  # Fetch the first company record
    return render(request, 'home.html', {'coins': coins, 'company': company})

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