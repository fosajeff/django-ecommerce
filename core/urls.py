from django.urls import path
from .views import (
    ProductHomeView,
    ProductDetailView,
    ProductCheckoutView,
)

app_name = 'core'


urlpatterns = [
    path('', ProductHomeView.as_view(), name='home'),
    path('product/<slug>/', ProductDetailView.as_view(), name='product'),
    path('checkout/',
         ProductCheckoutView.as_view(), name='checkout'),
]
