from django.db.models.signals import post_save
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField


CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sport wear'),
    ('OW', 'Outwear'),
)


LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),
)


ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


# save credit card number
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username



# all items that can purchase
class Item(models.Model):
    title = models.CharField(max_length=25)
    price = models.PositiveIntegerField()
    discount_price = models.PositiveIntegerField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    description = models.TextField()
    slug = models.SlugField()
    image = models.ImageField(blank=True, null=True)     # pip install pillow

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('core:add_to_cart', kwargs={
            'slug': self.slug
        })
    def get_remove_from_cart_url(self):
        return reverse('core:remove_from_cart', kwargs={
            'slug': self.slug
        })     



# linking between 'Item', 'Order'
# as 'Item' added in shopping cart, it becomes 'OrderItem'
class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    
    ordered = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} of {self.item.title}'
    
    # order_summary total item price (not discount)
    def get_total_item_price(self):
        return self.quantity * self.item.price
    # order_summary total item price (discount)
    def get_total_item_discount_price(self):
        return self.quantity * self.item.discount_price
    # saved price
    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_item_discount_price()
    # final price (single item, not order final price)
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_item_discount_price()
        return self.get_total_item_price()


# shopping cart/order
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    # whether it has been ordered or not
    ordered = models.BooleanField(default=False)
    # 循環關係(cyclic)，models 要加括號，因為 model 尚未 defined
    # address
    billing_address = models.ForeignKey('Address', related_name='billing_address',
                                         on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey('Address', related_name='shipping_address',
                                        on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    # coupon
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    # refund
    being_delivered = models.BooleanField(default=False)    # 運送狀態
    received = models.BooleanField(default=False)           # 收貨狀態
    refund_requested = models.BooleanField(default=False)   # 退單需求
    refund_granted = models.BooleanField(default=False)     # 被核可的退單

    '''
    create Order 
    1. add to cart
    2. add a billing address
    3. payment
    4. being delivered
    5. received
    6. refunds**
    '''

    def __str__(self):
        return self.user.username
    
    # order final price
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        # coupon discount
        if self.coupon:
            total -= self.coupon.amount
        return total

# user 地址
class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=128)
    apartment_address = models.CharField(max_length=128)
    country = CountryField(multiple=False)
    # 郵遞區號
    zip = models.CharField(max_length=128)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    # 是否預設地址
    default = models.BooleanField(default=False)
    # 建立時間
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    # 更改 admin 左方 models 介面的名字
    class Meta:
        verbose_name_plural = 'Addresses'



# stripe 付款 單號
class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)   # SET_NULL 為 AUTH_USER_MODEL 刪除時，此 ForeignKey 設為 null
    amount = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# 折扣碼 Coupon
class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.PositiveIntegerField()
    
    def __str__(self):
        return self.code


# 退款 Refund
class Refund(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f'{self.pk}'


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)

post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
