from django.contrib import admin

from .models import Order, OrderItem, Item, Payment, Coupon, Category, Profile


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('title',)
    }


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',)
    }


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', 'being_delivered',
                    'received', 'refund_requested', 'refund_granted',
                    'billing_address', 'payment', 'coupon']
    list_display_links = ['user', 'billing_address', 'payment', 'coupon']
    list_filter = ['ordered', 'being_delivered',
                   'received', 'refund_requested', 'refund_granted']
    search_fields = [
        'user__username',
        'ref_code'
    ]


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Item, ItemAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Profile)
