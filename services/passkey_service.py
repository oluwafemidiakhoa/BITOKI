"""Passkey (WebAuthn) service for passwordless authentication."""

import os
import secrets
import base64
from datetime import datetime, timedelta
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
    ResidentKeyRequirement,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from models import db
from models_passkey import Passkey, PasskeyChallenge


class PasskeyService:
    """Handle WebAuthn passkey operations."""

    def __init__(self):
        self.rp_id = os.getenv('WEBAUTHN_RP_ID', 'localhost')  # Relying Party ID (your domain)
        self.rp_name = os.getenv('WEBAUTHN_RP_NAME', 'BITfisher')
        self.origin = os.getenv('APP_URL', 'http://localhost:5000')

    def generate_registration_options(self, user):
        """
        Generate WebAuthn registration options for a user.

        Args:
            user: User object

        Returns:
            dict: Registration options for the client
        """
        # Get existing passkeys to exclude
        existing_passkeys = Passkey.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()

        exclude_credentials = [
            PublicKeyCredentialDescriptor(id=pk.credential_id)
            for pk in existing_passkeys
        ]

        # Generate options
        registration_options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=str(user.id).encode('utf-8'),
            user_name=user.email,
            user_display_name=user.username,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,  # Prefer platform authenticators (Face ID, Touch ID)
                resident_key=ResidentKeyRequirement.PREFERRED,  # Enable discoverable credentials
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
            timeout=300000,  # 5 minutes
        )

        # Store challenge in database
        challenge_str = base64.urlsafe_b64encode(registration_options.challenge).decode('utf-8')

        # Delete old challenges for this user
        PasskeyChallenge.query.filter_by(
            user_id=user.id,
            challenge_type='registration'
        ).delete()

        # Create new challenge
        challenge_record = PasskeyChallenge(
            user_id=user.id,
            challenge=challenge_str,
            challenge_type='registration',
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.session.add(challenge_record)
        db.session.commit()

        return options_to_json(registration_options)

    def verify_registration(self, user, credential, passkey_name=None, user_agent=None, ip_address=None):
        """
        Verify and save a new passkey registration.

        Args:
            user: User object
            credential: Registration credential from client
            passkey_name: Optional friendly name for the passkey
            user_agent: Browser user agent
            ip_address: Client IP address

        Returns:
            dict: Success/error response
        """
        try:
            # Get stored challenge
            challenge_record = PasskeyChallenge.query.filter_by(
                user_id=user.id,
                challenge_type='registration'
            ).order_by(PasskeyChallenge.created_at.desc()).first()

            if not challenge_record or challenge_record.is_expired():
                return {
                    'success': False,
                    'error': 'Challenge expired or not found'
                }

            # Decode challenge
            expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge)

            # Verify registration
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=expected_challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
            )

            # Create passkey record
            passkey = Passkey(
                user_id=user.id,
                credential_id=verification.credential_id,
                public_key=verification.credential_public_key,
                sign_count=verification.sign_count,
                name=passkey_name or self._generate_passkey_name(credential),
                aaguid=verification.aaguid.hex() if verification.aaguid else None,
                device_type=credential.get('authenticatorAttachment', 'cross-platform'),
                user_agent=user_agent,
                ip_address=ip_address,
                is_backup_eligible=verification.credential_backed_up,
                is_backup_state=verification.credential_backed_up,
            )

            # Extract transports
            if 'transports' in credential.get('response', {}).get('transports', []):
                passkey.transports = ','.join(credential['response']['transports'])

            db.session.add(passkey)

            # Delete used challenge
            db.session.delete(challenge_record)

            db.session.commit()

            return {
                'success': True,
                'passkey': passkey.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    def generate_authentication_options(self, email=None):
        """
        Generate WebAuthn authentication options.

        Args:
            email: Optional user email (for conditional UI)

        Returns:
            dict: Authentication options for the client
        """
        # Get user's passkeys if email provided
        allow_credentials = []
        user_id = None

        if email:
            from models import User
            user = User.query.filter_by(email=email).first()
            if user:
                user_id = user.id
                passkeys = Passkey.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()

                allow_credentials = [
                    PublicKeyCredentialDescriptor(
                        id=pk.credential_id,
                        transports=pk.transports.split(',') if pk.transports else []
                    )
                    for pk in passkeys
                ]

        # Generate options
        authentication_options = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
            timeout=300000,  # 5 minutes
        )

        # Store challenge
        challenge_str = base64.urlsafe_b64encode(authentication_options.challenge).decode('utf-8')

        # Delete old challenges
        if user_id:
            PasskeyChallenge.query.filter_by(
                user_id=user_id,
                challenge_type='authentication'
            ).delete()
        elif email:
            PasskeyChallenge.query.filter_by(
                email=email,
                challenge_type='authentication'
            ).delete()

        # Create new challenge
        challenge_record = PasskeyChallenge(
            user_id=user_id,
            email=email,
            challenge=challenge_str,
            challenge_type='authentication',
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.session.add(challenge_record)
        db.session.commit()

        return options_to_json(authentication_options)

    def verify_authentication(self, credential):
        """
        Verify passkey authentication.

        Args:
            credential: Authentication credential from client

        Returns:
            dict: Success/error response with user if successful
        """
        try:
            # Find passkey by credential ID
            credential_id = base64.urlsafe_b64decode(credential['id'])
            passkey = Passkey.query.filter_by(
                credential_id=credential_id,
                is_active=True
            ).first()

            if not passkey:
                return {
                    'success': False,
                    'error': 'Passkey not found'
                }

            # Get stored challenge
            challenge_record = PasskeyChallenge.query.filter_by(
                user_id=passkey.user_id,
                challenge_type='authentication'
            ).order_by(PasskeyChallenge.created_at.desc()).first()

            if not challenge_record or challenge_record.is_expired():
                return {
                    'success': False,
                    'error': 'Challenge expired or not found'
                }

            # Decode challenge
            expected_challenge = base64.urlsafe_b64decode(challenge_record.challenge)

            # Verify authentication
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=expected_challenge,
                expected_origin=self.origin,
                expected_rp_id=self.rp_id,
                credential_public_key=passkey.public_key,
                credential_current_sign_count=passkey.sign_count,
            )

            # Update passkey
            passkey.sign_count = verification.new_sign_count
            passkey.last_used_at = datetime.utcnow()

            # Delete used challenge
            db.session.delete(challenge_record)
            db.session.commit()

            return {
                'success': True,
                'user_id': passkey.user_id,
                'passkey_id': passkey.id
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    def delete_passkey(self, passkey_id, user_id):
        """
        Delete a passkey.

        Args:
            passkey_id: Passkey ID
            user_id: User ID (for authorization)

        Returns:
            dict: Success/error response
        """
        passkey = Passkey.query.filter_by(
            id=passkey_id,
            user_id=user_id
        ).first()

        if not passkey:
            return {
                'success': False,
                'error': 'Passkey not found'
            }

        db.session.delete(passkey)
        db.session.commit()

        return {
            'success': True,
            'message': 'Passkey deleted successfully'
        }

    def _generate_passkey_name(self, credential):
        """Generate a friendly name for a passkey based on credential info."""
        attachment = credential.get('authenticatorAttachment', 'unknown')

        if attachment == 'platform':
            return 'This Device (Face ID/Touch ID)'
        elif attachment == 'cross-platform':
            return 'Security Key'
        else:
            return 'Passkey'


# Global service instance
passkey_service = PasskeyService()
