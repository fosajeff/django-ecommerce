from django.contrib import admin

from .models import Order, OrderItem, Item, Payment, Coupon, Category, UserProfile, Refund, Address


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


def set_order_being_delivered(modeladmin, request, queryset):
    queryset.update(being_delivered=True)


set_order_being_delivered.short_description = 'Update orders to being delivered'


def make_order_delivered(modeladmin, request, queryset):
    queryset.update(being_delivered=False, received=True)


make_order_delivered.short_description = 'Update orders to delivered'


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('title',)
    }


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',)
    }


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'shipping_address',
                    'billing_address',
                    'payment',
                    'coupon']
    list_display_links = ['user',
                          'shipping_address',
                          'billing_address',
                          'payment',
                          'coupon']
    list_filter = ['ordered',
                   'being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted']
    search_fields = [
        'user__username',
        'ref_code'
    ]
    actions = [make_refund_accepted,
               set_order_being_delivered,
               make_order_delivered]


class AddressAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'street_address',
                    'appartment_address',
                    'country',
                    'zip_code',
                    'address_type',
                    'default']
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user__username',
                     'street_address', 'appartment_address', 'zip']


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Item, ItemAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Category, CategoryAdmin)
admin.site.register(UserProfile)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
