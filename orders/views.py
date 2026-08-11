from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from shop.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from carts.utils.omnisend import send_contact



def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

from django.contrib.auth.models import AnonymousUser
import datetime
from decimal import Decimal  # Import Decimal


from decimal import Decimal
import datetime

def place_order(request):
    current_user = request.user if request.user.is_authenticated else None

    # Fetch cart items for the current user or guest
    cart_items = CartItem.objects.filter(user=current_user)
    if not cart_items.exists():
        return redirect('home')

    # Initialize totals
    total = Decimal(0)
    quantity = 0
    tax = Decimal(0)

    # Get selected shipping from POST request (default to 8 GEL for Tbilisi)
    selected_shipping = request.POST.get('shipping', '8')
    shipping = Decimal(selected_shipping)

    # Calculate total and quantity
    for cart_item in cart_items:
        price = cart_item.price if cart_item.price is not None else cart_item.product.price
        total += Decimal(str(price)) * cart_item.quantity
        quantity += cart_item.quantity

    # Compute final grand total
    grand_total = total + shipping

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Create Order instance
            data = Order(
                user=current_user,
                first_name=form.cleaned_data['first_name'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                address_line_1=form.cleaned_data['address_line_1'],
                city=form.cleaned_data['city'],
                order_note=form.cleaned_data['order_note'],
                order_total=grand_total,
                tax=tax,
                shipping_price=shipping,  # Store the selected shipping cost
                ip=request.META.get('REMOTE_ADDR'),
            )
            data.save()
            send_contact(form.cleaned_data['email'], first_name=form.cleaned_data['first_name'], last_name=form.cleaned_data['last_name'])

            # Generate order number
            current_date = datetime.date.today().strftime("%Y%m%d")
            data.order_number = f"{current_date}{data.id}"
            data.save()

            # Create OrderProduct instances
            ordered_products = []
            for item in cart_items:
                product_price = item.price if item.price is not None else item.product.price

                order_product = OrderProduct.objects.create(
                    order=data,
                    user=current_user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=Decimal(str(product_price)),
                    color=item.variations.filter(color__isnull=False).first().color.title if item.variations.filter(color__isnull=False).exists() else '',
                    size=item.variations.filter(size__isnull=False).first().size.title if item.variations.filter(size__isnull=False).exists() else '',
                    ordered=False
                )

                ordered_products.append(order_product)
                item.product.stock -= item.quantity
                item.product.save()

            # Clear cart after order is placed
            cart_items.delete()

            context = {
                'order': data,
                'cart_items': cart_items,
                'total': total,
                'shipping': shipping,
                'grand_total': grand_total,
                'ordered_products': ordered_products,
            }
            return render(request, 'shop/submit_order.html', context)

    return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    # transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:

            subtotal += i.product_price * i.quantity

        # payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            # 'transID': payment.payment_id,
            # 'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Order.DoesNotExist):
        return redirect('home')
