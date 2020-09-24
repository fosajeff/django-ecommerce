from django.contrib import admin

from .models import Order, OrderItem, Item, Payment

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Item)
admin.site.register(Payment)
