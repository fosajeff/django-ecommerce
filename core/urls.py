from django.urls import path
from .views import (
    ProductHomeView,
    ProductDetailView,
    ProductCheckoutView,
    add_to_cart,
    remove_from_cart,
)

app_name = 'core'


urlpatterns = [
    path('', ProductHomeView.as_view(), name='home'),
    path('product/<slug>/', ProductDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('checkout/',
         ProductCheckoutView.as_view(), name='checkout'),
]
