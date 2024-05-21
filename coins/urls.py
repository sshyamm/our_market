from django.urls import path, include
from . import views
from .views import CustomLoginView, custom_password_change, custom_password_change_done

urlpatterns = [
    path('', views.home, name='home'),
    path("accounts/login/", CustomLoginView.as_view(), name='login'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('accounts/signup/', views.signup, name='signup'),
    path("password_change/", custom_password_change, name="password_change"),
    path("password_change/done/", custom_password_change_done, name="password_change_done"),
    path('auctions/', views.auctions, name='auctions'),
    path('coin-details/<int:coin_id>/', views.coin_details, name='coin-details'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('contact/', views.contact, name='contact'),
    path('error/', views.error, name='error'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]