from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('auctions/', views.auctions, name='auctions'),
    path('coin-details/<int:coin_id>/', views.coin_details, name='coin-details'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('contact/', views.contact, name='contact'),
    path('error/', views.error, name='error'),
]