import os
import django
import requests
import json
from django.shortcuts import get_object_or_404

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solutioner.settings')
django.setup()

from orders.models import Payment

# Step 1: Get a fresh token from BOG
auth_url = "https://oauth2.bog.ge/auth/realms/bog/protocol/openid-connect/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": os.environ.get("BOG_CLIENT_ID", ""),         # 🔁 Replace with actual values
    "client_secret": os.environ.get("BOG_CLIENT_SECRET", "")  # 🔁 Replace with actual values
}

auth_response = requests.post(auth_url, data=token_data)
token_json = auth_response.json()

if 'access_token' not in token_json:
    print("❌ Failed to get access token:", token_json)
    exit()

bearer_token = token_json['access_token']

# Step 2: Query BOG payment status
payment_id = "P811824"
payment = get_object_or_404(Payment, p_number=payment_id)

if payment.status == 'process' and payment.bank == 'bog':
    url = f"https://api.bog.ge/payments/v1/receipt/{payment.payment_id}"

    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    response = requests.get(url, headers=headers)
    resp = response.json()

    print("Full BOG Response:", json.dumps(resp, indent=2))  # Debug: Show the full response
    print("BOG Order Status Key:", resp.get("order_status", {}).get("key"))
    print("BOG Payment Code:", resp.get("payment_detail", {}).get("code"))
    print("BOG Payment Description:", resp.get("payment_detail", {}).get("code_description"))
