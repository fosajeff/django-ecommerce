from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_OPTIONS = (
    ('S', 'Stripe'),
    ('P', 'PayPal')
)


class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'id': 'address',
        'class': 'form-control',
        'placeholder': '1234 Main St'
    }))
    appartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'id': 'address-2',
        'class': 'form-control',
        'placeholder': 'Apartment or suite'
    }))
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'id': 'country',
        'class': 'custom-select d-block w-100'
    }))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={
        'id': 'zip',
        'class': 'form-control'
    }))
    same_shipping_address = forms.BooleanField(required=False)
    save_info = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={
            'name': 'paymentMethod',
            'class': 'custom-control-input'
        }), choices=PAYMENT_OPTIONS)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': "Recipient's username",
        'aria-describedby': 'basic-addon2'
    }))
