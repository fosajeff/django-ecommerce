from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import Order, OrderItem, Item, BillingAddress
from .forms import CheckoutForm
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    View
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


class OrderSummary(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            context = {
                'order': Order.objects.get(
                    user=self.request.user,
                    ordered=False
                )
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order.")
            return redirect('/')


class ProductCheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            context = {
                'order': Order.objects.get(
                    user=self.request.user,
                    ordered=False
                ),
                'form': CheckoutForm()
            }

            return render(self.request, 'checkout-page.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order.")
            return redirect('/')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                appartment_address = form.cleaned_data.get(
                    'appartment_address')
                country = form.cleaned_data.get('country')
                zip_code = form.cleaned_data.get('zip_code')
                same_shipping_address = form.cleaned_data.get(
                    'same_shipping_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')

                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    appartment_address=appartment_address,
                    country=country,
                    zip_code=zip_code
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                # Add redirect to selected payment option
                messages.info(
                    self.request, "Redirecting to your selected payment gateway...")
                return redirect('core:checkout')
            messages.warning(self.request, "Checkout not successful.")
            return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order.")
            return redirect('/')


@login_required
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
            return redirect('core:order-summary')
        else:
            messages.success(request, "Item added to your cart.")
            order.items.add(order_item)
            return redirect('core:order-summary')
    else:
        ordered_date = timezone.now()
        new_order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        new_order.items.add(order_item)
        messages.success(request, "Item added to your cart.")
        return redirect('core:order-summary')


@login_required
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
            order_item.quantity = 1
            order_item.save()
            messages.info(request, "Item removed from your cart.")
            return redirect('core:order-summary')
        else:
            # the item is not in your active order
            messages.warning(request, "This item is not in your cart.")
            return redirect('core:product', slug=slug)
    else:
        # the user does not have an active order
        messages.warning(request, "You do not have an active order.")
        return redirect('core:product', slug=slug)


@login_required
def remove_single_from_cart(request, slug):
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

            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, "Item quantity was updated.")

            else:
                order.items.remove(order_item)
                messages.info(request, "Item removed from your cart.")

            return redirect('core:order-summary')
        else:
            # the item is not in your active order
            messages.warning(request, "This item is not in your cart.")
            return redirect('core:product', slug=slug)
    else:
        # the user does not have an active order
        messages.warning(request, "You do not have an active order.")
        return redirect('core:product', slug=slug)
