/**
 * WebAuthn/Passkey Frontend Integration
 * Handles passkey registration and authentication
 */

class PasskeyManager {
    constructor() {
        this.isSupported = this.checkSupport();
    }

    /**
     * Check if WebAuthn is supported in this browser
     */
    checkSupport() {
        return window.PublicKeyCredential !== undefined &&
               navigator.credentials !== undefined;
    }

    /**
     * Convert base64url to ArrayBuffer
     */
    base64urlToBuffer(base64url) {
        const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    /**
     * Convert ArrayBuffer to base64url
     */
    bufferToBase64url(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        const base64 = btoa(binary);
        return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    }

    /**
     * Register a new passkey
     */
    async register(passkeyName = '') {
        if (!this.isSupported) {
            throw new Error('WebAuthn is not supported in this browser');
        }

        try {
            // Get registration options from server
            const optionsResponse = await fetch('/passkey/register/options', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!optionsResponse.ok) {
                const error = await optionsResponse.json();
                throw new Error(error.error || 'Failed to get registration options');
            }

            const { options } = await optionsResponse.json();
            const optionsJSON = JSON.parse(options);

            // Convert base64url strings to ArrayBuffers
            const publicKeyCredentialCreationOptions = {
                ...optionsJSON,
                challenge: this.base64urlToBuffer(optionsJSON.challenge),
                user: {
                    ...optionsJSON.user,
                    id: this.base64urlToBuffer(optionsJSON.user.id),
                },
                excludeCredentials: optionsJSON.excludeCredentials?.map(cred => ({
                    ...cred,
                    id: this.base64urlToBuffer(cred.id),
                })) || [],
            };

            // Create credential
            const credential = await navigator.credentials.create({
                publicKey: publicKeyCredentialCreationOptions,
            });

            if (!credential) {
                throw new Error('Failed to create credential');
            }

            // Convert credential to JSON
            const credentialJSON = {
                id: credential.id,
                rawId: this.bufferToBase64url(credential.rawId),
                type: credential.type,
                authenticatorAttachment: credential.authenticatorAttachment,
                response: {
                    clientDataJSON: this.bufferToBase64url(credential.response.clientDataJSON),
                    attestationObject: this.bufferToBase64url(credential.response.attestationObject),
                    transports: credential.response.getTransports ? credential.response.getTransports() : [],
                },
            };

            // Verify registration with server
            const verifyResponse = await fetch('/passkey/register/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: credentialJSON,
                    name: passkeyName,
                }),
            });

            if (!verifyResponse.ok) {
                const error = await verifyResponse.json();
                throw new Error(error.error || 'Failed to verify registration');
            }

            const result = await verifyResponse.json();
            return result;

        } catch (error) {
            console.error('Passkey registration error:', error);
            throw error;
        }
    }

    /**
     * Authenticate with a passkey
     */
    async authenticate(email = null) {
        if (!this.isSupported) {
            throw new Error('WebAuthn is not supported in this browser');
        }

        try {
            // Get authentication options from server
            const optionsResponse = await fetch('/passkey/authenticate/options', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (!optionsResponse.ok) {
                const error = await optionsResponse.json();
                throw new Error(error.error || 'Failed to get authentication options');
            }

            const { options } = await optionsResponse.json();
            const optionsJSON = JSON.parse(options);

            // Convert base64url strings to ArrayBuffers
            const publicKeyCredentialRequestOptions = {
                ...optionsJSON,
                challenge: this.base64urlToBuffer(optionsJSON.challenge),
                allowCredentials: optionsJSON.allowCredentials?.map(cred => ({
                    ...cred,
                    id: this.base64urlToBuffer(cred.id),
                })) || [],
            };

            // Get credential
            const credential = await navigator.credentials.get({
                publicKey: publicKeyCredentialRequestOptions,
            });

            if (!credential) {
                throw new Error('Failed to get credential');
            }

            // Convert credential to JSON
            const credentialJSON = {
                id: credential.id,
                rawId: this.bufferToBase64url(credential.rawId),
                type: credential.type,
                response: {
                    clientDataJSON: this.bufferToBase64url(credential.response.clientDataJSON),
                    authenticatorData: this.bufferToBase64url(credential.response.authenticatorData),
                    signature: this.bufferToBase64url(credential.response.signature),
                    userHandle: credential.response.userHandle
                        ? this.bufferToBase64url(credential.response.userHandle)
                        : null,
                },
            };

            // Verify authentication with server
            const verifyResponse = await fetch('/passkey/authenticate/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    credential: credentialJSON,
                }),
            });

            if (!verifyResponse.ok) {
                const error = await verifyResponse.json();
                throw new Error(error.error || 'Failed to verify authentication');
            }

            const result = await verifyResponse.json();
            return result;

        } catch (error) {
            console.error('Passkey authentication error:', error);
            throw error;
        }
    }

    /**
     * Get list of user's passkeys
     */
    async listPasskeys() {
        try {
            const response = await fetch('/passkey/list');

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to get passkeys');
            }

            const result = await response.json();
            return result.passkeys || [];

        } catch (error) {
            console.error('List passkeys error:', error);
            throw error;
        }
    }

    /**
     * Delete a passkey
     */
    async deletePasskey(passkeyId) {
        try {
            const response = await fetch(`/passkey/delete/${passkeyId}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete passkey');
            }

            const result = await response.json();
            return result;

        } catch (error) {
            console.error('Delete passkey error:', error);
            throw error;
        }
    }
}

// Global instance
const passkeyManager = new PasskeyManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PasskeyManager;
}
