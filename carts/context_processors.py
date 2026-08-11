from .models import Cart, CartItem, Wishlist
from .views import _cart_id, _wishlist_id
from django.core.exceptions import ObjectDoesNotExist


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)


def carttest(request, total=0, quantity=0, shipping=0, cart_items=None):
    try:
        total = 0
        grand_total_cart_item = 0
        shipping = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:

            # 🔴 GIFT FIX
            if cart_item.is_gift:
                item_total = 0
            else:
                item_total = cart_item.product.price * cart_item.quantity
                total += item_total

            quantity += cart_item.quantity

        grand_total_cart_item = total + shipping

    except ObjectDoesNotExist:
        pass

    return dict(grand_total_cart_item=grand_total_cart_item)
    
    
    
def carttest_shipping(request, total=0, quantity=0, shipping=0, cart_items=None):
    try:
        total = 0
        grand_total_cart_item = 0
        shipping = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:

            # 🔴 GIFT FIX
            if cart_item.is_gift:
                continue

            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        if total <= 50:
            shipping = 50
        else:
            shipping = 0

        grand_total_cart_item = total + shipping

    except ObjectDoesNotExist:
        pass

    return dict(shipping=shipping, total=total)

def carttest2(request, total=0, quantity=0, shipping=0, cart_items_cart=None):
    try:
        total = 0
        quantity = 0
        shipping = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items_cart = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items_cart = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items_cart:

            # 🔴 GIFT FIX
            if cart_item.is_gift:
                continue

            variation = cart_item.variations.first() if cart_item.variations.exists() else None

            if variation:
                price = (
                    variation.discount_price
                    if cart_item.product.is_on_sale and variation.discount_price
                    else variation.price
                )
            else:
                price = (
                    cart_item.product.discount_price
                    if cart_item.product.is_on_sale and cart_item.product.discount_price
                    else cart_item.product.price
                )

            total += price * cart_item.quantity
            quantity += cart_item.quantity

        grand_total = total + shipping

    except Cart.DoesNotExist:
        pass

    return dict(
        cart_items_cart=cart_items_cart,
        shipping=shipping,
        grand_total=grand_total
    )


def wishlist(request, total=0, quantity=0, shipping=0, wishlist_items_cart=None):
    try:
        total = 0
        grand_total = 0
        shipping = 0
        if request.user.is_authenticated:
            wishlist_items_cart = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
            wishlist_items_cart = WishlistItem.objects.filter(wishlist=wishlist, is_active=True)
        for wishlist_item in wishlist_items_cart:
            total += (wishlist_item.product.price * wishlist_item.quantity)
            quantity += wishlist_item.quantity


        if total <= 50:
            shipping += 50
        else:
            shipping == 0

        grand_total = total + shipping
    except ObjectDoesNotExist:
        pass #just ignore

    return dict(wishlist_items_cart=wishlist_items_cart, shipping=shipping)


def carttest3(request, total=0, quantity=0, shipping=0, cart_items=None):
    try:
        total = 0
        grand_total_cart_item = 0
        shipping = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity


        if total <= 50:
            shipping += 50
        else:
            shipping == 0

        grand_total_cart_item = total + shipping
    except ObjectDoesNotExist:
        pass #just ignore

    return dict(grand_total_cart_item=grand_total_cart_item, shipping=shipping)
