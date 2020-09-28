from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import Order, OrderItem, Item, BillingAddress, Payment, Coupon, Category
from .forms import CheckoutForm, CouponForm
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    View
)
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(ListView):
    model = Item
    template_name = 'home-page.html'
    paginate_by = 8
    ordering = 'title'

# def get_items_by_category(request, category):
#     items_qs = Item.objects.filter(ca)


class ProductsView(ListView):
    model = Item
    template_name = 'products.html'
    paginate_by = 12
    ordering = 'title'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all()
        })
        return context


def get_items_by_category(request, slug):
    try:
        category = Category.objects.get(slug=slug)
        item_qs = Item.objects.filter(category=category)
        # print(f"queryset:{item_qs}")

        if item_qs.exists():
            items = item_qs[:]
            print(items)

            context = {
                'active_category_slug': slug,
                'categories': Category.objects.all(),
                'items': items
            }
            return render(request, 'products.html', context)
        else:
            messages.info(request, "No items in this category")
            return redirect('core:products')
    except ObjectDoesNotExist:
        messages.info(request, "No such category exist")
        return redirect('core:products')


class ProductDetailView(DetailView):
    model = Item
    template_name = 'product-page.html'


class ProductPaymentView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if order.billing_address:
                context = {
                    'order': order,
                    'DISPLAY_COUPON_FORM': False
                }
                return render(self.request, 'payment.html', context)
            else:
                messages.info(
                    self.request, "You have not added a billing address")
                return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect('/')

    def post(self, *args, **kwargs):
        try:
            order = Order.objects.get(
                user=self.request.user,
                ordered=False
            )
            token = self.request.POST.get('stripeToken')
            amount = int(order.get_total() * 100)

            try:
                # Use Stripe's library to make requests...
                charge = stripe.Charge.create(
                    amount=amount,  # cents
                    currency='usd',
                    source=token,
                )

                # create the payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # change ordered status in orderItem
                order_item = order.items.all()
                order_item.update(ordered=True)
                for item in order_item:
                    item.save()

                # assign payment to order
                order.ordered = True
                order.payment = payment
                order.save()

                messages.success(self.request, "Your order was successful")
                return redirect('/')

                # check for the selected payment gateway alreay.

            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect('/')

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, "Rate limit error")
                return redirect('/')

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.warning(self.request, "Invalid parameters")
                return redirect('/')

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, "Not authenticated")
                return redirect('/')

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, "Network error")
                return redirect('/')

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(
                    self.request, "Something went wrong. You were not charged. Please try again")
                return redirect('/')

            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.warning(
                    self.request, "A serious error occured. We have been notified")
                return redirect('/')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect('/')


class OrderSummary(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            context = {
                'order': Order.objects.get(
                    user=self.request.user,
                    ordered=False
                ),
                'coupon': Coupon.objects.all()
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect('/')


class ProductCheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            coupon_form = CouponForm()
            context = {
                'order': order,
                'form': form,
                'couponform': coupon_form,
                'DISPLAY_COUPON_FORM': True
            }

            return render(self.request, 'checkout-page.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
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

                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
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
            messages.info(request, "This item quantity was updated")
            return redirect('core:order-summary')
        else:
            messages.success(request, "Item added to your cart")
            order.items.add(order_item)
            return redirect('core:order-summary')
    else:
        ordered_date = timezone.now()
        new_order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        new_order.items.add(order_item)
        messages.success(request, "Item added to your cart")
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
            messages.info(request, "Item removed from your cart")
            return redirect('core:order-summary')
        else:
            # the item is not in your active order
            messages.warning(request, "This item is not in your cart")
            return redirect('core:product', slug=slug)
    else:
        # the user does not have an active order
        messages.warning(request, "You do not have an active order")
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
                messages.info(request, "Item quantity was updated")

            else:
                order.items.remove(order_item)
                messages.info(request, "Item removed from your cart")

            return redirect('core:order-summary')
        else:
            # the item is not in your active order
            messages.warning(request, "This item is not in your cart")
            return redirect('core:product', slug=slug)
    else:
        # the user does not have an active order
        messages.warning(request, "You do not have an active order")
        return redirect('core:product', slug=slug)


class AddCouponView(View):
    def post(self, *args, **kwargs):

        form = CouponForm(self.request.POST)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')

                # validate coupon
                try:
                    coupon = Coupon.objects.get(code=code)

                except ObjectDoesNotExist:
                    messages.info(self.request, "This coupon does not exist")
                    return redirect('core:checkout')

                # save coupon in user order if valid
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = coupon
                order.save()
                messages.success(self.request, "Coupon added successfully")
                return redirect('core:checkout')

            # handle exception for getting user order
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect('/')
        messages.warning(self.request, "Enter valid coupon code")
        return redirect('core:checkout')
