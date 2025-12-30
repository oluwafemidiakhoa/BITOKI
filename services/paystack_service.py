"""Paystack payment integration for NGN deposits and withdrawals."""

import os
import requests
import secrets
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class PaystackService:
    """Handle Paystack payments for NGN transactions."""

    def __init__(self):
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.public_key = os.getenv('PAYSTACK_PUBLIC_KEY')
        self.base_url = 'https://api.paystack.co'
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def initialize_payment(self, email, amount_ngn, reference=None, callback_url=None):
        """
        Initialize a Paystack payment transaction.

        Args:
            email (str): Customer email
            amount_ngn (float): Amount in Naira
            reference (str): Unique transaction reference
            callback_url (str): URL to redirect after payment

        Returns:
            dict: Payment initialization response
        """
        if not reference:
            reference = f"BF-DEP-{secrets.token_urlsafe(16)}"

        # Paystack accepts amount in kobo (1 NGN = 100 kobo)
        amount_kobo = int(amount_ngn * 100)

        payload = {
            'email': email,
            'amount': amount_kobo,
            'reference': reference,
            'currency': 'NGN',
            'callback_url': callback_url or f"{os.getenv('APP_URL', 'http://127.0.0.1:5000')}/api/wallet/paystack-callback"
        }

        try:
            response = requests.post(
                f'{self.base_url}/transaction/initialize',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def verify_payment(self, reference):
        """
        Verify a payment transaction.

        Args:
            reference (str): Transaction reference

        Returns:
            dict: Verification response
        """
        try:
            response = requests.get(
                f'{self.base_url}/transaction/verify/{reference}',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status'] and data['data']['status'] == 'success':
                return {
                    'success': True,
                    'amount': data['data']['amount'] / 100,  # Convert from kobo to NGN
                    'reference': data['data']['reference'],
                    'paid_at': data['data']['paid_at'],
                    'channel': data['data']['channel'],
                    'customer_email': data['data']['customer']['email']
                }
            else:
                return {
                    'success': False,
                    'error': 'Payment verification failed'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_transfer_recipient(self, account_number, bank_code, account_name):
        """
        Create a transfer recipient for NGN withdrawals.

        Args:
            account_number (str): Bank account number
            bank_code (str): Bank code (e.g., '058' for GTBank)
            account_name (str): Account holder name

        Returns:
            dict: Recipient creation response
        """
        payload = {
            'type': 'nuban',
            'name': account_name,
            'account_number': account_number,
            'bank_code': bank_code,
            'currency': 'NGN'
        }

        try:
            response = requests.post(
                f'{self.base_url}/transferrecipient',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status']:
                return {
                    'success': True,
                    'recipient_code': data['data']['recipient_code'],
                    'details': data['data']['details']
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Failed to create recipient')
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def initiate_transfer(self, amount_ngn, recipient_code, reason=None, reference=None):
        """
        Initiate a transfer (withdrawal) to a bank account.

        Args:
            amount_ngn (float): Amount in Naira
            recipient_code (str): Paystack recipient code
            reason (str): Transfer reason/description
            reference (str): Unique transfer reference

        Returns:
            dict: Transfer response
        """
        if not reference:
            reference = f"BF-WD-{secrets.token_urlsafe(16)}"

        # Paystack accepts amount in kobo
        amount_kobo = int(amount_ngn * 100)

        payload = {
            'source': 'balance',
            'amount': amount_kobo,
            'recipient': recipient_code,
            'reason': reason or 'BITfisher withdrawal',
            'reference': reference,
            'currency': 'NGN'
        }

        try:
            response = requests.post(
                f'{self.base_url}/transfer',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status']:
                return {
                    'success': True,
                    'transfer_code': data['data']['transfer_code'],
                    'reference': data['data']['reference'],
                    'status': data['data']['status']
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Transfer failed')
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def verify_account(self, account_number, bank_code):
        """
        Verify bank account details.

        Args:
            account_number (str): Bank account number
            bank_code (str): Bank code

        Returns:
            dict: Account verification response
        """
        try:
            response = requests.get(
                f'{self.base_url}/bank/resolve',
                params={
                    'account_number': account_number,
                    'bank_code': bank_code
                },
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status']:
                return {
                    'success': True,
                    'account_name': data['data']['account_name'],
                    'account_number': data['data']['account_number']
                }
            else:
                return {
                    'success': False,
                    'error': 'Account verification failed'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_banks(self):
        """
        Get list of Nigerian banks supported by Paystack.

        Returns:
            dict: List of banks
        """
        try:
            response = requests.get(
                f'{self.base_url}/bank',
                params={'country': 'nigeria'},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status']:
                banks = [
                    {
                        'name': bank['name'],
                        'code': bank['code'],
                        'slug': bank['slug']
                    }
                    for bank in data['data']
                ]
                return {
                    'success': True,
                    'banks': banks
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to fetch banks'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_balance(self):
        """
        Get Paystack account balance.

        Returns:
            dict: Balance information
        """
        try:
            response = requests.get(
                f'{self.base_url}/balance',
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data['status']:
                balances = data['data']
                return {
                    'success': True,
                    'balance_ngn': balances[0]['balance'] / 100 if balances else 0
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to fetch balance'
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }


# Common Nigerian Banks with their Paystack codes
NIGERIAN_BANKS = [
    {'name': 'Access Bank', 'code': '044'},
    {'name': 'Citibank Nigeria', 'code': '023'},
    {'name': 'Ecobank Nigeria', 'code': '050'},
    {'name': 'Fidelity Bank', 'code': '070'},
    {'name': 'First Bank of Nigeria', 'code': '011'},
    {'name': 'First City Monument Bank (FCMB)', 'code': '214'},
    {'name': 'Guaranty Trust Bank (GTBank)', 'code': '058'},
    {'name': 'Heritage Bank', 'code': '030'},
    {'name': 'Keystone Bank', 'code': '082'},
    {'name': 'Polaris Bank', 'code': '076'},
    {'name': 'Providus Bank', 'code': '101'},
    {'name': 'Stanbic IBTC Bank', 'code': '221'},
    {'name': 'Standard Chartered Bank', 'code': '068'},
    {'name': 'Sterling Bank', 'code': '232'},
    {'name': 'Union Bank of Nigeria', 'code': '032'},
    {'name': 'United Bank for Africa (UBA)', 'code': '033'},
    {'name': 'Unity Bank', 'code': '215'},
    {'name': 'Wema Bank', 'code': '035'},
    {'name': 'Zenith Bank', 'code': '057'},
    {'name': 'Kuda Bank', 'code': '50211'},
    {'name': 'OPay', 'code': '999992'},
    {'name': 'PalmPay', 'code': '999991'},
]
