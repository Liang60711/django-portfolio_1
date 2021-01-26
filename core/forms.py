from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget    # country style


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal'),
)


class CheckoutForm(forms.Form):
    # shipping address
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)

    # https://github.com/SmileyChris/django-countries
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=False, 
        widget=CountrySelectWidget(attrs={'class': 'custom-select d-block w-100',})
    )
    shipping_zip = forms.CharField(required=False)

    # billing address
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)

    billing_country = CountryField(blank_label='(select country)').formfield(
        required=False, 
        widget=CountrySelectWidget(attrs={'class': 'custom-select d-block w-100',})
    )
    billing_zip = forms.CharField(required=False)

    # 勾選地址選項
    same_as_shipping_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    # 勾選付款方式
    payment_option = forms.ChoiceField(widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)



# Coupon form
class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


# Refund form
class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)