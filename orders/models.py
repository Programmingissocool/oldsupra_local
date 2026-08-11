from django.db import models
from accounts.models import Account
from shop.models import Product, Variation
import random
import string
from django.db.models import JSONField


class UniquePNumberField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)  # Set maximum length for the field
        kwargs.setdefault('unique', True)     # Ensure uniqueness
        kwargs.setdefault('editable', False)  # Prevent manual editing
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        # If the field is already populated, don't generate a new value
        value = getattr(model_instance, self.attname)
        if value:
            return value

        # Generate a unique identifier starting with 'P'
        while True:
            random_part = ''.join(random.choices(string.digits, k=6))
            generated_value = f'P{random_part}'
            if not model_instance.__class__.objects.filter(**{self.name: generated_value}).exists():
                setattr(model_instance, self.attname, generated_value)
                return generated_value

        return super().pre_save(model_instance, add)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('process', 'Process')
    ]
    
    
    
    BANK = [
        ('bog', 'Bank Of Georgia'),
        ('tbc', 'TBC Bank'),
        ('flitt', 'Flitt'),
        ('tbc_loan', 'tbc_loan'),
        ('liberty', 'Liberty Bank')
    ]

    
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    p_number = UniquePNumberField()
    amount_paid = models.CharField(max_length=100) # this is the total amount paid
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    bank = models.CharField(max_length=10, choices=BANK, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bearer = models.CharField(max_length=1900, null=True, blank=True)
    products = models.CharField(max_length=1900, blank=True)
    cart_data = JSONField(null=True, blank=True)
    checkout_data = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    shipping_price = models.FloatField(default=8.00) 
    tax = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

    def __str__(self):
        return self.first_name


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=100, blank=True)  # New field for color
    size = models.CharField(max_length=100, blank=True)  # New field for size
    quantity = models.IntegerField()
    variation = models.ForeignKey(Variation, on_delete=models.SET_NULL, null=True, blank=True) 
    product_price = models.FloatField()
    ordered = models.BooleanField(default=True)
    gift = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.Product_name

    def product_total(self):
        return self.product_price * self.quantity

    def variation_image_url(self):
        if self.variation and self.variation.image:
            return self.variation.image.url
        return self.product.images.url 

