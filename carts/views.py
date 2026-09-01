from django.conf import settings
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import Product, Variation, Category
from .models import Cart, CartItem, Wishlist, WishlistItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from .forms import CartItemForm, WishlistItemForm
from django.contrib import messages
from django.http import JsonResponse
import requests
import json
from orders.models import Payment
from django.db.models import Sum
from .utils.omnisend import send_contact, send_cart_event, send_cart_event_beta, send_placed_order_event
from django.template.loader import render_to_string
from django.core.mail import send_mail
from orders.models import Order, OrderProduct
from django.urls import reverse
from django.templatetags.static import static
from hashlib import sha1
import hashlib
import time
import random


from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import translation


def _send_customer_order_email(request, order, ordered_products, total, grand_total, shipping):
    language_code = getattr(request, "LANGUAGE_CODE", None) or "ka"
    language_code = "en" if language_code.startswith("en") else "ka"

    logo_url = request.build_absolute_uri(static("assets/img/suprawhite.svg"))
    payment_number = getattr(getattr(order, "payment", None), "p_number", "")
    order_url = request.build_absolute_uri(
        f"/{language_code}/carts/payment_check/?id={payment_number}"
    ) if payment_number else ""
    context = {
        "order": order,
        "ordered_products": ordered_products,
        "total": total,
        "grand_total": grand_total,
        "shipping": shipping,
        "current_year": datetime.datetime.now().year,
        "email_language": language_code,
        "logo_url": logo_url,
        "order_url": order_url,
    }

    subject = (
        f"Order Confirmation - {order.order_number}"
        if language_code == "en"
        else f"შეკვეთის დადასტურება - {order.order_number}"
    )

    with translation.override(language_code):
        body = render_to_string(
            "shop/customer_new_order_notification.html",
            context,
            request=request,
        )

    send_mail(
        subject=subject,
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=body,
        fail_silently=False,
    )

@require_POST
def cart_recalculate(request):
    user = request.user

    cart_items = CartItem.objects.filter(user=user, is_active=True)

    shipping = Decimal(request.POST.get("shipping", 0))
    voucher_code = (request.POST.get("voucher_code") or "").lower()

    cart_total = Decimal("0")

    items_data = []

    for item in cart_items:
        unit_price = item.get_unit_price()
        subtotal = Decimal(unit_price) * item.quantity
        cart_total += subtotal

        items_data.append({
            "id": item.id,
            "quantity": item.quantity,
            "subtotal": float(subtotal)
        })

    discount = Decimal("0")

    if voucher_code == "sale5" and cart_total > 50:
        discount = cart_total * Decimal("0.05")

    elif voucher_code == "sale10" and cart_total > 50:
        discount = cart_total * Decimal("0.10")

    elif voucher_code == "sale15" and cart_total > 50:
        discount = cart_total * Decimal("0.15")

    # free shipping voucher
    if voucher_code == "since1998" and cart_total > 50:
        shipping = Decimal("0")

    grand_total = cart_total - discount + shipping

    return JsonResponse({
        "success": True,
        "cart_total": float(cart_total),
        "shipping": float(shipping),
        "discount": float(discount),
        "grand_total": float(grand_total),
        "items": items_data,
        "voucher_message": {
            "text": "OK",
            "color": "green"
        } if voucher_code else None
    })



def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()



# Create your views here.
from django.http import HttpResponse


def _wishlist_id(request):
    wishlist = request.session.session_key
    if not wishlist:
        # session.create() returns None; it sets session_key as a side effect.
        request.session.create()
        wishlist = request.session.session_key
    return wishlist

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        # session.create() returns None; it sets session_key as a side effect.
        # Returning its result put NULL into carts_cart.cart_id and raised
        # IntegrityError for every visitor without an existing session.
        request.session.create()
        cart = request.session.session_key
    return cart

def add_wishlist(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id) #get the product
    form = WishlistItemForm(request.POST)
    # If the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass


        is_wishlist_item_exists = WishlistItem.objects.filter(product=product, user=current_user).exists()
        if is_wishlist_item_exists:
            wishlist_item = CartItem.objects.get(product=product, user=current_user)
            wishlist_item.quantity += 1
            wishlist_item.save()

        else:
            wishlist_item = WishlistItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user,
            )

        return redirect(request.META.get('HTTP_REFERER') + '?item_added=true')
    # If the user is not authenticated
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass


        try:
            wishlist = Wishlist.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the session
        except Wishlist.DoesNotExist:
            wishlist = Wishlist.objects.create(
                wishlist_id = _wishlist_id(request)
            )
        wishlist.save()

        is_wishlist_item_exists = WishlistItem.objects.filter(product=product, cart=cart).exists()
        if is_wishlist_item_exists:
            wishlist_item = CartItem.objects.get(product=product, cart=cart)
            wishlist_item.quantity += 1
            wishlist_item.save()

        else:
            wishlist_item = WishlistItem.objects.create(
                product = product,
                quantity = int(request.POST['quantity']),
                wishlist = wishlist,
            )
            if len(product_variation) > 0:
                wishlist_item.variations.clear()
                wishlist_item.variations.add(*product_variation)
            wishlist_item.save()
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))




def wishlist(request, total=0, quantity=0, shipping=0,wishlist_item_total = 0, wishlist_items=None):
    try:
        total = 0
        grand_total = 0
        shipping = 0
        wishlist_item_total = 0
        if request.user.is_authenticated:
            wishlist_items = WishlistItem.objects.filter(user=request.user, is_active=True)
        else:
            wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
            wishlist_items = WishlistItem.objects.filter(wishlist=wishlist, is_active=True)
        for wishlist_item in wishlist_items:
            if wishlist_item.product.is_on_sale:
                total += (wishlist_item.product.discount_price * wishlist_item.quantity)
                quantity += wishlist_item.quantity

            else:
                total += (wishlist_item.product.price * wishlist_item.quantity)
                quantity += wishlist_item.quantity


        if total <= 50 or total ==0:
            shipping += 50
        else:
            shipping == 0

        grand_total = total + shipping
    except ObjectDoesNotExist:
        pass #just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'wishlist_items': wishlist_items,
        'grand_total': grand_total,
        'shipping': shipping,
    }
    return render(request, 'shop/wishlist.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from shop.models import Product, Variation
from .models import Cart, CartItem
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string

def get_effective_price(product, variation=None):
    if variation:
        return variation.discount_price if product.is_on_sale and variation.discount_price else variation.price
    return product.discount_price if product.is_on_sale and product.discount_price else product.price


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    quantity = int(request.POST.get('quantity', '1'))
    product_variation = []

    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    def get_effective_price(product, variation=None):
        if variation:
            return variation.discount_price if product.is_on_sale and variation.discount_price else variation.price
        return product.discount_price if product.is_on_sale and product.discount_price else product.price

    selected_variation = product_variation[0] if product_variation else None
    price = get_effective_price(product, selected_variation)

    if current_user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        send_contact(request.user.email, request.user.first_name, request.user.last_name)

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, user=current_user)
            cart_item.quantity += quantity
            cart_item.price = price  # ✅ Assign the updated price
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=quantity,
                user=current_user,
                price=price  # ✅ Assign the effective price here
            )
            if product_variation:
                cart_item.variations.set(product_variation)
            cart_item.save()



        cart_items = CartItem.objects.filter(user=current_user)
        cart_items_html = render_to_string('cart/cart_items.html', {'cart_items_cart': cart_items})

        grand_total = sum(
            item.quantity * get_effective_price(item.product, item.variations.first() if item.variations.exists() else None)
            for item in cart_items
        )

        return JsonResponse({
            'cart_item_count': cart_items.count(),
            'cart_items_html': cart_items_html,
            'grand_total': grand_total
        })




    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            cart_item.quantity += quantity
            cart_item.price = price  # ✅ Update price here too
            cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=quantity,
                cart=cart,
                price=price  # ✅ Save correct price
            )
            if product_variation:
                cart_item.variations.set(product_variation)
            cart_item.save()

        cart_items = CartItem.objects.filter(cart=cart)
        cart_items_html = render_to_string('includes/mini_cart_items.html', {'cart_items_cart': cart_items})

        grand_total = sum(
            item.quantity * get_effective_price(item.product, item.variations.first() if item.variations.exists() else None)
            for item in cart_items
        )

        return JsonResponse({
            'cart_item_count': cart_items.count(),
            'cart_items_html': cart_items_html,
            'grand_total': grand_total
        })





def add_cart_main(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    cart = None

    if not current_user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    if request.method == 'POST':
        color_id = request.POST.get('color_id')
        size_id = request.POST.get('size_id')
        quantity = int(request.POST.get('quantity', 1))

        variation = None
        if color_id and size_id:
            variation = Variation.objects.filter(product=product, color_id=color_id, size_id=size_id).first()
            if not variation:
                messages.error(request, "Selected variation does not exist.")
                return redirect(request.META.get('HTTP_REFERER', 'cart'))

        price = get_effective_price(product, variation)

        if current_user.is_authenticated:
            cart_item_qs = CartItem.objects.filter(product=product, user=current_user)
        else:
            cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

        if variation:
            cart_item_qs = cart_item_qs.filter(variations=variation)

        if cart_item_qs.exists():
            cart_item = cart_item_qs.first()
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                product=product,
                user=current_user if current_user.is_authenticated else None,
                cart=cart if not current_user.is_authenticated else None,
                quantity=quantity,
                price=price
            )
            cart_item.save()
            if variation:
                cart_item.variations.add(variation)

        cart_item.save()
        messages.success(request, "Item added to cart successfully.")

        if current_user.is_authenticated:
            send_cart_event_beta(
                user_email=current_user.email,
                cart_item=cart_item
            )

        return redirect(request.META.get('HTTP_REFERER', '/') + f'?item_added=true&pid={product.id}')

    messages.warning(request, "Invalid request method.")
    return redirect(request.META.get('HTTP_REFERER', '/') + f'?item_added=true&pid={product.id}')

