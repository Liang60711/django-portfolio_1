from django.contrib import admin
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address, UserProfile


# action 加入 update 退款許可(refund_granted) 功能
def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_granted=True)

make_refund_accepted.short_description = 'Update orders to refund granted'



# 確認 Order 狀態
class OrderAdmin(admin.ModelAdmin):
    # 狀態欄
    list_display = [
        'user', 
        'ordered', 
        'ref_code',
        'being_delivered', 
        'received',
        'refund_requested',
        'refund_granted',
        'shipping_address',
        'billing_address',
        'payment',
        'coupon',
    ]
    
    # 狀態欄 link (必須在 list_display 裡面)
    list_display_links = [
        'user',
        'ref_code',
        'shipping_address',
        'billing_address',
        'payment',
        'coupon',
    ]
    
    # admin 右方篩選欄
    list_filter = [
        'ordered', 
        'being_delivered', 
        'received',
        'refund_requested',
        'refund_granted',
    ]

    # 上方 search bar 
    search_fields = [
        'user__username',
        'ref_code',
    ]

    # 加入 退款許可功能
    actions = [make_refund_accepted]


# 確認 address 狀態
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default',
    ]

    list_filter = [
        'default',
        'address_type',
        'country',
    ]

    search_fields = [
        'user',
        'street_address',
        'apartment_address',
        'zip',
    ]


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)
admin.site.register(UserProfile)