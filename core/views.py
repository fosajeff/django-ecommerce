from django.shortcuts import render
from .models import Order, OrderItem, Item
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
)


class ProductHomeView(ListView):
    model = Item
    template_name = 'home-page.html'


class ProductDetailView(DetailView):
    model = Item
    template_name = 'product-page.html'


class ProductCheckoutView(TemplateView):
    model = Order
    template_name = 'checkout-page.html'
