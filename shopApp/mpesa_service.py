import requests
import base64
from datetime import datetime
from django.conf import settings


def get_mpesa_access_token():
    """Fetches the OAuth token needed to authorize API requests."""
    if settings.MPESA_ENV == "sandbox":
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        api_url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    # Encode the consumer key and secret
    auth_string = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {"Authorization": f"Basic {b64_auth}"}
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Failed to get access token: {response.text}")


def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    """Sends the STK Push prompt to the customer's phone."""
    access_token = get_mpesa_access_token()

    if settings.MPESA_ENV == "sandbox":
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    else:
        api_url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    # Generate Timestamp and Password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode()

    # Format phone number: remove leading 0 or +254, ensure it starts with 254
    phone_number = str(phone_number)
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference[:12],
        "TransactionDesc": transaction_desc[:13]
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()