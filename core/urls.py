from django.urls import path
from .views import (
    ProductHomeView,
    ProductDetailView,
    ProductCheckoutView,
    ProductPaymentView,
    ProductsView,
    OrderSummary,
    add_to_cart,
    remove_from_cart,
    remove_single_from_cart,
)

app_name = 'core'


urlpatterns = [
    path('', ProductHomeView.as_view(), name='home'),
    path('products/', ProductsView.as_view(), name='products'),
    path('order-summary/', OrderSummary.as_view(), name='order-summary'),
    path('product/<slug>/', ProductDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_from_cart,
         name='remove-single-item-from-cart'),
    path('checkout/',
         ProductCheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', ProductPaymentView.as_view(), name='payment')
]
