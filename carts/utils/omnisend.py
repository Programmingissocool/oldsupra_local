
import requests
from datetime import datetime
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings


API_KEY = settings.OMNISEND_API_KEY
BASE_URL = "https://api.omnisend.com/v3"
HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

def send_contact(email, first_name=None, last_name=None):
    data = {
        "email": email,
        "status": "subscribed",
        "statusDate": datetime.utcnow().isoformat() + "Z"
    }

    if first_name:
        data["firstName"] = first_name
    if last_name:
        data["lastName"] = last_name

    try:
        response = requests.post(f"{BASE_URL}/contacts", headers=HEADERS, json=data)
        print("Omnisend contact response:", response.status_code, response.text)
        return response.status_code
    except Exception as e:
        print("Omnisend error:", e)
        return None



OMNISEND_API_KEY = settings.OMNISEND_API_KEY
OMNISEND_BASE_URL = "https://api.omnisend.com/v3"
OMNISEND_HEADERS = {
    "X-API-KEY": OMNISEND_API_KEY,
    "Content-Type": "application/json",
    "accept": "application/json"
}


from shop.models import Product, Variation
from carts.models import Cart, CartItem

def send_cart_event(email, cart_id, products, phone=None, contact_id=None):
    """Send 'added-product-to-cart' event to Omnisend."""
    url = f"{OMNISEND_BASE_URL}/carts"
    payload = {
        "eventName": "added-product-to-cart",
        "cartID": str(cart_id),
        "currency": "GEL",
        "email": email,
        "phone": phone,
        "contactID": contact_id,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "products": products
    }
    try:
        response = requests.post(url, json=payload, headers=OMNISEND_HEADERS)
        print("Omnisend cart event response:", response.status_code, response.text)
    except Exception as e:
        print("Omnisend cart event error:", e)
        
        
def send_cart_event_beta(user_email, cart_item):
    url = "https://api.omnisend.com/v3/carts"

    price = cart_item.price or cart_item.product.price
    total = cart_item.quantity * price

    payload = {
        "eventName": "added-product-to-cart",
        "currency": "GEL",
        "products": [
            {
                "cartProductID": str(cart_item.id),
                "productID": str(cart_item.product.id),
                "variantID": str(cart_item.variations.first().id) if cart_item.variations.exists() else None,
                "title": cart_item.product.Product_name,
                "quantity": cart_item.quantity,
                "price": int(price * 100)  # price in cents
            }
        ],
        "cartID": str(cart_item.cart.id if cart_item.cart else cart_item.id),
        "email": user_email,
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "cartSum": int(total * 100)  # total price in cents
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": OMNISEND_API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("\nOmnisend beta response:", response.status_code, response.text)
    except Exception as e:
        print("Omnisend beta error:", e)
        
        
        

# def send_placed_order_event(order, ordered_products):
#     url = f"{OMNISEND_BASE_URL}/events"

#     products_payload = []
#     for item in ordered_products:
#         products_payload.append({
#             "productID": str(item.product.id),
#             "title": item.product.Product_name,
#             "quantity": item.quantity,
#             "price": int(item.product_price * 100)  # in cents
#         })

#     payload = {
#         "eventName": "placed-order",
#         "email": order.email,
#         "firstName": order.first_name,
#         "lastName": order.last_name,
#         "phone": order.phone,
#         "orderID": str(order.id),
#         "currency": "GEL",
#         "total": int(order.order_total * 100),  # in cents
#         "products": products_payload,
#         "createdAt": datetime.utcnow().isoformat() + "Z"  # ✅ required field
#     }

#     try:
#         response = requests.post(url, headers=OMNISEND_HEADERS, json=payload)
#         print("Omnisend placed-order response:", response.status_code, response.text)
#     except Exception as e:
#         print("Omnisend placed-order error:", e)
        
        
        
def send_placed_order_event(order, order_products):
    """
    Send 'placed-order' event to Omnisend.
    Docs: https://api-docs.omnisend.com/reference/placed-order
    """
    url = f"{OMNISEND_BASE_URL}/orders"

    payload = {
        "orderID": str(order.order_number),  # must be unique
        "email": order.email,
        "phone": order.phone if order.phone else None,
        "currency": "GEL",
        "orderDate": order.created_at.isoformat() + "Z",
        "status": "placed",  # could be 'placed', 'shipped', etc.
        "products": [],
        "orderSum": int(order.order_total * 100),  # in cents
        "shippingPrice": int(order.shipping_price * 100),  
        "createdAt": datetime.utcnow().isoformat() + "Z",  # ✅ required field# in cents
        "billingAddress": {
            "firstName": order.first_name,
            "lastName": order.last_name,
            "country": order.country,
            "city": order.city,
            "address": order.address_line_1,
            "state": order.state,
            "postalCode": "",  # add if available
        },
        "shippingAddress": {
            "firstName": order.first_name,
            "lastName": order.last_name,
            "country": order.country,
            "city": order.city,
            "address": order.address_line_1,
            "state": order.state,
            "postalCode": "",  # add if available
        }
    }

    # Add products
    for op in order_products:
        payload["products"].append({
            "productID": str(op.product.id),
            "variantID": str(op.variation.id) if op.variation else None,
            "title": op.product.Product_name,
            "quantity": op.quantity,
            "price": int(op.product_price * 100),  # in cents
        })

    try:
        response = requests.post(url, json=payload, headers=OMNISEND_HEADERS)
        print("\nOmnisend placed-order response:", response.status_code, response.text)
    except Exception as e:
        print("Omnisend placed-order error:", e)        
