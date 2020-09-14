from django.shortcuts import render, get_object_or_404
from django.contrib import messages
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
    paginate_by = 8
    ordering = 'title'


class ProductsView(ListView):
    model = Item
    template_name = 'products.html'
    paginate_by = 12
    ordering = 'title'


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
            messages.info(request, "This item quantity was updated.")
            return redirect('core:product', slug=slug)
        else:
            messages.success(request, "Item added to your cart.")
            order.items.add(order_item)
            return redirect('core:product', slug=slug)
    else:
        ordered_date = timezone.now()
        new_order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        new_order.items.add(order_item)
        messages.success(request, "Item added to your cart.")
        return redirect('core:product', slug=slug)


def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Item was removed from cart.")
            return redirect('core:product', slug=slug)
        else:
            # the item is not in your active order
            messages.warning(request, "This item is not in your cart.")
            return redirect('core:product', slug=slug)
    else:
        # the user does not have an active order
        messages.warning(request, "You do not have an active order.")
        return redirect('core:product', slug=slug)
