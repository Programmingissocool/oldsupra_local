from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name','phone','city', 'email', 'address_line_1','country', 'order_note']
