from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
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


def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    # get order_item or create one in an order not completed
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(
        user=request.user, ordered=False)  # get order not completed

    # check if user has an active order else create one
    if order_qs.exists():

        # it is required for you to slice it
        # the returned result is also a query set
        # link: https://docs.djangoproject.com/en/3.1/topics/db/queries/#limiting-querysets

        order = order_qs[0]
        # check if ordered item is in the active order, increment the quantity else add it
        if order.items.filter(item__slug=slug).exists():
            order_item.quantity += 1
            order_item.save()
        else:
            order.items.add(order_item)
    else:
        ordered_date = timezone.now()
        new_order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        new_order.items.add(order_item)

    return redirect('core:product', slug=slug)



