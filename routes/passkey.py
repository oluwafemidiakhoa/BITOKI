"""Passkey (WebAuthn) authentication routes."""

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user, login_user
from services.passkey_service import passkey_service
from models import User, db

passkey_bp = Blueprint('passkey', __name__)


@passkey_bp.route('/register/options', methods=['POST'])
@login_required
def registration_options():
    """Generate passkey registration options."""
    try:
        options = passkey_service.generate_registration_options(current_user)
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/register/verify', methods=['POST'])
@login_required
def registration_verify():
    """Verify and save passkey registration."""
    try:
        data = request.get_json()
        credential = data.get('credential')
        passkey_name = data.get('name', '')
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr

        result = passkey_service.verify_registration(
            user=current_user,
            credential=credential,
            passkey_name=passkey_name,
            user_agent=user_agent,
            ip_address=ip_address
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Passkey registered successfully!',
                'passkey': result['passkey']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Registration failed')
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/authenticate/options', methods=['POST'])
def authentication_options():
    """Generate passkey authentication options."""
    try:
        data = request.get_json()
        email = data.get('email')

        options = passkey_service.generate_authentication_options(email=email)
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/authenticate/verify', methods=['POST'])
def authentication_verify():
    """Verify passkey authentication and log user in."""
    try:
        data = request.get_json()
        credential = data.get('credential')

        result = passkey_service.verify_authentication(credential=credential)

        if result['success']:
            # Get user and log them in
            user = User.query.get(result['user_id'])
            if user:
                login_user(user, remember=True)
                return jsonify({
                    'success': True,
                    'message': 'Login successful!',
                    'redirect': '/dashboard'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Authentication failed')
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/list', methods=['GET'])
@login_required
def list_passkeys():
    """List all passkeys for current user."""
    try:
        from models_passkey import Passkey
        passkeys = Passkey.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(Passkey.created_at.desc()).all()

        return jsonify({
            'success': True,
            'passkeys': [pk.to_dict() for pk in passkeys]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/delete/<int:passkey_id>', methods=['DELETE'])
@login_required
def delete_passkey(passkey_id):
    """Delete a passkey."""
    try:
        result = passkey_service.delete_passkey(
            passkey_id=passkey_id,
            user_id=current_user.id
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Passkey deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to delete passkey')
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@passkey_bp.route('/manage', methods=['GET'])
@login_required
def manage():
    """Passkey management page."""
    from models_passkey import Passkey
    passkeys = Passkey.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(Passkey.created_at.desc()).all()

    return render_template('security.html', passkeys=passkeys, user=current_user)