def add_cart_main_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    cart = None

    if not current_user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    if request.method == 'POST':
        color_id = request.POST.get('color_id_new')
        size_id = request.POST.get('size_id_new')
        quantity = int(request.POST.get('quantity', 1))

        variation = None
        if color_id and size_id:
            variation = Variation.objects.filter(product=product, color_id=color_id, size_id=size_id).first()
            if not variation:
                messages.error(request, "Selected variation does not exist.")
                return redirect(request.META.get('HTTP_REFERER', 'cart'))

        price = get_effective_price(product, variation)

        if current_user.is_authenticated:
            cart_item_qs = CartItem.objects.filter(product=product, user=current_user)
        else:
            cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

        if variation:
            cart_item_qs = cart_item_qs.filter(variations=variation)

        if cart_item_qs.exists():
            cart_item = cart_item_qs.first()
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                product=product,
                user=current_user if current_user.is_authenticated else None,
                cart=cart if not current_user.is_authenticated else None,
                quantity=quantity,
                price=price
            )
            cart_item.save()
            if variation:
                cart_item.variations.add(variation)

        cart_item.save()
        messages.success(request, "Item added to cart successfully.")

        # 🔔 Omnisend event trigger for authenticated users
        if current_user.is_authenticated:
            send_cart_event_beta(
                user_email=current_user.email,
                cart_item=cart_item
            )

        return redirect(reverse('cartcheck') + f'?item_added=true&pid={product.id}')

    messages.warning(request, "Invalid request method.")
    return redirect(reverse('cartcheck') + f'?item_added=true&pid={product.id}')



def add_cart_main_cartcheck(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)

    print("Request Method:", request.method)
    print("POST Data:", request.POST)

    cart = None
    if not current_user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    if request.method == 'POST':
        # Use updated field names
        color_id = request.POST.get('buy_color_id')
        size_id = request.POST.get('buy_size_id')
        quantity = int(request.POST.get('quantity', 1))

        print("Selected Color ID:", color_id)
        print("Selected Size ID:", size_id)
        print("Quantity:", quantity)

        variation = None
        price = product.price  # Default to base price

        if color_id and size_id:
            variation = Variation.objects.filter(
                product=product, color_id=color_id, size_id=size_id
            ).first()
            if variation:
                print("Variation found:", variation)
                price = variation.price
            else:
                print("Variation not found.")
                messages.error(request, "Selected variation does not exist.")
                return redirect('cartcheck')
        else:
            print("No variation selected. Using default price.")

        # Get or create cart item
        if current_user.is_authenticated:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
        else:
            cart_item = CartItem.objects.filter(product=product, cart=cart)

        if variation:
            cart_item = cart_item.filter(variations=variation)

        if cart_item.exists():
            cart_item = cart_item.first()
            cart_item.quantity += quantity
            cart_item.save()
            print("Cart item updated. New quantity:", cart_item.quantity)
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=quantity,
                user=current_user if current_user.is_authenticated else None,
                cart=cart if not current_user.is_authenticated else None,
                price=price
            )
            if variation:
                cart_item.variations.add(variation)
                print("Variation added to cart item.")
            cart_item.save()
            print("New cart item created.")

        if current_user.is_authenticated:
            send_contact(request.user.email, request.user.first_name, request.user.last_name)

        messages.success(request, "Item added to cart successfully.")
        return redirect('cartcheck')

    print("Invalid request method.")
    messages.warning(request, "Invalid request method.")
    return redirect('cartcheck')


def add_cart_new(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', '1'))
    product_variation = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # Pricing logic
    def get_effective_price(product, variation=None):
        if variation:
            return variation.discount_price if product.is_on_sale and variation.discount_price else variation.price
        return product.discount_price if product.is_on_sale and product.discount_price else product.price

    # Get cart & cart_item
    if current_user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_item, created = CartItem.objects.get_or_create(
            product=product,
            user=current_user,
            cart=cart
        )
    else:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_item, created = CartItem.objects.get_or_create(
            product=product,
            cart=cart
        )

    # Update or create cart item
    if created:
        selected_variation = product_variation[0] if product_variation else None
        cart_item.price = get_effective_price(product, selected_variation)
        cart_item.quantity = quantity
        cart_item.save()
        if product_variation:
            cart_item.variations.set(product_variation)
    else:
        cart_item.quantity += quantity
        cart_item.save()

    # Build products payload using cartitem_set
    products_payload = []
    for item in cart.cartitem_set.all():  # FIXED: no .items
        products_payload.append({
            "cartProductID": str(item.id),
            "productID": str(item.product.id),
            "variantID": str(item.variations.first().id) if item.variations.exists() else None,
            "title": item.product.Product_name,
            "quantity": item.quantity,
            "price": float(item.price or item.product.price)
        })

    # Send event to Omnisend
    send_cart_event(
        email=current_user.email if current_user.is_authenticated else None,
        cart_id=cart.id,
        products=products_payload,
        phone=getattr(current_user, "phone_number", None) if current_user.is_authenticated else None
    )

    messages.success(request, "Item added to cart successfully.")
    return redirect('cart')



def remove_cart(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')



def add_cart_main_cartcheck(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)

    print("Request Method:", request.method)
    print("POST Data:", request.POST)

    cart = None
    if not current_user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(cart_id=_cart_id(request))

    if request.method == 'POST':
        color_id = request.POST.get('color_id')
        size_id = request.POST.get('size_id')
        print("Selected Color ID:", color_id)
        print("Selected Size ID:", size_id)

        variation = None
        if color_id and size_id:
            variation = Variation.objects.filter(product=product, color_id=color_id, size_id=size_id).first()
            if not variation:
                print("Variation does not exist.")
                messages.error(request, "Selected variation does not exist.")
                return redirect('cartcheck')
            price = variation.price
        else:
            print("No variation selected. Using base product price.")
            price = product.price

        if current_user.is_authenticated:
            cart_item = CartItem.objects.filter(product=product, user=current_user, variations=variation).first()
        else:
            cart_item = CartItem.objects.filter(product=product, cart=cart, variations=variation).first()

        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
            print("Cart item updated. Quantity:", cart_item.quantity)
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user if current_user.is_authenticated else None,
                cart=cart if not current_user.is_authenticated else None,
                price=price,
            )
            if variation:
                cart_item.variations.add(variation)
            cart_item.save()
            print("New cart item created with ID:", cart_item.id)

        messages.success(request, "Item added to cart successfully.")
        return redirect('cartcheck')

    print("Invalid request method. Redirecting to cart.")
    messages.warning(request, "Invalid request method. Redirecting to cart.")
    return redirect('cartcheck')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')



from django.template.loader import render_to_string

def remove_cart_item_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product,
                user=request.user,
                id=cart_item_id
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(
                product=product,
                cart=cart,
                id=cart_item_id
            )

        cart_item.delete()

        # Refresh cart data
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        grand_total = 0
        cart_count = 0

        for item in cart_items:
            grand_total += item.sub_total()
            cart_count += item.quantity

        cart_items_html = render_to_string(
            'includes/mini_cart_items.html',
            {
                'cart_items_cart': cart_items
            },
            request=request
        )

        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'grand_total': grand_total,
            'cart_items_html': cart_items_html
        })

    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False
        })


from django.core.exceptions import ObjectDoesNotExist




def is_promotion_eligible(cart_item):
    return (
        cart_item.product.category.promotion is True
    )


from decimal import Decimal, ROUND_HALF_UP

from django.db.models import F, Case, When, FloatField, Value

def get_effective_price_expression():
    return Case(
        When(
            is_on_sale=True,
            discount_price__gt=0,
            then=F('discount_price')
        ),
        default=F('price'),
        output_field=FloatField()
    )


def get_gift_candidates(cart_item):

    variation = (
        cart_item.variations.first()
        if cart_item.variations.exists()
        else None
    )

    base_price = get_effective_price(cart_item.product, variation)

    qs = Product.objects.annotate(
        effective_price=get_effective_price_expression()
    ).filter(
        is_availiable=True,
        effective_price__lte=base_price   # ✅ TRUE PRICE LOGIC
    )

    return qs.only(
        'id',
        'Product_name',
        'price',
        'discount_price',
        'images'
    ).order_by('-effective_price')[:30]



def cart(request):

    cats = Category.objects.all()

    # -----------------------------
    # CART LOAD
    # -----------------------------
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('product', 'product__category').prefetch_related('variations')
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = None
            cart_items = []
        else:
            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            ).select_related('product', 'product__category').prefetch_related('variations')

    # -----------------------------
    # INPUTS (DO NOT TRUST FRONTEND FULLY)
    # -----------------------------
    shipping = int(request.GET.get('shipping', 0))
    voucher_code = request.GET.get('voucher', '').strip().lower()

    # -----------------------------
    # CALCULATIONS
    # -----------------------------
    total = 0
    quantity = 0
    discount = 0

    # promo rules
    valid_vouchers = ["since1998", "sale5", "sale10", "sale15"]

    for item in cart_items:

        variation = item.variations.first() if item.variations.exists() else None
        price = get_effective_price(item.product, variation)

        # promo logic
        item.is_promo_eligible = is_promotion_eligible(item)
        item.gift_candidates = (
            get_gift_candidates(item)
            if item.is_promo_eligible and not item.is_gift
            else []
        )

        # subtotal
        if item.is_gift:
            item.subtotal = 0
        else:
            item.subtotal = price * item.quantity
            total += item.subtotal

        quantity += item.quantity

    # -----------------------------
    # VOUCHER LOGIC (SERVER SIDE ONLY)
    # -----------------------------
    # Free shipping for orders over 100
    if total > 100:

        shipping = 0

    elif voucher_code in valid_vouchers and total > 50:

        if voucher_code == "since1998":
            shipping = 0

        elif voucher_code == "sale5":
            discount = total * 0.05

        elif voucher_code == "sale10":
            discount = total * 0.10

        elif voucher_code == "sale15":
            discount = total * 0.15

    else:
        voucher_code = ""  # invalid reset

    # -----------------------------
    # FINAL TOTAL
    # -----------------------------
    grand_total = total - discount + shipping

    # -----------------------------
    # CONTEXT
    # -----------------------------
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'cats': cats,

        # totals
        'total': total,
        'discount': discount,
        'shipping': shipping,
        'grand_total': grand_total,
        'quantity': quantity,

        # voucher
        'voucher_code': voucher_code,
    })



