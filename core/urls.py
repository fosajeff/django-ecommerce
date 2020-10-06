from django.urls import path
from .views import (
    HomeView,
    ProductDetailView,
    ProductCheckoutView,
    ProductPaymentView,
    ProductsView,
    OrderSummary,
    add_to_cart,
    remove_from_cart,
    remove_single_from_cart,
    AddCouponView,
    get_items_by_category,
    RefundRequestView,
    UserProfileView,
)

app_name = 'core'


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('products/', ProductsView.as_view(), name='products'),
    path('order-summary/', OrderSummary.as_view(), name='order-summary'),
    path('product/<slug>/', ProductDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_from_cart,
         name='remove-single-item-from-cart'),
    path('checkout/',
         ProductCheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/',
         ProductPaymentView.as_view(), name='payment'),
    path('products/category/<slug>',
         get_items_by_category, name='category-filter'),
    path('request-refund/', RefundRequestView.as_view(), name='request-refund'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
