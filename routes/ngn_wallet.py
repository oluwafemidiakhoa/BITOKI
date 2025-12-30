"""NGN Wallet routes for deposits and withdrawals."""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Wallet, Transaction, BankAccount
from services.paystack_service import PaystackService, NIGERIAN_BANKS
import secrets
from datetime import datetime

ngn_bp = Blueprint('ngn', __name__, url_prefix='/ngn')
paystack = PaystackService()


@ngn_bp.route('/wallet')
@login_required
def wallet():
    """NGN wallet overview page."""
    # Get or create NGN wallet
    ngn_wallet = Wallet.query.filter_by(
        user_id=current_user.id,
        currency='NGN'
    ).first()

    if not ngn_wallet:
        ngn_wallet = Wallet(
            user_id=current_user.id,
            currency='NGN',
            balance=0.0
        )
        db.session.add(ngn_wallet)
        db.session.commit()

    # Get recent transactions
    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        currency='NGN'
    ).order_by(Transaction.created_at.desc()).limit(10).all()

    # Get saved bank accounts
    bank_accounts = BankAccount.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        'ngn/wallet.html',
        wallet=ngn_wallet,
        transactions=transactions,
        bank_accounts=bank_accounts
    )


@ngn_bp.route('/deposit')
@login_required
def deposit_page():
    """NGN deposit page."""
    return render_template('ngn/deposit.html')


@ngn_bp.route('/withdraw')
@login_required
def withdraw_page():
    """NGN withdrawal page."""
    # Get NGN wallet
    ngn_wallet = Wallet.query.filter_by(
        user_id=current_user.id,
        currency='NGN'
    ).first()

    if not ngn_wallet:
        flash('Please create an NGN wallet first', 'error')
        return redirect(url_for('ngn.wallet'))

    # Get saved bank accounts
    bank_accounts = BankAccount.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        'ngn/withdraw.html',
        wallet=ngn_wallet,
        bank_accounts=bank_accounts
    )


