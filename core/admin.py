from django.contrib import admin

from .models import Order, OrderItem, Item, Payment, Coupon, Category


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('title',)
    }


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',)
    }


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered']


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Item, ItemAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Category, CategoryAdmin)
