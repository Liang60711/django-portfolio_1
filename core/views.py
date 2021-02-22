from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin   # class-base 的 login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile
from .forms import CheckoutForm, CouponForm, RefundForm, PaymentForm

import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Order 編號
def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
    # random.choices(sequence, weights=None, cum_weights=None, k=1) >>> 回傳list；參數 sequence 可放list, tuple, string，k為取幾次，weights為權重
    # string.ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
    # string.digits = '0123456789'


# check form if blank
def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

# checkout page
class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            # Order object
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()     # CheckoutForm object
            coupon = CouponForm()     # CouponForm object

            context = {
                'form': form,
                'order': order,
                'couponform': coupon,
                'DISPLAY_COUPON_FORM': True,    # 在 checkout.html 預設顯示，payment.html 預設不顯示
            }
            
            # shipping address
            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            ).order_by('-timestamp')    # use latest address
            if shipping_address_qs.exists():
                context.update({'default_shipping_address': shipping_address_qs[0]})

            # billing address
            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            ).order_by('-timestamp')
            if billing_address_qs.exists():
                context.update({'default_billing_address': billing_address_qs[0]})

            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active order.')
            return redirect('core:checkout')
            
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():

                # 勾選 use_default_shipping
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
            
                if use_default_shipping:
                    print('Using the default shipping')
                    
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs.last()
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, 'No default shipping address available')
                        return redirect('core:checkout')
                else:
                    print('User need to enter a new shipping address')

                    # save model Address
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        # 用 is_valid_form 檢查是否有空值
                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address1,
                            apartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip,
                            address_type = 'S',

                        )
                        shipping_address.save()

                        # create relationship
                        order.shipping_address = shipping_address
                        order.save()

                        # 勾選 set_default_shipping
                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, 'Please fill in the required shipping address fields')

                # 勾選 use_default_billing
                use_default_billing = form.cleaned_data.get('use_default_billing')
                # 勾選 same_as_shipping_address
                same_as_shipping_address = form.cleaned_data.get('same_as_shipping_address')
                if same_as_shipping_address:
                    billing_address = shipping_address
                    billing_address.pk = None   # 因為要複製 shipping_address 所以 pk=None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print('Using the default billing')
                    address_qs = Address.objects.filter(
                        user = self.request.user,
                        address_type = 'B',
                        default = True,
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, 'No default billing address available')
                        return redirect('core:checkout')
                else:
                    print('User need to enter a new billing address')

                    # save model Address
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        # 用 is_valid_form 檢查是否有空值
                        billing_address = Address(
                            user = self.request.user,
                            street_address = billing_address1,
                            apartment_address = billing_address2,
                            country = billing_country,
                            zip = billing_zip,
                            address_type = 'B',
                        )
                        billing_address.save()

                        # create relationship
                        order.billing_address = billing_address
                        order.save()

                        # 勾選 set_default_billing
                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, 'Please fill in the required billing address fields')


                #
                payment_option = form.cleaned_data.get('payment_option')


                # select payment option
                if payment_option == 'S':
                    return redirect('core:payment', payment_option='Stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='PayPal')
                else:
                    messages.warning(self.request, 'Invalid payment selection.')
                    return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order.')
            return redirect('core:order_summary')
            

# payment stripe
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,   # 在 checkout.html 預設顯示，payment.html 預設不顯示
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            
            # 使用預設 卡片
            if userprofile.one_click_purchasing:
                # 抓卡片資料
                cards = stripe.Customer.list_sources(
                    userprofile.stripe_customer_id,
                    limit=3,
                    object='card'
                )
                card_list = cards['data']
                if len(card_list) > 0:
                    context.update({
                        'card': card_list[0]
                    })
            return render(self.request, "payment.html", context)
        else:
            messages.warning(self.request, 'You have not added a billing address.')
            return redirect('core:checkout')

    def post(self, *args, **kwargs):
        order = Order.objects.get_or_create(user=self.request.user, ordered=False)[0]
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)

        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')    # function stripeTokenHandler(token)
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            # 勾選 Save for future purchases
            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(userprofile.stripe_customer_id)
                    customer.sources.create(source=token)
                
                else:
                    customer = stripe.Customer.create(email=self.request.user.email, source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()

            amount = int(order.get_total() * 100)           # cents

            try:
                if use_default or save:
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        customer=userprofile.stripe_customer_id
                    )
                else:
                    charge = stripe.Charge.create(
                        amount=amount,  # cents
                        currency="usd",
                        source=token
                    )

                # create payment
                payment = Payment()
                payment.stripe_charge_id = charge['id']
                payment.user = self.request.user
                payment.amount = order.get_total()
                payment.save()

                # 上一筆 Order 完成後()， OrderItem(cart) 裡面的內容應該要歸零
                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()
            
                # create relationship to order
                order.ordered = True    # order 成立
                order.payment = payment
                # create ref_code
                order.ref_code = create_ref_code()
                order.save()
                
                messages.success(self.request, 'Your order was successful.')
                return redirect('/')

            except stripe.error.CardError as e:
                # Since it's a decline, stripe.error.CardError will be caught
                body = e.json_body
                err = body.get('error', {})
                messages.warning(self.request, f"{err.get('message')}")
                return redirect('/')

            except stripe.error.RateLimitError as e:
                # Too many requests made to the API too quickly
                messages.warning(self.request, 'RateLimitError')
                return redirect('/')

            except stripe.error.InvalidRequestError as e:
                # Invalid parameters were supplied to Stripe's API
                messages.warning(self.request, 'InvalidRequestError')
                return redirect('/')

            except stripe.error.AuthenticationError as e:
                # Authentication with Stripe's API failed
                # (maybe you changed API keys recently)
                messages.warning(self.request, 'AuthenticationError')
                return redirect('/')

            except stripe.error.APIConnectionError as e:
                # Network communication with Stripe failed
                messages.warning(self.request, 'APIConnectionError')
                return redirect('/')

            except stripe.error.StripeError as e:
                # Display a very generic error to the user, and maybe send
                # yourself an email
                messages.warning(self.request, 'StripeError')
                return redirect('/')

            except Exception as e:
                # Something else happened, completely unrelated to Stripe
                messages.warning(self.request, 'Error')
                return redirect('/')
        
        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")