@ngn_bp.route('/api/initialize-deposit', methods=['POST'])
@login_required
def initialize_deposit():
    """Initialize NGN deposit via Paystack."""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))

        # Validation
        if amount < 1000:  # Minimum ₦1,000
            return jsonify({
                'success': False,
                'error': 'Minimum deposit amount is ₦1,000'
            }), 400

        if amount > 10000000:  # Maximum ₦10M
            return jsonify({
                'success': False,
                'error': 'Maximum deposit amount is ₦10,000,000'
            }), 400

        # Generate unique reference
        reference = f"BF-DEP-{current_user.id}-{secrets.token_urlsafe(8)}"

        # Initialize payment with Paystack
        payment_result = paystack.initialize_payment(
            email=current_user.email,
            amount_ngn=amount,
            reference=reference
        )

        if not payment_result['success']:
            return jsonify({
                'success': False,
                'error': payment_result.get('error', 'Payment initialization failed')
            }), 500

        # Create pending transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type='deposit',
            currency='NGN',
            amount=amount,
            fee=0.0,  # Paystack charges the payer, not us
            status='pending',
            reference=reference
        )
        db.session.add(transaction)
        db.session.commit()

        # Return payment URL
        payment_data = payment_result['data']['data']
        return jsonify({
            'success': True,
            'authorization_url': payment_data['authorization_url'],
            'reference': payment_data['reference'],
            'access_code': payment_data['access_code']
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ngn_bp.route('/api/verify-deposit/<reference>')
@login_required
def verify_deposit(reference):
    """Verify Paystack deposit and credit wallet."""
    try:
        # Find transaction
        transaction = Transaction.query.filter_by(
            reference=reference,
            user_id=current_user.id
        ).first()

        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

        if transaction.status == 'completed':
            return jsonify({
                'success': True,
                'message': 'Transaction already completed',
                'amount': transaction.amount
            })

        # Verify with Paystack
        verification = paystack.verify_payment(reference)

        if not verification['success']:
            return jsonify({
                'success': False,
                'error': verification.get('error', 'Verification failed')
            }), 400

        # Get or create NGN wallet
        ngn_wallet = Wallet.query.filter_by(
            user_id=current_user.id,
            currency='NGN'
        ).first()

        if not ngn_wallet:
            ngn_wallet = Wallet(
                user_id=current_user.id,
                currency='NGN',
                balance=0.0
            )
            db.session.add(ngn_wallet)

        # Credit wallet
        ngn_wallet.balance += verification['amount']
        ngn_wallet.updated_at = datetime.utcnow()

        # Update transaction
        transaction.status = 'completed'
        transaction.completed_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'₦{verification["amount"]:,.2f} has been credited to your wallet',
            'amount': verification['amount'],
            'new_balance': ngn_wallet.balance
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ngn_bp.route('/api/withdraw', methods=['POST'])
@login_required
def withdraw():
    """Process NGN withdrawal to bank account."""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        bank_account_id = data.get('bank_account_id')

        # Get NGN wallet
        ngn_wallet = Wallet.query.filter_by(
            user_id=current_user.id,
            currency='NGN'
        ).first()

        if not ngn_wallet:
            return jsonify({
                'success': False,
                'error': 'NGN wallet not found'
            }), 404

        # Validation
        if amount < 1000:
            return jsonify({
                'success': False,
                'error': 'Minimum withdrawal amount is ₦1,000'
            }), 400

        # Withdrawal fee (₦100 flat fee)
        withdrawal_fee = 100.0
        total_deduction = amount + withdrawal_fee

        if ngn_wallet.balance < total_deduction:
            return jsonify({
                'success': False,
                'error': f'Insufficient balance. You need ₦{total_deduction:,.2f} (₦{amount:,.2f} + ₦{withdrawal_fee:,.2f} fee)'
            }), 400

        # Get bank account
        bank_account = BankAccount.query.filter_by(
            id=bank_account_id,
            user_id=current_user.id
        ).first()

        if not bank_account:
            return jsonify({
                'success': False,
                'error': 'Bank account not found'
            }), 404

        # Find bank code
        bank_code = next(
            (bank['code'] for bank in NIGERIAN_BANKS if bank['name'] == bank_account.bank_name),
            None
        )

        if not bank_code:
            return jsonify({
                'success': False,
                'error': 'Invalid bank'
            }), 400

        # Create or get recipient on Paystack
        recipient_result = paystack.create_transfer_recipient(
            account_number=bank_account.account_number,
            bank_code=bank_code,
            account_name=bank_account.account_name
        )

        if not recipient_result['success']:
            return jsonify({
                'success': False,
                'error': recipient_result.get('error', 'Failed to create recipient')
            }), 500

        # Generate unique reference
        reference = f"BF-WD-{current_user.id}-{secrets.token_urlsafe(8)}"

        # Initiate transfer
        transfer_result = paystack.initiate_transfer(
            amount_ngn=amount,
            recipient_code=recipient_result['recipient_code'],
            reason=f'Withdrawal by {current_user.username}',
            reference=reference
        )

        if not transfer_result['success']:
            return jsonify({
                'success': False,
                'error': transfer_result.get('error', 'Transfer failed')
            }), 500

        # Deduct from wallet
        ngn_wallet.balance -= total_deduction
        ngn_wallet.updated_at = datetime.utcnow()

        # Create transaction record
        transaction = Transaction(
            user_id=current_user.id,
            type='withdrawal',
            currency='NGN',
            amount=amount,
            fee=withdrawal_fee,
            status='pending',  # Will be updated via webhook
            reference=reference,
            address=f"{bank_account.bank_name} - {bank_account.account_number}"
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Withdrawal of ₦{amount:,.2f} initiated successfully',
            'amount': amount,
            'fee': withdrawal_fee,
            'new_balance': ngn_wallet.balance,
            'reference': reference
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ngn_bp.route('/api/add-bank-account', methods=['POST'])
@login_required
def add_bank_account():
    """Add a new bank account for withdrawals."""
    try:
        data = request.get_json()
        bank_name = data.get('bank_name')
        account_number = data.get('account_number')

        # Find bank code
        bank_code = next(
            (bank['code'] for bank in NIGERIAN_BANKS if bank['name'] == bank_name),
            None
        )

        if not bank_code:
            return jsonify({
                'success': False,
                'error': 'Invalid bank selected'
            }), 400

        # Verify account with Paystack
        verification = paystack.verify_account(account_number, bank_code)

        if not verification['success']:
            return jsonify({
                'success': False,
                'error': 'Could not verify account. Please check account number.'
            }), 400

        # Check if account already exists
        existing = BankAccount.query.filter_by(
            user_id=current_user.id,
            account_number=account_number
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'error': 'This account is already added'
            }), 400

        # Add bank account
        bank_account = BankAccount(
            user_id=current_user.id,
            bank_name=bank_name,
            account_number=account_number,
            account_name=verification['account_name'],
            is_verified=True
        )

        # If this is the first account, make it default
        if BankAccount.query.filter_by(user_id=current_user.id).count() == 0:
            bank_account.is_default = True

        db.session.add(bank_account)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Bank account added successfully',
            'account': {
                'id': bank_account.id,
                'bank_name': bank_account.bank_name,
                'account_number': bank_account.account_number,
                'account_name': bank_account.account_name
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ngn_bp.route('/api/banks')
@login_required
def get_banks():
    """Get list of supported Nigerian banks."""
    return jsonify({
        'success': True,
        'banks': NIGERIAN_BANKS
    })


@ngn_bp.route('/api/paystack-webhook', methods=['POST'])
def paystack_webhook():
    """Handle Paystack webhook events."""
    # This endpoint receives notifications from Paystack
    # about deposit/withdrawal status changes
    # TODO: Implement webhook signature verification
    # TODO: Handle different event types (charge.success, transfer.success, etc.)
    return jsonify({'status': 'received'}), 200
