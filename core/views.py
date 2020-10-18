from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import Order, OrderItem, Item, Address, Payment, Coupon, Category, Refund, UserProfile
from .forms import CheckoutForm, CouponForm, RefundForm, UserForm, PaymentForm
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    View
)
import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class HomeView(ListView):
    model = Item
    template_name = 'home-page.html'
    paginate_by = 8
    ordering = 'title'
    context_object_name = 'items'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all()
        })
        return context


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
                userprofile = self.request.user.userprofile
                if userprofile.one_click_processing:
                    # fetch the user's card list
                    cards = stripe.Customer.list_sources(
                        userprofile.stripe_customer_id,
                        limit=3,
                        object='card'
                    )
                    card_list = cards['data']
                    if len(card_list) > 0:
                        # update the context with the default card
                        context.update({
                            'card': card_list[0]
                        })
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
            form = PaymentForm(self.request.POST)
            userprofile = UserProfile.objects.get(user=self.request.user)
            if form.is_valid():
                token = form.cleaned_data.get('PaymentForm')
                save = form.cleaned_data.get('save')
                use_default = form.cleaned_data.get('use_default')

                if save:
                    # allow to fetch cards
                    if not userprofile.stripe_customer_id:
                        customer = stripe.Customer.create(
                            email=self.request.user.email,
                            source=token
                        )
                        userprofile.stripe_customer_id = customer['id']
                        userprofile.one_click_processing = True
                        userprofile.save()
                    else:
                        stripe.Customer.create_source(
                            userprofile.stripe_customer_id,
                            source=token
                        )

                amount = int(order.get_total() * 100)

                try:
                    # Use Stripe's library to make requests...
                    if use_default:
                        charge = stripe.Charge.create(
                            amount=amount,  # cents
                            currency='usd',
                            customer=userprofile.stripe_customer_id,
                        )
                    else:
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


def is_valid_form(fields):
    valid = True
    for field in fields:
        if field == '':
            valid = False
    return valid


class ProductCheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            coupons = Coupon.objects.all()
            form = CheckoutForm()
            coupon_form = CouponForm()
            context = {
                'order': order,
                'form': form,
                'coupons': coupons,
                'couponform': coupon_form,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})

            return render(self.request, 'checkout-page.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect('/')

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)

            if form.is_valid():
                # shipping address
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')

                if use_default_shipping:
                    shipping_address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if shipping_address_qs.exists():
                        shipping_address = shipping_address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')

                else:
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip_code = form.cleaned_data.get(
                        'shipping_zip_code')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip_code]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            appartment_address=shipping_address2,
                            country=shipping_country,
                            zip_code=shipping_zip_code,
                            address_type='S',
                        )
                        shipping_address.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                            order.shipping_address = shipping_address
                            order.save()
                    else:
                        messages.warning(
                            self.request, "Please fill in the required shipping address fields")
                        return redirect('core:checkout')

                # billing address
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.shipping_address = shipping_address
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    billing_address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if billing_address_qs.exists():
                        billing_address = billing_address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')

                else:
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip_code = form.cleaned_data.get(
                        'billing_zip_code')

                    if is_valid_form([billing_address1, billing_country, billing_zip_code]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            appartment_address=billing_address2,
                            country=billing_country,
                            zip_code=billing_zip_code,
                            address_type='B',
                        )
                        billing_address.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                            order.billing_address = billing_address
                            order.save()
                    else:
                        messages.warning(
                            self.request, "Please fill in the required billing address fields")
                        return redirect('core:checkout')

                payment_option = form.cleaned_data.get('payment_option')
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
        ref_code = create_ref_code()
        new_order = Order.objects.create(
            user=request.user, ordered_date=ordered_date, ref_code=ref_code)
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

                if order.coupon or order.coupon == coupon:
                    messages.info(self.request, "Offer applied already")
                    return redirect('core:checkout')
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


class RefundRequestView(View):
    def get(self, *args, **kwargs):
        context = {
            'form': RefundForm()
        }
        return render(self.request, 'request-refund.html', context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')

            try:
                # edit order
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.user = self.request.user
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(
                    self.request, "Your request was sent successfully")
                return redirect('core:request-refund')
            except ObjectDoesNotExist:
                messages.warning(
                    self.request, "Order with reference code does not exist")
                return redirect('core:request-refund')


class UserProfileView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        form = UserForm()
        prev_order_qs = Order.objects.filter(
            user=self.request.user, ordered=True)
        active_order_qs = Order.objects.filter(
            user=self.request.user, ordered=False)
        if prev_order_qs.exists():
            prev_order = prev_order_qs
            print(prev_order)
        else:
            prev_order = None
        if active_order_qs.exists():
            active_order = active_order_qs[0]
        else:
            active_order = None

        try:
            profile = UserProfile.objects.get(
                user=self.request.user)

            context = {
                'profile': profile,
                'prev_order': prev_order,
                'active_order': active_order,
                'form': form
            }
            return render(self.request, "profile.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "No profile for user")
            return redirect('/')

    def post(self, *args, **kwargs):
        form = UserForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            photo = form.cleaned_data.get('photo')
            username = form.cleaned_data.get('username')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            if not username and not first_name and not last_name and not photo:
                messages.info(
                    self.request, "Invalid input, could not update your profile")
                return redirect('core:profile')
            else:
                try:
                    user = User.objects.get(
                        username=self.request.user.username)
                    profile = UserProfile.objects.get(
                        user=self.request.user)
                    if photo:
                        profile.photo = photo
                        profile.save()
                    if username:
                        user.username = username
                    if first_name:
                        user.first_name = first_name
                    if last_name:
                        user.last_name = last_name
                    user.save()
                    messages.success(
                        self.request, "Profile updated successfully")
                    return redirect('core:profile')

                except ObjectDoesNotExist:
                    messages.info(self.request, "User does not exist")
                    return redirect('/')
