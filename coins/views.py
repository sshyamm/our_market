from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')

def auctions(request):
    return render(request, 'auctions.html')

def coin_details(request):
    return render(request, 'coin-details.html')

def cart(request):
    return render(request, 'cart.html')

def checkout(request):
    return render(request, 'checkout.html')

def contact(request):
    return render(request, 'contact.html')

def error(request):
    return render(request, 'error.html')