def cartcheck(
    request,
    total=0,
    quantity=0,
    shipping=0,
    cart_item_total=0,
    cart_items=None
):

    try:

        total = 0
        grand_total = 0
        cart_item_total = 0

        shipping = int(
            request.GET.get('shipping', 0)
        )

        cats = Category.objects.all()

        if request.user.is_authenticated:

            cart_items = CartItem.objects.filter(
                user=request.user,
                is_active=True
            ).select_related(
                'product',
                'product__category'
            ).prefetch_related(
                'variations'
            )

        else:

            cart = Cart.objects.get(
                cart_id=_cart_id(request)
            )

            cart_items = CartItem.objects.filter(
                cart=cart,
                is_active=True
            ).select_related(
                'product',
                'product__category'
            ).prefetch_related(
                'variations'
            )

        for cart_item in cart_items:

            variation = (
                cart_item.variations.first()
                if cart_item.variations.exists()
                else None
            )

            price = get_effective_price(
                cart_item.product,
                variation
            )

            cart_item.is_promo_eligible = (
                is_promotion_eligible(cart_item)
            )

            if (
                cart_item.is_promo_eligible
                and not cart_item.is_gift
            ):

                cart_item.gift_candidates = (
                    get_gift_candidates(cart_item)
                )

            else:

                cart_item.gift_candidates = []

            if cart_item.is_gift:

                cart_item.subtotal = 0

            else:

                cart_item.subtotal = (
                    price * cart_item.quantity
                )

                total += cart_item.subtotal

            quantity += cart_item.quantity

        grand_total = total + shipping

    except ObjectDoesNotExist:

        cart_items = []

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'shipping': shipping,
        'cats': cats,
    }

    return render(
        request,
        'cart.html',
        context
    )

def add_gift_product(request, cart_item_id, product_id):

    try:

        # AUTH USER
        if request.user.is_authenticated:

            parent_item = get_object_or_404(
                CartItem,
                id=cart_item_id,
                user=request.user,
                is_active=True
            )

        # GUEST USER
        else:

            cart = get_object_or_404(
                Cart,
                cart_id=_cart_id(request)
            )

            parent_item = get_object_or_404(
                CartItem,
                id=cart_item_id,
                cart=cart,
                is_active=True
            )

        # PROMOTION CHECK
        if not parent_item.product.category.promotion:

            return JsonResponse({
                'success': False,
                'message': 'Promotion inactive'
            })

        # PARENT PRICE
        parent_variation = (
            parent_item.variations.first()
            if parent_item.variations.exists()
            else None
        )

        parent_price = get_effective_price(
            parent_item.product,
            parent_variation
        )

        # GIFT PRODUCT
        gift_product = get_object_or_404(
            Product,
            id=product_id,
            is_availiable=True
        )

        gift_variation = None

        gift_price = gift_product.price

        try:

            gift_price = get_effective_price(
                gift_product,
                gift_variation
            )

        except Exception as e:

            print('GIFT PRICE FALLBACK:', str(e))

            gift_price = gift_product.price

        # PRICE VALIDATION
        if gift_price > parent_price:

            return JsonResponse({
                'success': False,
                'message': 'Gift too expensive'
            })

        # REMOVE OLD GIFT
        CartItem.objects.filter(
            parent_item=parent_item,
            is_gift=True
        ).delete()

        # CREATE NEW GIFT
        if request.user.is_authenticated:

            CartItem.objects.create(
                user=request.user,
                product=gift_product,
                quantity=1,
                is_gift=True,
                parent_item=parent_item,
                is_active=True
            )

        else:

            CartItem.objects.create(
                cart=cart,
                product=gift_product,
                quantity=1,
                is_gift=True,
                parent_item=parent_item,
                is_active=True
            )

        return JsonResponse({
            'success': True
        })

    except Exception as e:

        return JsonResponse({
            'success': False,
            'message': str(e)
        })

# def cart(request, total=0, quantity=0, shipping=0, cart_item_total=0, cart_items=None):
#     try:
#         total = 0
#         grand_total = 0
#         cats = Category.objects.all()
#         shipping = int(request.GET.get('shipping', 0))

#         if request.user.is_authenticated:
#             cart_items = CartItem.objects.filter(user=request.user, is_active=True)
#         else:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_items = CartItem.objects.filter(cart=cart, is_active=True)

#         for item in cart_items:
#             variation = item.variations.first() if item.variations.exists() else None
#             price = get_effective_price(item.product, variation)
#             item.subtotal = price * item.quantity  # Add subtotal to each cart_item
#             total += item.subtotal
#             quantity += item.quantity

#         grand_total = total + shipping

#     except ObjectDoesNotExist:
#         cart_items = []

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'grand_total': grand_total,
#         'shipping': shipping,
#         'cats': cats,
#     }
#     return render(request, 'cart.html', context)



# def cartcheck(request, total=0, quantity=0, shipping=0, cart_item_total=0, cart_items=None):
#     try:
#         total = 0
#         grand_total = 0
#         shipping = int(request.GET.get('shipping', 0))
#         cats = Category.objects.all()
#         cart_item_total = 0

#         if request.user.is_authenticated:
#             cart_items = CartItem.objects.filter(user=request.user, is_active=True)
#         else:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_items = CartItem.objects.filter(cart=cart, is_active=True)

#         for cart_item in cart_items:
#             variation = cart_item.variations.first() if cart_item.variations.exists() else None
#             price = get_effective_price(cart_item.product, variation)
#             total += price * cart_item.quantity
#             quantity += cart_item.quantity


#         grand_total = total + shipping

#     except ObjectDoesNotExist:
#         pass

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'grand_total': grand_total,
#         'shipping': shipping,
#         'cats': cats,
#     }
#     return render(request, 'checkoutcart.html', context)



from decimal import Decimal
import json
import datetime
from requests.auth import HTTPBasicAuth




from decimal import Decimal, ROUND_HALF_UP
import json
import datetime

import hashlib
from django.http import HttpResponse
from django.utils.html import escape



def payge_amount_gel_to_tetri(amount_gel: str) -> int:
    """Convert GEL decimal string to tetri (integer)"""
    return int((Decimal(amount_gel).quantize(Decimal("0.01"))) * 100)


