"""Paystack integration for NGN deposits and withdrawals."""

import requests
import os
from datetime import datetime
from models import db, Transaction
import uuid


class PaystackAPI:
    """Paystack payment gateway integration."""

    BASE_URL = "https://api.paystack.co"

    def __init__(self, secret_key=None):
        """Initialize Paystack API."""
        self.secret_key = secret_key or os.getenv('PAYSTACK_SECRET_KEY')
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def initialize_payment(self, email, amount, reference=None, callback_url=None):
        """
        Initialize a payment transaction.

        Args:
            email: Customer email
            amount: Amount in kobo (multiply Naira by 100)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment

        Returns:
            dict with authorization_url and reference
        """
        if not reference:
            reference = f"BITOKI_{uuid.uuid4().hex[:12].upper()}"

        url = f"{self.BASE_URL}/transaction/initialize"
        data = {
            'email': email,
            'amount': int(amount * 100),  # Convert to kobo
            'reference': reference,
            'callback_url': callback_url or 'http://localhost:5000/payment/callback'
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                return {
                    'success': True,
                    'authorization_url': result['data']['authorization_url'],
                    'access_code': result['data']['access_code'],
                    'reference': result['data']['reference']
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_payment(self, reference):
        """
        Verify a payment transaction.

        Args:
            reference: Transaction reference

        Returns:
            dict with payment details
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                data = result['data']
                return {
                    'success': True,
                    'status': data['status'],
                    'amount': data['amount'] / 100,  # Convert from kobo
                    'reference': data['reference'],
                    'paid_at': data.get('paid_at'),
                    'customer': data.get('customer', {})
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_transfer_recipient(self, account_number, bank_code, name):
        """
        Create a transfer recipient for payouts.

        Args:
            account_number: Bank account number
            bank_code: Bank code (e.g., '058' for GTBank)
            name: Account holder name

        Returns:
            dict with recipient_code
        """
        url = f"{self.BASE_URL}/transferrecipient"
        data = {
            'type': 'nuban',
            'name': name,
            'account_number': account_number,
            'bank_code': bank_code,
            'currency': 'NGN'
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                return {
                    'success': True,
                    'recipient_code': result['data']['recipient_code'],
                    'details': result['data']['details']
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def initiate_transfer(self, recipient_code, amount, reason=None):
        """
        Initiate a bank transfer (withdrawal).

        Args:
            recipient_code: Recipient code from create_transfer_recipient
            amount: Amount in Naira
            reason: Transfer reason/description

        Returns:
            dict with transfer details
        """
        url = f"{self.BASE_URL}/transfer"
        data = {
            'source': 'balance',
            'reason': reason or 'Withdrawal from BITOKI',
            'amount': int(amount * 100),  # Convert to kobo
            'recipient': recipient_code
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                return {
                    'success': True,
                    'transfer_code': result['data']['transfer_code'],
                    'status': result['data']['status'],
                    'reference': result['data']['reference']
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def verify_account_number(self, account_number, bank_code):
        """
        Verify bank account number.

        Args:
            account_number: Bank account number
            bank_code: Bank code

        Returns:
            dict with account name
        """
        url = f"{self.BASE_URL}/bank/resolve"
        params = {
            'account_number': account_number,
            'bank_code': bank_code
        }

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                return {
                    'success': True,
                    'account_name': result['data']['account_name'],
                    'account_number': result['data']['account_number']
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_banks(self):
        """
        Get list of Nigerian banks.

        Returns:
            list of banks with name and code
        """
        url = f"{self.BASE_URL}/bank?currency=NGN"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            if result['status']:
                return {
                    'success': True,
                    'banks': result['data']
                }
            else:
                return {'success': False, 'error': result['message']}

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Nigerian banks (common ones)
NIGERIAN_BANKS = {
    '044': 'Access Bank',
    '023': 'Citibank',
    '063': 'Diamond Bank',
    '050': 'Ecobank',
    '084': 'Enterprise Bank',
    '070': 'Fidelity Bank',
    '011': 'First Bank of Nigeria',
    '214': 'First City Monument Bank',
    '058': 'Guaranty Trust Bank',
    '030': 'Heritage Bank',
    '301': 'Jaiz Bank',
    '082': 'Keystone Bank',
    '526': 'Parallex Bank',
    '076': 'Polaris Bank',
    '101': 'Providus Bank',
    '125': 'Rubies MFB',
    '221': 'Stanbic IBTC Bank',
    '068': 'Standard Chartered',
    '232': 'Sterling Bank',
    '100': 'Suntrust Bank',
    '032': 'Union Bank',
    '033': 'United Bank for Africa',
    '215': 'Unity Bank',
    '035': 'Wema Bank',
    '057': 'Zenith Bank',
}