# homepage
class HomeView(ListView):
    model = Item
    paginate_by = 8     # 每頁顯示多少個list項目
    template_name = 'home.html'


# Order check page
class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *arg, **kwarg):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object':order,
            }
            return render(self.request, 'order_summary.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, 'You do not have an active order.')
            return redirect('/')
        

# product page (detail)
class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


# add to shopping cart
@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    
    # get_or_create return 'tuple'
    order_item = OrderItem.objects.get_or_create(
        user=request.user,
        item=item,
        ordered=False,
    )[0]
    
    # ordered=False: order has not complete
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    if order_qs.exists():   # check order exist 
        order = order_qs[0]

        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect('core:order_summary')
        else:
            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart.')
            return redirect('core:product', slug=slug)
    
    # not already have an order
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart.')
        return redirect('core:product', slug=slug)


# remove all item form shopping cart
@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                user=request.user,
                item=item,
                ordered=False,
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, 'This item was remove from your cart.')
            return redirect('core:order_summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('core:product', slug=slug)
    else:
        # add a message saying the user doesn't have an order
        messages.info(request, 'You do not have an active order.')
        return redirect('core:product', slug=slug)


# remove single item from shopping cart
@login_required
def remove_single_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
    )
    
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                user=request.user,
                item=item,
                ordered=False,
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, 'This item quantity was updated.')
            # no need slug = slug argument
            return redirect('core:order_summary')
        else:
            messages.info(request, 'This item was not in your cart.')
            return redirect('core:order_summary')
    else:
        # add a message saying the user doesn't have an order
        messages.info(request, 'You do not have an active order.')
        return redirect('core:order_summary')


# 獲得coupon
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        messages.success(request, 'Successfully added coupon.')
        return coupon

    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return None


# 輸入coupon
class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code=code)
                order.save()
                return redirect('core:checkout')

            except ObjectDoesNotExist:
                messages.info(self.request, 'You do not have an active order.')
                return redirect('core:checkout')
            except:
                messages.info(request, "This coupon does not exist")
                return redirect('core:checkout')
    

# 退款 refund
class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form,
        }
        return render(self.request, 'request_refund.html', context)
    
    
    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
                        
            try:
                # edit the order
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, 'Your request was received.')
                return redirect('core:request_refund')

            except ObjectDoesNotExist:
                messages.info(self.request, 'This order does not exist.')
                return redirect('core:request_refund')