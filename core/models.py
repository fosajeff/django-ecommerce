from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField


LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

LABEL_TAGS = (
    ('N', 'NEW'),
    ('F', 'Featured'),
    ('B', 'bestseller')
)


class Category(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=30, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Item(models.Model):
    title = models.CharField(max_length=20)
    price = models.FloatField()
    percentage_discount = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(Category,
                                 on_delete=models.SET_NULL, null=True, blank=True)
    label_tag = models.CharField(
        choices=LABEL_TAGS, max_length=1, null=True, blank=True)
    label = models.CharField(choices=LABEL_CHOICES,
                             max_length=1, null=True, blank=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    image = models.ImageField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug
        })

    def get_discount_price(self):
        if self.percentage_discount:
            return round((100 - self.percentage_discount) / 100 * self.price, 2)

    def get_add_to_cart_url(self):
        return reverse('core:add-to-cart', kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('core:remove-from-cart', kwargs={
            'slug': self.slug
        })

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        return '#'


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        if self.item.get_discount_price():
            return round(self.item.get_discount_price() * self.quantity, 2)
        return round(self.item.price * self.quantity, 2)

    def get_amount_saved(self):
        if self.item.get_discount_price():
            return round(self.item.price * self.quantity - self.get_total_item_price(), 2)


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey(
        'BillingAddress', on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total(self):
        if self.coupon:
            if self.coupon.percentage_discount:
                # apply the percentage discount of the coupon and get the new order total price
                total = sum([price.get_total_item_price()
                             for price in self.items.all()])
                return round((100 - self.coupon.percentage_discount) / 100 * total, 2)
        return sum([price.get_total_item_price() for price in self.items.all()])


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    appartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    percentage_discount = models.IntegerField()

    def __str__(self):
        return self.code
