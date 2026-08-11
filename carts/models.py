from django.db import models
from shop.models import Product, Variation
from accounts.models import Account
from django.db.models import Sum



# Create your models here.

class Cart(models.Model):

    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)
    
    def get_total_price(self):
        total = sum(item.quantity * item.price for item in self.items.all())
        return total

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_gift = models.BooleanField(default=False)
    parent_item = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gift_items'
    )

    # session_key = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.price is None:
            self.price = self.product.price  # Assign product price if not set
        super(CartItem, self).save(*args, **kwargs)

    def get_unit_price(self):
        if self.is_gift:
            return 0
    
        variation = self.variations.first()
    
        if variation:
            return variation.get_price
    
        return self.product.get_price()


    def sub_total(self):
        return self.get_unit_price() * self.quantity



        
class Wishlist(models.Model):

    wishlist_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class WishlistItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart    = models.ForeignKey(Wishlist, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        if self.product.is_on_sale:
            return self.product.discount_price * self.quantity
        else:
            return self.product.price * self.quantity

    def __unicode__(self):
        return self.product