def payge_amount_tetri(amount_gel_str: str) -> int:
    d = Decimal(amount_gel_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(d * 100)

def payge_check(password: str, params: dict) -> str:
    # SHA256(password + merchant + ordercode + amount + currency + description + clientname + customdata + lng + testmode + ispreauth)
    # per spec. ([cdn.lb.ge](https://cdn.lb.ge/pay/temp/4b50f7e7b0824850a563d88ac5aecdfa.pdf))
    s = (
        password
        + params.get("merchant", "")
        + params.get("ordercode", "")
        + str(params.get("amount", ""))
        + params.get("currency", "")
        + params.get("description", "")
        + params.get("clientname", "")
        + params.get("customdata", "")
        + params.get("lng", "")
        + params.get("ispreauth", "")
    )
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def html_autopost_form(action_url: str, fields: dict) -> HttpResponse:
    inputs = "\n".join(
        f'<input type="hidden" name="{escape(str(k))}" value="{escape(str(v))}"/>'
        for k, v in fields.items()
        if v is not None
    )
    html = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Redirecting…</title></head>
<body>
<form id="payForm" method="post" action="{escape(action_url)}">
{inputs}
<noscript><button type="submit">Continue</button></noscript>
</form>
<script>document.getElementById('payForm').submit();</script>
</body>
</html>"""
    return HttpResponse(html)

def checkout_generate(request):
    requested_bank = request.GET.get("bank")
    voucher_code = request.GET.get("voucher", "").strip().lower()

    def generate_flitt_signature(payment_key, amount, currency, merchant_id, order_desc, order_id, server_callback_url):
        """
        Generates a valid signature for Flitt API requests.
        """
        text = f"{payment_key}|{amount}|{currency}|{merchant_id}|{order_desc}|{order_id}|{server_callback_url}"
        return sha1(text.encode("utf-8")).hexdigest()

    def tbcgenerate():
        url = "https://api.tbcbank.ge/v1/tpay/access-token"
        payload = {
            "client_id": settings.TBC_CLIENT_ID,
            "client_secret": settings.TBC_CLIENT_SECRET,
        }
        headers = {
            "accept": "application/json",
            "apikey": settings.TBC_ACCESS_TOKEN_API_KEY,
            "content-type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=payload, headers=headers)
        response_dict = response.json()
        if "status" in response_dict and response_dict["status"] == 400:
            return render(request, 'payment_generate.html', {})
        return response_dict["access_token"]

    def boggenerate():
        client_id = settings.BOG_CLIENT_ID
        client_secret = settings.BOG_CLIENT_SECRET
        url = "https://oauth2.bog.ge/auth/realms/bog/protocol/openid-connect/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }
        response = requests.post(url, headers=headers, data=data, auth=HTTPBasicAuth(client_id, client_secret))
        if response.status_code == 200:
            return response.json()["access_token"]
        print("Failed to get token!")
        return None

    def create_flitt_checkout(payment_key, merchant_id, order_id, amount, currency, order_desc, server_callback_url):
        # 2.1. გენერაცია signature-ს
        signature = generate_flitt_signature(payment_key, amount, currency, merchant_id, order_desc, order_id, server_callback_url)
        print(signature)
        # 2.2. POST მონაცემების კონსტრუქცია
        data = {
            "request": {
                "server_callback_url": server_callback_url,
                "order_id": order_id,
                "currency": currency,
                "merchant_id": merchant_id,
                "order_desc": order_desc,
                "amount": amount,
                "signature": signature
            }
        }
        print(server_callback_url, "+++++++++++++++++++++++++++++++")
        # 2.3. Headers
        headers = {"Content-Type": "application/json"}

        # 2.4. POST მოთხოვნა Flitt API-ს
        url = "https://pay.flitt.com/api/checkout/url"
        response = requests.post(url, headers=headers, json=data)

        # 2.5. პასუხის ანალიზი
        if response.status_code == 200:
            resp_json = response.json().get("response", {})
            if resp_json.get("response_status") == "success":
                checkout_url = resp_json.get("checkout_url")
                payment_id = resp_json.get("payment_id")
                return {"checkout_url": checkout_url, "payment_id": payment_id}
            else:
                return {"error": resp_json}
        else:
            return {"error": f"HTTP {response.status_code}"}



    if requested_bank == "tbc":
        token = tbcgenerate()
    elif requested_bank == "bog":
        token = boggenerate()
    elif requested_bank == "flitt":
        token = ""
    elif requested_bank == "liberty":
        token = ""
    elif requested_bank == "tbc_installment":
        token = ""

    user = request.user if request.user.is_authenticated else None
    product_ids = request.GET.getlist("id")

    if user and user.is_authenticated:
        cart_items = CartItem.objects.filter(user=user, product_id__in=product_ids, is_active=True)
    else:
        cart_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart, product_id__in=product_ids, is_active=True)

    total = Decimal("0.00")
    for item in cart_items:
        unit_price = Decimal(item.get_unit_price())
        total += unit_price * item.quantity

    shipping_value = request.GET.get("checkout_shipping", "8")
    shipping = Decimal(shipping_value)

    voucher_code = request.GET.get('voucher', '').strip().lower()
    request.session['voucher_code'] = voucher_code

    discount = Decimal('0')

    if total > 100:
        shipping = 0
    elif voucher_code == "since1998" and total > 50:
        shipping = Decimal('0')
    elif total >= 50:
        if voucher_code == "sale5":
            discount = total * Decimal('0.05')
        elif voucher_code == "sale10":
            discount = total * Decimal('0.10')
        elif voucher_code == "sale15":
            discount = total * Decimal('0.15')

    total_after_discount = total - discount
    grand_total = total_after_discount + shipping
    payment_amount_str = format(grand_total, '.2f')

    paymentobj = Payment.objects.create(
        user=user,
        status='process',
        bearer=token,
        amount_paid=payment_amount_str,
        bank = (
            'tbc' if requested_bank == 'tbc'
            else 'bog' if requested_bank == 'bog'
            else 'flitt' if requested_bank == 'flitt'
            else 'liberty' if requested_bank == 'liberty'
            else 'tbc_loan' if requested_bank == 'tbc_installment'
            else None
        )
    )

    detailed_cart = []

    for item in cart_items:

        color_title = ''
        size_title = ''

        color_var = item.variations.filter(
            color__isnull=False
        ).first()

        if color_var and color_var.color:
            color_title = color_var.color.title

        size_var = item.variations.filter(
            size__isnull=False
        ).first()

        if size_var and size_var.size:
            size_title = size_var.size.title

        item_data = {

            "name": item.product.Product_name,

            "product_id": item.product.id,

            "quantity": item.quantity,

            # 🔥 ALWAYS USE NORMALIZED UNIT PRICE
            "price": str(item.get_unit_price()),

            # 🔥 IMPORTANT
            "gift": bool(item.is_gift),

            "variations": [

                {
                    "variation_category": "Color",
                    "variation_value": color_title
                },

                {
                    "variation_category": "Size",
                    "variation_value": size_title
                }

            ]
        }

        detailed_cart.append(item_data)

    paymentobj.products = ','.join(product_ids)
    paymentobj.cart_data = detailed_cart
    paymentobj.save()

    checkout_snapshot = {
        'first_name': request.GET.get('first_name', ''),
        'email': request.GET.get('email', ''),
        'phone': request.GET.get('phone', ''),
        'address_line_1': request.GET.get('address_line_1', ''),
        'city': request.GET.get('city', ''),
        'order_note': request.GET.get('order_note', ''),
        'shipping': str(shipping),
        'voucher_code': voucher_code,
    }

    paymentobj.checkout_data = json.dumps(checkout_snapshot)
    paymentobj.save(update_fields=["checkout_data"])

    # (Optional but fine to keep for redirect UX)
    request.session['order_form_data'] = checkout_snapshot



    redirect_url = ""
    base_url = request.build_absolute_uri('/').rstrip('/')

    def sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


    if requested_bank == "tbc":
        payload = {
            "amount": {
                "currency": "GEL",
                "total": payment_amount_str,
            },
            "returnurl": f"{base_url}/{request.LANGUAGE_CODE}/carts/payment_check/?id={paymentobj.p_number}",
            "callbackUrl": f"{base_url}/{request.LANGUAGE_CODE}/carts/payment_check/?id={paymentobj.p_number}",
            "extra": "GE55TB7881436020100013",
            "expirationMinutes": 12,
            "methods": [5],
            "preAuth": False,
            "merchantPaymentId": paymentobj.p_number,
            "saveCard": False
        }

        headers = {
            "accept": "application/json",
            "apikey": settings.TBC_PAYMENTS_API_KEY,
            "content-type": "application/json",
            "authorization": f"Bearer {token}"
        }

        url = 'https://api.tbcbank.ge/v1/tpay/payments'
        response = requests.post(url, json=payload, headers=headers)
        resp_text = response.json()
        redirect_url = resp_text['links'][1]['uri']
        paymentobj.payment_id = resp_text['payId']
        paymentobj.save()

    elif requested_bank == "bog":
        url = "https://api.bog.ge/payments/v1/ecommerce/orders"
        headers = {
            "Accept-Language": "ka",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "callback_url": f"{base_url}/en/carts/check_bog_callback/",
            "external_order_id": paymentobj.p_number,
            "purchase_units": {
                "currency": "GEL",
                "total_amount": payment_amount_str,
                "basket": [
                    {
                        "quantity": 1,
                        "unit_price": payment_amount_str,
                        "product_id": "BOG Service"
                    }
                ]
            },
            "redirect_urls": {
                "fail": f"{base_url}/{request.LANGUAGE_CODE}/carts/payment_check/?id={paymentobj.p_number}",
                "success": f"{base_url}/{request.LANGUAGE_CODE}/carts/payment_check/?id={paymentobj.p_number}",
            }
        }

        response = requests.post(url, headers=headers, json=data)
        resp_text = response.json()
        redirect_url = resp_text["_links"]["redirect"]["href"]
        paymentobj.payment_id = resp_text['id']
        paymentobj.save()

    elif requested_bank == "flitt":
        from hashlib import sha1
        payment_key = settings.FLITT_PAYMENT_KEY
        merchant_id = settings.FLITT_MERCHANT_ID
        order_id = paymentobj.p_number
        amount = int(round(float(payment_amount_str) * 100))  # smallest unit
        currency = "GEL"
        order_desc = "Flitt Payment"
        server_callback_url = request.build_absolute_uri("/en/carts/check_flitt_webhook/")

        # Generate signature
        signature_text = f"{payment_key}|{amount}|{currency}|{merchant_id}|{order_desc}|{order_id}|{server_callback_url}"
        signature = sha1(signature_text.encode("utf-8")).hexdigest()

        payload = {
            "request": {
                "server_callback_url": server_callback_url,
                "order_id": order_id,
                "currency": currency,
                "merchant_id": merchant_id,
                "order_desc": order_desc,
                "amount": amount,
                "signature": signature
            }
        }

        response = requests.post("https://pay.flitt.com/api/checkout/url", json=payload)
        resp_json = response.json().get("response", {})

        redirect_url = resp_json.get("checkout_url", "")
        paymentobj.payment_id = paymentobj.p_number
        paymentobj.save()
        return redirect(redirect_url)



    elif requested_bank == "tbc_installment":
        payment_key = settings.FLITT_PAYMENT_KEY
        merchant_id = settings.FLITT_MERCHANT_ID
        order_id = paymentobj.p_number
        amount = int(round(float(payment_amount_str) * 100))
        currency = "GEL"
        order_desc = f"Order #{paymentobj.p_number}"

        server_callback_url = request.build_absolute_uri(
            "/en/carts/check_flitt_webhook/"
        )

        response_url = request.build_absolute_uri(
            f"/{request.LANGUAGE_CODE}/carts/payment_check/?id={paymentobj.p_number}"
        )

        params = {
            "amount": amount,
            "currency": currency,
            "merchant_id": merchant_id,
            "order_desc": order_desc,
            "order_id": order_id,
            "payment_method": "tbc",
            "payment_systems": "installments",
            "response_url": response_url,
            "server_callback_url": server_callback_url,
        }

        signature_parts = [payment_key]

        for key in sorted(params.keys()):
            value = params[key]
            if value is not None and value != "":
                signature_parts.append(str(value))

        signature = hashlib.sha1(
            "|".join(signature_parts).encode("utf-8")
        ).hexdigest()

        payload = {
            "request": {
                **params,
                "signature": signature,
            }
        }

        response = requests.post(
            "https://pay.flitt.com/api/checkout/url",
            json=payload
        )

        print(response.text)

        data = response.json()
        resp_json = data.get("response", {})

        redirect_url = resp_json.get("checkout_url")

        if not redirect_url:
            return HttpResponse(response.text)

        paymentobj.payment_id = resp_json.get(
            "payment_id",
            paymentobj.p_number
        )
        paymentobj.save()

        return redirect(redirect_url)


    elif requested_bank == "liberty":
        PAY_URL = "https://www.pay.ge/pay"
        MERCHANT = settings.PAYGE_MERCHANT_ID
        PASSWORD = settings.PAYGE_PASSWORD

        ORDER_CODE = str(paymentobj.p_number)
        # Always store amount in GEL two-decimal format
        payment_amount_gel = Decimal(payment_amount_str).quantize(Decimal("0.01"))
        AMOUNT = payge_amount_gel_to_tetri(str(payment_amount_gel))
        CURRENCY = "GEL"
        LNG = "KA"
        DESCRIPTION = f"Order #{paymentobj.p_number}"
        CUSTOMDATA = str(paymentobj.id)

        params = {
            "merchant": MERCHANT,
            "ordercode": ORDER_CODE,
            "amount": AMOUNT,
            "currency": CURRENCY,
            "description": DESCRIPTION,
            "clientname": "",
            "customdata": CUSTOMDATA,
            "lng": LNG,
            "ispreauth": "",
        }

        CHECK = payge_check(PASSWORD, params)

        pay_fields = dict(params)
        pay_fields["check"] = CHECK

        paymentobj.payment_id = ORDER_CODE
        paymentobj.amount_paid = str(payment_amount_gel)  # <-- always store GEL decimal
        paymentobj.save(update_fields=["payment_id", "amount_paid"])

        return html_autopost_form(PAY_URL, pay_fields)


    return redirect(redirect_url)


from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage
import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from decimal import Decimal
import datetime
import json
import logging

logger = logging.getLogger("flitt_payments")


from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from decimal import Decimal
import hashlib
import json
import datetime
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

# ------------------ LOGGER ------------------


MERCHANT_PASSWORD = settings.PAYGE_PASSWORD


from django.template.loader import render_to_string
from django.conf import settings
import xml.etree.ElementTree as ET

liberty_logger = logging.getLogger("liberty_payments")



# MERCHANT_PASSWORD = settings.PAYGE_PASSWORD




def payge_amount_gel_to_tetri(amount_gel: str) -> int:
    return int((Decimal(amount_gel).quantize(Decimal("0.01"))) * 100)


def sha256_string(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def gel_to_tetri(amount_gel: str) -> int:
    return int((Decimal(amount_gel).quantize(Decimal("0.01"))) * 100)


def build_xml_response(resultcode: int, resultdesc: str, transactioncode: str) -> HttpResponse:
    """
    PAY CALLBACK RESPONSE FORMAT
    check = SHA256(resultcode + resultdesc + transactioncode + password)
    """
    check_string = f"{resultcode}{resultdesc}{transactioncode}{MERCHANT_PASSWORD}"
    check_hash = sha256_string(check_string)

    root = ET.Element("result")
    ET.SubElement(root, "resultcode").text = str(resultcode)
    ET.SubElement(root, "resultdesc").text = resultdesc
    ET.SubElement(root, "check").text = check_hash
    ET.SubElement(root, "data").text = transactioncode

    xml_bytes = ET.tostring(root, encoding="utf-8")
    return HttpResponse(xml_bytes, content_type="application/xml")


# ---------------------------------------------------------
# CALLBACK
# ---------------------------------------------------------

from django.db import transaction
from django.utils import timezone



@csrf_exempt
def check_liberty(request):

    if request.method == "POST":
        data = request.POST
    else:
        data = request.GET

    ordercode = data.get("ordercode")

    if not ordercode:
        return render(request, "shop/submit_order.html", {
            "response": "missing_ordercode"
        })

    payment = get_object_or_404(Payment, p_number=ordercode)
    order = Order.objects.filter(payment=payment).first()

    return render(request, "shop/submit_order.html", {
        "response": payment.status,
        "ecom": payment,
        "order": order,
        "id": payment.payment_id,
    })



# ---------------------------------------------------------
# LIBERTY CALLBACK
# ---------------------------------------------------------

@csrf_exempt
def check_liberty_callback(request):

    import json
    import datetime

    from decimal import Decimal
    from django.db import transaction
    from django.utils import timezone
    from django.core.mail import send_mail, EmailMessage
    from django.template.loader import render_to_string

    data = request.POST if request.method == "POST" else request.GET

    liberty_logger.info(
        "PAY callback %s: %s",
        request.method,
        dict(data)
    )

    status = data.get("status", "").upper()
    transactioncode = data.get("transactioncode", "")
    amount = data.get("amount", "")
    currency = data.get("currency", "")
    ordercode = data.get("ordercode", "")
    paymethod = data.get("paymethod", "")
    customdata = data.get("customdata", "")
    testmode = data.get("testmode", "")
    payedamount = data.get("payedamount")
    received_check = data.get("check", "").upper()

    # -------------------------------------------------
    # REQUIRED VALIDATION
    # -------------------------------------------------

    if not ordercode or not received_check:

        liberty_logger.error(
            "Missing required parameters"
        )

        return build_xml_response(
            -3,
            "Missing parameters",
            transactioncode
        )

    # -------------------------------------------------
    # VERIFY SIGNATURE
    # -------------------------------------------------

    check_string = (
        f"{status}"
        f"{transactioncode}"
        f"{amount}"
        f"{currency}"
        f"{ordercode}"
        f"{paymethod}"
    )

    if paymethod == "PAYTERM" and payedamount:
        check_string += str(payedamount)

    check_string += (
        f"{customdata}"
        f"{testmode}"
        f"{MERCHANT_PASSWORD}"
    )

    calculated_check = sha256_string(check_string)

    if calculated_check != received_check:

        liberty_logger.error(
            "Signature mismatch for %s",
            ordercode
        )

        return build_xml_response(
            -3,
            "Invalid signature",
            transactioncode
        )

    # -------------------------------------------------
    # FETCH PAYMENT
    # -------------------------------------------------

    try:

        payment = Payment.objects.select_for_update().get(
            p_number=ordercode
        )

    except Payment.DoesNotExist:

        liberty_logger.error(
            "Transaction not found: %s",
            ordercode
        )

        return build_xml_response(
            -2,
            "Transaction not found",
            transactioncode
        )

    # -------------------------------------------------
    # PAYTERM CHECK
    # -------------------------------------------------

    if status == "CHECK":

        liberty_logger.info(
            "PAYTERM CHECK OK: %s",
            ordercode
        )

        return build_xml_response(
            0,
            "Ok",
            transactioncode
        )

    # -------------------------------------------------
    # IDEMPOTENCY
    # -------------------------------------------------

    if payment.status == "success":

        liberty_logger.info(
            "Duplicate transaction: %s",
            ordercode
        )

        return build_xml_response(
            1,
            "Duplicate transaction",
            transactioncode
        )

    # -------------------------------------------------
    # COMPLETED
    # -------------------------------------------------

    if status == "COMPLETED":

        try:

            callback_tetri = (
                int(payedamount)
                if paymethod == "PAYTERM" and payedamount
                else int(amount)
            )

            expected_tetri = gel_to_tetri(
                str(payment.amount_paid)
            )

        except Exception as e:

            liberty_logger.error(
                "Amount parse error: %s",
                e
            )

            return build_xml_response(
                -3,
                "Invalid amount format",
                transactioncode
            )

        # -------------------------------------------------
        # AMOUNT VALIDATION
        # -------------------------------------------------

        if callback_tetri < expected_tetri:

            liberty_logger.error(
                "Amount mismatch %s expected=%s got=%s",
                ordercode,
                expected_tetri,
                callback_tetri
            )

            return build_xml_response(
                -3,
                "Amount mismatch",
                transactioncode
            )

        # -------------------------------------------------
        # CREATE ORDER
        # -------------------------------------------------

        with transaction.atomic():

            payment.status = "success"
            payment.payment_method = paymethod.lower()

            payment.save(
                update_fields=[
                    "status",
                    "payment_method"
                ]
            )

            checkout_data = json.loads(
                payment.checkout_data or "{}"
            )

            cart_data = payment.cart_data or []

            # -------------------------------------------------
            # TOTALS
            # -------------------------------------------------

            total = Decimal("0")

            for item in cart_data:

                # 🔥 GIFTS ARE FREE
                if item.get("is_gift"):
                    continue

                total += (
                    Decimal(str(item["price"]))
                    * int(item["quantity"])
                )

            shipping = Decimal(
                str(checkout_data.get("shipping", "0"))
            )

            grand_total = total + shipping

            # -------------------------------------------------
            # CREATE ORDER
            # -------------------------------------------------

            order = Order.objects.create(
                user=payment.user if payment.user and payment.user.is_authenticated else None,
                first_name=checkout_data.get("first_name", ""),
                phone=checkout_data.get("phone", ""),
                email=checkout_data.get("email", ""),
                address_line_1=checkout_data.get("address_line_1", ""),
                city=checkout_data.get("city", ""),
                order_note=checkout_data.get("order_note", ""),
                order_total=grand_total,
                shipping_price=shipping,
                tax=Decimal("0"),
                ip=request.META.get("REMOTE_ADDR"),
                payment=payment,
            )

            ordered_products = []

            # -------------------------------------------------
            # CREATE ORDER PRODUCTS
            # -------------------------------------------------

            for item in cart_data:

                product = Product.objects.select_for_update().get(
                    id=item["product_id"]
                )

                color_value = ""
                size_value = ""
                variation_instance = None

                # -------------------------------------------------
                # VARIATIONS
                # -------------------------------------------------

                for var in item.get("variations", []):

                    if (
                        var["variation_category"].lower()
                        == "color"
                    ):
                        color_value = var["variation_value"]

                    elif (
                        var["variation_category"].lower()
                        == "size"
                    ):
                        size_value = var["variation_value"]

                variation_qs = Variation.objects.filter(
                    product=product
                )

                if color_value:

                    variation_qs = variation_qs.filter(
                        color__title=color_value
                    )

                if size_value:

                    variation_qs = variation_qs.filter(
                        size__title=size_value
                    )

                variation_instance = variation_qs.first()

                # -------------------------------------------------
                # GIFT BOOLEAN
                # -------------------------------------------------

                is_gift = bool(
                    item.get("is_gift", False)
                )

                # -------------------------------------------------
                # PRICE
                # -------------------------------------------------

                product_price = (
                    Decimal("0")
                    if is_gift
                    else Decimal(str(item["price"]))
                )

                # -------------------------------------------------
                # CREATE ORDER PRODUCT
                # -------------------------------------------------

                order_product = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=order.user,
                    product=product,
                    quantity=int(item["quantity"]),
                    product_price=product_price,
                    color=color_value,
                    size=size_value,
                    variation=variation_instance,
                    ordered=True,
                    gift=is_gift
                )

                ordered_products.append(
                    order_product
                )

                # -------------------------------------------------
                # STOCK UPDATE
                # -------------------------------------------------

                product.stock -= int(item["quantity"])

                product.save(
                    update_fields=["stock"]
                )

            # -------------------------------------------------
            # ORDER NUMBER
            # -------------------------------------------------

            order.order_number = (
                f"{timezone.now():%Y%m%d}{order.id}"
            )

            order.save(
                update_fields=["order_number"]
            )

        liberty_logger.info(
            "Order created successfully: %s",
            order.order_number
        )

        # =================================================
        # CUSTOMER EMAIL
        # =================================================

        if order.email:
            _send_customer_order_email(
                request,
                order,
                ordered_products,
                total,
                grand_total,
                shipping,
            )

        # =================================================
        # ADMIN EMAIL
        # =================================================

        current_year = datetime.datetime.now().year

        admin_context = {
            "order": order,
            "ordered_products": ordered_products,
            "total": total,
            "grand_total": grand_total,
            "shipping": shipping,
            "current_year": current_year,
        }

        admin_body = render_to_string(
            "shop/order_confirmation.html",
            admin_context
        )

        admin_email = EmailMessage(
            subject=f"New Order Received - {order.order_number}",
            body=admin_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email for _, email in settings.ADMINS],
        )

        # 🔥 IMPORTANT
        admin_email.content_subtype = "html"

        admin_email.send()

        # =================================================
        # OMNISEND
        # =================================================

        try:

            send_placed_order_event(
                order,
                ordered_products
            )

        except Exception as e:

            liberty_logger.warning(
                "Omnisend placed-order failed: %s",
                e
            )

        return build_xml_response(
            0,
            "Ok",
            transactioncode
        )

    # -------------------------------------------------
    # UNKNOWN STATUS
    # -------------------------------------------------

    liberty_logger.error(
        "Unknown status received: %s",
        status
    )

    return build_xml_response(
        -3,
        "Unknown status",
        transactioncode
    )

# ---------------------------------------------------------
# FLITT WEBHOOK
# ---------------------------------------------------------

@csrf_exempt
def check_flitt_webhook(request):

    import json
    import datetime

    from decimal import Decimal
    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404
    from django.db import transaction
    from django.utils import timezone
    from django.template.loader import render_to_string
    from django.core.mail import send_mail, EmailMessage
    from django.conf import settings

    logger.info("====== FLITT WEBHOOK RECEIVED ======")

    logger.info(
        "Headers: %s",
        dict(request.headers)
    )

    logger.info(
        "Raw body: %s",
        request.body
    )

    # -------------------------------------------------
    # METHOD CHECK
    # -------------------------------------------------

    if request.method != "POST":

        return HttpResponse(
            "INVALID METHOD",
            status=405
        )

    # -------------------------------------------------
    # PARSE JSON
    # -------------------------------------------------

    try:

        data = json.loads(
            request.body.decode("utf-8")
        )

    except Exception:

        logger.exception(
            "Invalid JSON from Flitt"
        )

        return HttpResponse(
            "INVALID JSON",
            status=400
        )

    logger.info(
        "Parsed webhook payload: %s",
        data
    )

    # -------------------------------------------------
    # ORDER ID
    # -------------------------------------------------

    order_id = data.get("order_id")

    if not order_id:

        logger.error(
            "Flitt webhook missing order_id"
        )

        return HttpResponse(
            "MISSING ORDER ID",
            status=400
        )

    payment = get_object_or_404(
        Payment,
        p_number=order_id
    )

    # -------------------------------------------------
    # IDEMPOTENCY
    # -------------------------------------------------

    if payment.status == "success":

        logger.info(
            "Payment already processed: %s",
            payment.p_number
        )

        return HttpResponse("OK")

    # -------------------------------------------------
    # PAYMENT STATUS
    # -------------------------------------------------

    if (
        data.get("order_status") != "approved"
        or data.get("response_status") != "success"
    ):

        payment.status = "failed"

        payment.save(
            update_fields=["status"]
        )

        logger.warning(
            "Payment failed for %s",
            payment.p_number
        )

        return HttpResponse("FAILED")

    # -------------------------------------------------
    # PAYMENT SUCCESS
    # -------------------------------------------------

    payment.status = "success"
    payment.payment_method = "flitt"

    payment.save(
        update_fields=[
            "status",
            "payment_method"
        ]
    )

    # -------------------------------------------------
    # LOAD CHECKOUT DATA
    # -------------------------------------------------

    try:

        checkout_data = json.loads(
            payment.checkout_data or "{}"
        )

    except Exception:

        logger.warning(
            "Invalid checkout JSON for payment %s",
            payment.p_number
        )

        checkout_data = {}

    cart_data = payment.cart_data or []

    ordered_products = []
    order = None

    # -------------------------------------------------
    # CREATE ORDER
    # -------------------------------------------------

    with transaction.atomic():

        # -------------------------------------------------
        # TOTALS
        # -------------------------------------------------

        total = Decimal("0")

        for item in cart_data:

            # 🔥 GIFTS ARE FREE
            if item.get("is_gift"):
                continue

            total += (
                Decimal(str(item["price"]))
                * int(item["quantity"])
            )

        shipping = Decimal(
            str(checkout_data.get("shipping", "8"))
        )

        grand_total = total + shipping

        # -------------------------------------------------
        # CREATE ORDER
        # -------------------------------------------------

        order = Order.objects.create(
            user=payment.user if payment.user and payment.user.is_authenticated else None,
            first_name=checkout_data.get("first_name", "Unknown"),
            phone=checkout_data.get("phone", ""),
            email=checkout_data.get("email", ""),
            address_line_1=checkout_data.get("address_line_1", ""),
            city=checkout_data.get("city", ""),
            order_note=checkout_data.get("order_note", ""),
            order_total=grand_total,
            tax=Decimal("0"),
            shipping_price=shipping,
            ip=request.META.get("REMOTE_ADDR"),
            payment=payment,
        )

        # -------------------------------------------------
        # ORDER PRODUCTS
        # -------------------------------------------------

        for item in cart_data:

            try:

                product = Product.objects.select_for_update().get(
                    id=item["product_id"]
                )

            except Product.DoesNotExist:

                logger.warning(
                    "Product not found: %s",
                    item["product_id"]
                )

                continue

            color_value = ""
            size_value = ""
            variation_instance = None

            # -------------------------------------------------
            # VARIATIONS
            # -------------------------------------------------

            for var in item.get("variations", []):

                if (
                    var["variation_category"].lower()
                    == "color"
                ):
                    color_value = var["variation_value"]

                elif (
                    var["variation_category"].lower()
                    == "size"
                ):
                    size_value = var["variation_value"]

            variation_qs = Variation.objects.filter(
                product=product
            )

            if color_value:

                variation_qs = variation_qs.filter(
                    color__title=color_value
                )

            if size_value:

                variation_qs = variation_qs.filter(
                    size__title=size_value
                )

            variation_instance = variation_qs.first()

            # -------------------------------------------------
            # GIFT BOOLEAN
            # -------------------------------------------------

            is_gift = bool(
                item.get("is_gift", False)
            )

            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            product_price = (
                Decimal("0")
                if is_gift
                else Decimal(str(item["price"]))
            )

            # -------------------------------------------------
            # CREATE ORDER PRODUCT
            # -------------------------------------------------

            order_product = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=payment.user if payment.user and payment.user.is_authenticated else None,
                product=product,
                quantity=int(item["quantity"]),
                product_price=product_price,
                color=color_value,
                size=size_value,
                variation=variation_instance,
                ordered=True,
                gift=is_gift
            )

            ordered_products.append(
                order_product
            )

            # -------------------------------------------------
            # STOCK UPDATE
            # -------------------------------------------------

            product.stock -= int(item["quantity"])

            product.save(
                update_fields=["stock"]
            )

        # -------------------------------------------------
        # ORDER NUMBER
        # -------------------------------------------------

        order.order_number = (
            f"{timezone.now():%Y%m%d}{order.id}"
        )

        order.save(
            update_fields=["order_number"]
        )

    logger.info(
        "Order successfully created: %s",
        order.order_number
    )

    # =================================================
    # CUSTOMER EMAIL
    # =================================================

    if order.email:
        _send_customer_order_email(
            request,
            order,
            ordered_products,
            total,
            grand_total,
            shipping,
        )

    # =================================================
    # ADMIN EMAIL
    # =================================================

    admin_context = {
        "order": order,
        "ordered_products": ordered_products,
        "total": total,
        "grand_total": grand_total,
        "shipping": shipping,
        "current_year": datetime.datetime.now().year,
    }

    admin_body = render_to_string(
        "shop/order_confirmation.html",
        admin_context,
    )

    admin_email = EmailMessage(
        subject=f"New Order Received - {order.order_number}",
        body=admin_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email for _, email in settings.ADMINS],
    )

    # 🔥 IMPORTANT
    admin_email.content_subtype = "html"

    admin_email.send()

    # =================================================
    # OMNISEND
    # =================================================

    try:

        send_placed_order_event(
            order,
            ordered_products
        )

    except Exception as e:

        logger.warning(
            "Omnisend placed-order failed: %s",
            e
        )

    return HttpResponse("OK")
@csrf_exempt
def check_flitt(request):
    """
    Flitt USER REDIRECT (POST)
    Shows order/payment status only
    """

    if request.method != "POST":
        return HttpResponse("INVALID METHOD", status=405)

    order_id = request.POST.get("order_id")

    if not order_id:
        return render(request, "shop/submit_order.html", {
            "response": "missing_order_id"
        })

    payment = get_object_or_404(Payment, p_number=order_id)

    order = Order.objects.filter(payment=payment).first()

    return render(request, "shop/submit_order.html", {
        "response": payment.status,
        "ecom": payment,
        "order": order,
        "id": payment.payment_id,
    })



# def payment_check(request):
#     payment_id = request.GET.get('id')
#     paymentl = get_object_or_404(Payment, p_number=payment_id)

#     if paymentl.status == 'process':
#         # ---------------- BANK CHECK ----------------
#         response_status = None
#         resp = {}

#         if paymentl.bank == 'tbc':
#             url = f"https://api.tbcbank.ge/v1/tpay/payments/{paymentl.payment_id}"
#             headers = {
#                 "accept": "application/json",
#                 "apikey": settings.TBC_PAYMENTS_API_KEY,
#                 "authorization": f"Bearer {paymentl.bearer}"
#             }
#             response = requests.get(url, headers=headers)
#             resp = response.json()
#             response_status = resp.get('status')

#         elif paymentl.bank == 'bog':
#             order_id = paymentl.payment_id
#             access_token = paymentl.bearer
#             url = f"https://api.bog.ge/payments/v1/receipt/{order_id}"
#             headers = {"Authorization": f"Bearer {access_token}"}
#             response = requests.get(url, headers=headers)
#             resp = response.json()
#             response_status = resp.get("payment_detail", {}).get("code")


#         elif paymentl.bank == 'flitt':
#     	    return check_flitt(request)

#         # elif paymentl.bank == 'liberty':
#         #     PAY_URL = "https://www.pay.ge/payments/v1/transactions/status"
#         #     MERCHANT = settings.PAYGE_MERCHANT_ID
#         # ---------------- ORDER CREATION ----------------
#         ordered_products = []
#         order = None
#         total = Decimal('0')
#         grand_total = Decimal('0')
#         shipping = Decimal('8')
#         discount = Decimal('0')

#         if response_status in ['Succeeded', '100'] or resp.get("order_status", {}).get("key") == "completed":
#             paymentl.status = 'success'

#             user = paymentl.user if paymentl.user else None
#             ip_address = request.META.get('REMOTE_ADDR')

#             form_data = request.session.pop('order_form_data', {})
#             shipping = Decimal(form_data.get('shipping', '8'))

#             cart_data = paymentl.cart_data or []
#             for item in cart_data:
#                 total += Decimal(item['price']) * int(item['quantity'])

#             # Apply voucher discounts
#             voucher_code = request.session.pop('voucher_code', '').strip().lower()
#             if voucher_code == "since1998" and total > 50:
#                 shipping = Decimal('0')
#             elif voucher_code == "sale5":
#                 discount = total * Decimal('0.05')
#             elif voucher_code == "sale10":
#                 discount = total * Decimal('0.10')
#             elif voucher_code == "sale15":
#                 discount = total * Decimal('0.15')

#             total_after_discount = total - discount
#             grand_total = total_after_discount + shipping

#             # Create main order
#             order = Order.objects.create(
#                 user=user if user and getattr(user, 'is_authenticated', False) else None,
#                 first_name=form_data.get('first_name', 'Unknown'),
#                 phone=form_data.get('phone', ''),
#                 email=form_data.get('email', ''),
#                 address_line_1=form_data.get('address_line_1', ''),
#                 city=form_data.get('city', ''),
#                 order_note=form_data.get('order_note', ''),
#                 order_total=grand_total,
#                 tax=Decimal('0'),
#                 shipping_price=shipping,
#                 ip=ip_address,
#                 payment=paymentl
#             )

#             # Loop through cart and create OrderProduct
#             for item in cart_data:
#                 try:
#                     product = Product.objects.get(id=item['product_id'])
#                 except Product.DoesNotExist:
#                     continue

#                 color_value = ''
#                 size_value = ''
#                 variation_instance = None

#                 # Extract chosen color/size from JSON
#                 for var in item.get('variations', []):
#                     if var['variation_category'].lower() == 'color':
#                         color_value = var['variation_value']
#                     elif var['variation_category'].lower() == 'size':
#                         size_value = var['variation_value']

#                 # Match exact variation in DB
#                 variation_qs = Variation.objects.filter(product=product)
#                 if color_value:
#                     variation_qs = variation_qs.filter(color__title=color_value)
#                 if size_value:
#                     variation_qs = variation_qs.filter(size__title=size_value)
#                 variation_instance = variation_qs.first()

#                 # Create order product
#                 order_product = OrderProduct.objects.create(
#                     order=order,
#                     payment=paymentl,
#                     user=user if user and getattr(user, 'is_authenticated', False) else None,
#                     product=product,
#                     quantity=int(item['quantity']),
#                     product_price=float(item['price']),
#                     color=color_value,
#                     size=size_value,
#                     variation=variation_instance,
#                     ordered=True
#                 )
#                 ordered_products.append(order_product)

#                 # Update stock
#                 product.stock -= int(item['quantity'])
#                 product.save()

#             # Set order number
#             current_date = datetime.date.today().strftime("%Y%m%d")
#             order.order_number = f"{current_date}{order.id}"
#             order.save()

#             # ---------------- EMAIL TO CUSTOMER ----------------
#             mail_context = {
#                 'order': order,
#                 'ordered_products': ordered_products,
#                 'grand_total': grand_total,
#                 'shipping': shipping,
#             }
#             email_subject = f'Order Confirmation - {order.order_number}'
#             email_body = render_to_string('shop/customer_new_order_notification.html', mail_context)
#             send_mail(
#                 email_subject,
#                 '',
#                 settings.DEFAULT_FROM_EMAIL,
#                 [order.email],
#                 html_message=email_body,
#                 fail_silently=False,
#             )

#             # ---------------- EMAIL TO ADMIN ----------------
#             current_year = datetime.datetime.now().year
#             admin_subject = f"New Order Received - {order.order_number}"
#             admin_body = render_to_string('shop/order_confirmation.html', {
#                 'order': order,
#                 'ordered_products': ordered_products,
#                 'total': total,
#                 'grand_total': grand_total,
#                 'shipping': shipping,
#                 'current_year': current_year,
#             })
#             admin_email = EmailMessage(
#                 subject=admin_subject,
#                 body=admin_body,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[admin_email for _, admin_email in settings.ADMINS],
#             )
#             admin_email.content_subtype = 'html'
#             admin_email.send()
#             try:
#                 send_placed_order_event(order, ordered_products)
#             except Exception as e:
#                 print("Omnisend placed-order send failed:", e)

#         elif response_status in [
#             "Failed", "101", "102", "103", "104", "105", "106", "107",
#             "108", "109", "110", "111", "112", "199"
#         ]:
#             paymentl.status = 'failed'
#         elif response_status == "CancelPaymentProcessing":
#             paymentl.status = 'canceled'
#         else:
#             paymentl.status = 'process'

#         paymentl.save()

#         return render(request, 'shop/submit_order.html', {
#             'response': response_status,
#             'ecom': paymentl,
#             'id': paymentl.payment_id,
#             'order': order,
#             'ordered_products': ordered_products,
#             'total': total,
#             'grand_total': grand_total,
#             'shipping': shipping,
#         })

#     # If payment is not "process", just show current status
#     return render(request, 'shop/submit_order.html', {
#         'response': paymentl.status,
#         'ecom': paymentl,
#         'id': paymentl.payment_id,
#         'total': paymentl.amount_paid,
#     })


def payment_check(request):
    """
    User-facing page to show payment/order status.
    Callback handles actual processing.
    """
    payment_id = request.GET.get('id')
    payment = Payment.objects.filter(p_number=payment_id).first()
    if not payment:
        fallback_date = datetime.datetime(2026, 8, 28)
        fallback_order = {
            'order_number': payment_id or '20260828123',
            'created_at': fallback_date,
            'first_name': 'Ani',
            'full_name': 'Ani Mucharashvili',
            'address_line_1': 'თბილისი',
            'city': 'საქართველო',
        }
        fallback_payment = {
            'p_number': payment_id or '20260828123',
            'payment_id': payment_id or '20260828123',
            'status': 'success',
            'created_at': fallback_date,
        }
        return render(request, 'shop/submit_order.html', {
            'response': 'success',
            'ecom': fallback_payment,
            'id': payment_id,
            'order': fallback_order,
            'ordered_products': OrderProduct.objects.none(),
            'cart_snapshot_items': [
                {
                    'name': 'OldSupra მაისური',
                    'quantity': 1,
                    'color': 'შავი',
                    'size': 'M',
                    'line_total': Decimal('89.00'),
                },
                {
                    'name': 'OldSupra ქუდი',
                    'quantity': 1,
                    'color': 'თეთრი',
                    'size': '',
                    'line_total': Decimal('49.00'),
                },
            ],
            'total': Decimal('138.00'),
            'grand_total': Decimal('146.00'),
            'shipping': Decimal('8.00'),
        })

    order = Order.objects.filter(payment=payment).first()
    ordered_products = OrderProduct.objects.none()
    cart_snapshot_items = []
    shipping = Decimal('0')
    total = Decimal('0')
    grand_total = Decimal(str(payment.amount_paid or '0'))

    if payment.cart_data:
        for item in payment.cart_data:
            quantity = int(item.get('quantity', 0))
            unit_price = Decimal(str(item.get('price', '0')))
            product_id = item.get('product_id')
            product = None
            if str(product_id).isdigit():
                product = Product.objects.filter(id=product_id).first()
            color = ''
            size = ''

            for variation in item.get('variations', []):
                category = variation.get('variation_category', '').lower()
                value = variation.get('variation_value', '')
                if category == 'color':
                    color = value
                elif category == 'size':
                    size = value

            is_gift = bool(item.get('is_gift', item.get('gift', False)))
            line_total = Decimal('0') if is_gift else unit_price * quantity

            cart_snapshot_items.append({
                'name': product.Product_name if product else item.get('name', ''),
                'product': product,
                'quantity': quantity,
                'color': color,
                'size': size,
                'line_total': line_total,
            })

            total += line_total

        checkout_data = payment.checkout_data or {}
        shipping = Decimal(str(checkout_data.get('shipping', '0')))
        grand_total = total + shipping

    if order:
        ordered_products = OrderProduct.objects.filter(order=order).select_related(
            'product',
            'variation',
            'variation__color',
            'variation__size',
        )
        shipping = Decimal(str(order.shipping_price or '0'))
        grand_total = Decimal(str(order.order_total or '0'))
        total = grand_total - shipping

    return render(request, 'shop/submit_order.html', {
        'response': payment.status,
        'ecom': payment,
        'id': payment.payment_id,
        'order': order,
        'ordered_products': ordered_products,
        'cart_snapshot_items': cart_snapshot_items,
        'total': total,
        'grand_total': grand_total,
        'shipping': shipping,
    })




@csrf_exempt
def check_bog_callback(request):

    import json
    import logging
    import datetime

    from decimal import Decimal
    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404
    from django.db import transaction
    from django.utils import timezone
    from django.template.loader import render_to_string
    from django.core.mail import send_mail, EmailMessage
    from django.conf import settings

    logger = logging.getLogger("bog_callback")

    try:

        # -------------------------------------------------
        # PARSE CALLBACK
        # -------------------------------------------------

        raw_body = request.body

        data = json.loads(raw_body)

        logger.info(
            "BOG Callback payload: %s",
            data
        )

        payload = data.get("body", {})

        order_id = payload.get(
            "external_order_id"
        )

        if not order_id:

            logger.error(
                "Missing external_order_id in callback"
            )

            return HttpResponse(status=200)

        payment = get_object_or_404(
            Payment,
            p_number=order_id
        )

        # -------------------------------------------------
        # IDEMPOTENCY
        # -------------------------------------------------

        if payment.status == "success":

            logger.info(
                "Payment already processed: %s",
                payment.p_number
            )

            return HttpResponse(status=200)

        # -------------------------------------------------
        # PAYMENT STATUS
        # -------------------------------------------------

        response_status = (
            payload.get("payment_detail", {}).get("code")
            or payload.get("order_status", {}).get("key")
        )

        logger.info(
            "BOG payment status: %s",
            response_status
        )

        if response_status not in [
            "100",
            "Succeeded",
            "completed"
        ]:

            payment.status = "failed"

            payment.save(
                update_fields=["status"]
            )

            return HttpResponse(status=200)

        # -------------------------------------------------
        # CREATE ORDER
        # -------------------------------------------------

        with transaction.atomic():

            payment.status = "success"
            payment.payment_method = "bog"

            payment.save(
                update_fields=[
                    "status",
                    "payment_method"
                ]
            )

            checkout_data = json.loads(
                payment.checkout_data or "{}"
            )

            cart_data = payment.cart_data or []

            user = (
                payment.user
                if payment.user
                and payment.user.is_authenticated
                else None
            )

            # -------------------------------------------------
            # TOTALS
            # -------------------------------------------------

            total = Decimal("0")

            for item in cart_data:

                # 🔥 GIFTS ARE FREE
                if item.get("is_gift"):
                    continue

                total += (
                    Decimal(str(item["price"]))
                    * int(item["quantity"])
                )

            shipping = Decimal(
                str(
                    checkout_data.get(
                        "shipping",
                        "0"
                    )
                )
            )

            grand_total = total + shipping

            # -------------------------------------------------
            # ORDER
            # -------------------------------------------------

            order = Order.objects.create(
                user=user,
                first_name=checkout_data.get(
                    "first_name",
                    ""
                ),
                phone=checkout_data.get(
                    "phone",
                    ""
                ),
                email=checkout_data.get(
                    "email",
                    ""
                ),
                address_line_1=checkout_data.get(
                    "address_line_1",
                    ""
                ),
                city=checkout_data.get(
                    "city",
                    ""
                ),
                order_note=checkout_data.get(
                    "order_note",
                    ""
                ),
                order_total=grand_total,
                tax=Decimal("0"),
                shipping_price=shipping,
                ip=request.META.get(
                    "REMOTE_ADDR"
                ),
                payment=payment
            )

            ordered_products = []

            # -------------------------------------------------
            # ORDER PRODUCTS
            # -------------------------------------------------

            for item in cart_data:

                try:

                    product = Product.objects.select_for_update().get(
                        id=item["product_id"]
                    )

                except Product.DoesNotExist:

                    logger.warning(
                        "Product not found: %s",
                        item["product_id"]
                    )

                    continue

                color_value = ""
                size_value = ""
                variation_instance = None

                # -------------------------------------------------
                # VARIATIONS
                # -------------------------------------------------

                for var in item.get("variations", []):

                    if (
                        var["variation_category"].lower()
                        == "color"
                    ):

                        color_value = (
                            var["variation_value"]
                        )

                    elif (
                        var["variation_category"].lower()
                        == "size"
                    ):

                        size_value = (
                            var["variation_value"]
                        )

                variation_qs = Variation.objects.filter(
                    product=product
                )

                if color_value:

                    variation_qs = variation_qs.filter(
                        color__title=color_value
                    )

                if size_value:

                    variation_qs = variation_qs.filter(
                        size__title=size_value
                    )

                variation_instance = (
                    variation_qs.first()
                )

                # -------------------------------------------------
                # GIFT BOOLEAN
                # -------------------------------------------------

                is_gift = bool(
                    item.get(
                        "is_gift",
                        False
                    )
                )

                # -------------------------------------------------
                # PRICE
                # -------------------------------------------------

                product_price = (
                    Decimal("0")
                    if is_gift
                    else Decimal(
                        str(item["price"])
                    )
                )

                # -------------------------------------------------
                # CREATE ORDER PRODUCT
                # -------------------------------------------------

                op = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=user,
                    product=product,
                    quantity=int(
                        item["quantity"]
                    ),
                    product_price=product_price,
                    color=color_value,
                    size=size_value,
                    variation=variation_instance,
                    ordered=True,
                    gift=is_gift
                )

                ordered_products.append(op)

                # -------------------------------------------------
                # STOCK UPDATE
                # -------------------------------------------------

                product.stock -= int(
                    item["quantity"]
                )

                product.save(
                    update_fields=["stock"]
                )

            # -------------------------------------------------
            # ORDER NUMBER
            # -------------------------------------------------

            order.order_number = (
                f"{timezone.now():%Y%m%d}{order.id}"
            )

            order.save(
                update_fields=[
                    "order_number"
                ]
            )

        # =================================================
        # CUSTOMER EMAIL
        # =================================================

        if order.email:
            _send_customer_order_email(
                request,
                order,
                ordered_products,
                total,
                grand_total,
                shipping,
            )

        # =================================================
        # ADMIN EMAIL
        # =================================================

        current_year = (
            datetime.datetime.now().year
        )

        admin_subject = (
            f"New Order Received - "
            f"{order.order_number}"
        )

        admin_context = {
            "order": order,
            "ordered_products": ordered_products,
            "total": total,
            "grand_total": grand_total,
            "shipping": shipping,
            "current_year": current_year,
        }

        admin_body = render_to_string(
            "shop/order_confirmation.html",
            admin_context
        )

        admin_email = EmailMessage(
            subject=admin_subject,
            body=admin_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[
                email
                for _, email
                in settings.ADMINS
            ],
        )

        # 🔥 IMPORTANT
        admin_email.content_subtype = "html"

        admin_email.send()

        # =================================================
        # OMNISEND
        # =================================================

        try:

            send_placed_order_event(
                order,
                ordered_products
            )

        except Exception as e:

            logger.error(
                "Omnisend placed-order send failed: %s",
                e
            )

        logger.info(
            "BOG order created: %s",
            order.order_number
        )

    except Exception as e:

        logger.exception(
            "BOG CALLBACK ERROR: %s",
            str(e)
        )

    return HttpResponse(status=200)




@login_required(login_url='login')
def checkout(request, total=0, quantity=0, shipping=0, cart_items=None):
    try:

        grand_total = 0
        total = 0
        shipping = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            if cart_item.product.is_on_sale:
                total += (cart_item.product.discount_price * cart_item.quantity)
                quantity += cart_item.quantity

            else:
                total += (cart_item.product.price * cart_item.quantity)
                quantity += cart_item.quantity
        if total <= 500:
            shipping += 50
        else:
            shipping == 0

        grand_total = total + shipping
    except ObjectDoesNotExist:
        pass #just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'shipping': shipping,
    }
    return render(request, 'shop/checkout.html', context)

def submit_order(request):
    return render(request, 'shop/submit_order.html',)


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@csrf_exempt
def update_cart_quantity(request, cart_item_id):
    try:
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {request.META.get('HTTP_X_CSRFTOKEN')}")

        if request.method != "POST":
            return JsonResponse({
                'success': False,
                'message': f'Invalid request method: {request.method}'
            }, status=405)

        # CART LOAD
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        # PRICE LOGIC
        def get_effective_price(product, variation=None, item=None):
            """
            Gift logic added:
            - If item is marked as gift -> price = 0
            """
            if item and hasattr(item, "is_gift") and item.is_gift:
                return Decimal("0")

            if variation:
                return (
                    variation.discount_price
                    if product.is_on_sale and variation.discount_price
                    else variation.price
                )

            return (
                product.discount_price
                if product.is_on_sale and product.discount_price
                else product.price
            )

        # ensure base price exists
        if not cart_item.price:
            variation = cart_item.variations.first() if cart_item.variations.exists() else None
            cart_item.price = get_effective_price(cart_item.product, variation, cart_item)
            cart_item.save()

        # UPDATE QTY
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)

        cart_item.quantity = new_quantity
        cart_item.save()

        # INPUTS
        voucher_code = request.POST.get('voucher_code', '').strip().lower()
        shipping_input = request.POST.get('shipping', '0')

        try:
            shipping = Decimal(shipping_input)
        except Exception:
            shipping = Decimal('0')

        # TOTAL CALCULATION
        total = Decimal('0')
        quantity = 0

        for item in cart_items:
            variation = item.variations.first() if item.variations.exists() else None

            price = Decimal(
                get_effective_price(item.product, variation, item)
            )

            line_total = price * item.quantity

            total += line_total
            quantity += item.quantity

        # DISCOUNT LOGIC
        discount = Decimal('0')


        if total >= 100:
            shipping = Decimal('0')

        if voucher_code == 'since1998' and total > 50:
            shipping = Decimal('0')

        elif total >= 50:
            if voucher_code == 'sale5':
                discount = total * Decimal('0.05')
            elif voucher_code == 'sale10':
                discount = total * Decimal('0.10')
            elif voucher_code == 'sale15':
                discount = total * Decimal('0.15')

        total_after_discount = total - discount
        grand_total = total_after_discount + shipping

        sub_total = (
            Decimal(get_effective_price(cart_item.product, cart_item.variations.first() if cart_item.variations.exists() else None, cart_item))
            * cart_item.quantity
        )

        return JsonResponse({
            'success': True,
            'sub_total': float(sub_total),
            'cart_total': float(total),
            'grand_total': float(grand_total),
            'shipping': float(shipping),
            'quantity': quantity
        })

    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)

    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart not found'}, status=404)

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# def update_cart_quantity(request, cart_item_id):
#     try:
#         if request.method != "POST":
#             return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

#         if request.user.is_authenticated:
#             cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
#             cart_items = CartItem.objects.filter(user=request.user, is_active=True)
#         else:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
#             cart_items = CartItem.objects.filter(cart=cart, is_active=True)

#         def get_effective_price(product, variation=None):
#             if variation:
#                 return variation.discount_price if product.is_on_sale and variation.discount_price else variation.price
#             return product.discount_price if product.is_on_sale and product.discount_price else product.price

#         if not cart_item.price:
#             variation = cart_item.variations.first() if cart_item.variations.exists() else None
#             cart_item.price = get_effective_price(cart_item.product, variation)
#             cart_item.save()

#         new_quantity = int(request.POST.get('quantity', 1))
#         if new_quantity <= 0:
#             return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)

#         cart_item.quantity = new_quantity
#         cart_item.save()

#         voucher_code = request.POST.get('voucher_code', '').strip().lower()
#         shipping_input = request.POST.get('shipping', '0')
#         try:
#             shipping = Decimal(shipping_input)
#         except Exception:
#             shipping = Decimal('0')

#         total = Decimal('0')
#         quantity = 0
#         for item in cart_items:
#             variation = item.variations.first() if item.variations.exists() else None
#             price = Decimal(get_effective_price(item.product, variation))
#             total += price * item.quantity
#             quantity += item.quantity

#         discount = Decimal('0')

#         if voucher_code == 'since1998' and total > 50:
#             shipping = Decimal('0')

#         elif total >= 50:
#             if voucher_code == 'sale5':
#                 discount = total * Decimal('0.05')
#             elif voucher_code == 'sale10':
#                 discount = total * Decimal('0.10')
#             elif voucher_code == 'sale15':
#                 discount = total * Decimal('0.15')
#         else:
#             pass

#         total_after_discount = total - discount
#         grand_total = total_after_discount + shipping

#         sub_total = cart_item.price * cart_item.quantity

#         return JsonResponse({
#             'success': True,
#             'sub_total': float(sub_total),
#             'cart_total': float(total),
#             'grand_total': float(grand_total),
#             'shipping': float(shipping),
#             'quantity': quantity
#         })

#     except CartItem.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)
#     except Cart.DoesNotExist:
#         return JsonResponse({'success': False, 'message': 'Cart not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'message': str(e)}, status=500)
