from django import forms
from .models import CartItem, WishlistItem


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
    def __init__(self, *args, **kwargs):
        super(CartItemForm, self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(CartItemForm, self).clean()
        quantity = cleaned_data.get('quantity')


class WishlistItemForm(forms.ModelForm):
    class Meta:
        model = WishlistItem
        fields = ['quantity']
    def __init__(self, *args, **kwargs):
        super(WishlistItemForm, self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(WishlistItemForm, self).clean()
        quantity = cleaned_data.get('quantity')
