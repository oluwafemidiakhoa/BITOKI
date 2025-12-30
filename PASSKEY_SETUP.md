# 🔑 Passkey Setup Guide

## Quick Start

Passkey authentication has been fully integrated into BITfisher! Follow these steps to enable it.

---

## 1️⃣ Install Dependencies

```bash
pip install webauthn==2.1.0 cbor2==5.6.2
```

---

## 2️⃣ Initialize Database Tables

Run the migration to create passkey tables:

```bash
# Option 1: Using Flask-Migrate (Recommended)
flask db upgrade

# Option 2: Manual SQL migration
sqlite3 bitoki.db < migrations/add_passkey_tables.sql
```

This creates two new tables:
- `passkeys` - Stores WebAuthn credentials
- `passkey_challenges` - Temporary authentication challenges

---

## 3️⃣ Environment Configuration

Your `.env` file has been updated with:

```bash
WEBAUTHN_RP_ID=127.0.0.1
WEBAUTHN_RP_NAME=BITfisher
APP_URL=http://127.0.0.1:5000
```

**For Production**, update these to:
```bash
WEBAUTHN_RP_ID=yourdomain.com
WEBAUTHN_RP_NAME=BITfisher
APP_URL=https://yourdomain.com
```

---

## 4️⃣ Test the Implementation

### **A. Start the App**
```bash
python app.py
```

### **B. Register a Passkey**
1. Login to your account with password
2. Go to **Security Settings**: http://127.0.0.1:5000/passkey/manage
3. Click **"Add Passkey"**
4. Follow device prompt (Face ID, Touch ID, Windows Hello)
5. Passkey created! ✅

### **C. Test Passkey Login**
1. Logout
2. Go to login page: http://127.0.0.1:5000/auth/login
3. Click **"Sign in with Passkey"** (green button)
4. Device prompts for biometric
5. Logged in! 🎉

---

## 📱 Supported Devices

### **Desktop**
- ✅ **Windows 10+**: Windows Hello (Face, Fingerprint, PIN)
- ✅ **macOS**: Touch ID, Face ID (on supported Macs)
- ✅ **Linux**: FIDO2 security keys (YubiKey, etc.)

### **Mobile**
- ✅ **iOS 16+**: Face ID, Touch ID
- ✅ **Android 9+**: Fingerprint, Face Unlock

### **Hardware Keys**
- ✅ YubiKey 5 Series
- ✅ Google Titan Security Key
- ✅ Feitian ePass FIDO2

---

## 🛠️ API Endpoints

All passkey routes are available at `/passkey/*`:

### **Registration**
```javascript
// Get registration options
POST /passkey/register/options
Response: { success: true, options: {...} }

// Verify registration
POST /passkey/register/verify
Body: { credential: {...}, name: "iPhone 13" }
Response: { success: true, passkey: {...} }
```

### **Authentication**
```javascript
// Get authentication options
POST /passkey/authenticate/options
Body: { email: "user@example.com" } // Optional
Response: { success: true, options: {...} }

// Verify authentication
POST /passkey/authenticate/verify
Body: { credential: {...} }
Response: { success: true, redirect: "/dashboard" }
```

### **Management**
```javascript
// List passkeys
GET /passkey/list
Response: { success: true, passkeys: [...] }

// Delete passkey
DELETE /passkey/delete/:id
Response: { success: true, message: "Passkey deleted" }

// Manage page (UI)
GET /passkey/manage
Response: HTML page
```

---

## 🔐 Security Features

### **What Makes Passkeys Secure?**

1. **Phishing-Proof**: Passkeys only work on your domain (RP_ID)
2. **Device-Bound**: Private key never leaves the user's device
3. **Biometric Protected**: Requires Face ID, Touch ID, or PIN
4. **No Password Storage**: Nothing to leak in a database breach
5. **Replay Protection**: Sign counter prevents credential reuse
6. **Challenge-Response**: Each login uses a unique cryptographic challenge

### **Database Security**

The `passkeys` table stores:
- ✅ `credential_id`: Unique identifier (safe to expose)
- ✅ `public_key`: For signature verification (safe to expose)
- ✅ `sign_count`: Prevents replay attacks
- ❌ **Private key**: NEVER stored (stays on device)

Even if your database is compromised, attackers **cannot** use passkeys because they don't have the private key!

---

## 🎯 User Flow

### **Registration Flow**
```
1. User clicks "Add Passkey"
   ↓
2. Server generates challenge → Stored in DB
   ↓
3. Browser prompts for Face ID/Touch ID
   ↓
4. Device creates keypair (public + private)
   ↓
5. Public key + credential ID sent to server
   ↓
6. Server verifies and stores public key
   ↓
7. Private key stays on device (NEVER transmitted!)
```

### **Authentication Flow**
```
1. User clicks "Sign in with Passkey"
   ↓
2. Server generates challenge → Stored in DB
   ↓
3. Browser prompts for Face ID/Touch ID
   ↓
4. Device signs challenge with private key
   ↓
5. Signature sent to server
   ↓
6. Server verifies signature with public key
   ↓
7. User logged in! ✅
```

---

## 🧪 Testing Checklist

- [ ] Install dependencies (`webauthn`, `cbor2`)
- [ ] Run database migration
- [ ] Start app and login with password
- [ ] Navigate to `/passkey/manage`
- [ ] Add a passkey successfully
- [ ] Logout
- [ ] Login with passkey
- [ ] Add a second passkey (test multiple)
- [ ] Delete a passkey
- [ ] Test passkey login from different device (if available)
- [ ] Check activity logs for passkey events

---

## 🚨 Troubleshooting

### **Error: "WebAuthn is not supported"**
- **Solution**: Use Chrome 67+, Safari 14+, or Edge 18+
- Passkeys require a modern browser with WebAuthn support

### **Error: "Challenge expired or not found"**
- **Solution**: Challenges expire in 5 minutes
- Try again and complete the flow quickly

### **Error: "Passkey not found"**
- **Solution**: You may be using a different device/browser
- Passkeys are device-specific (unless synced via iCloud/Google)

### **Error: "User verification failed"**
- **Solution**: Ensure biometrics are enabled on your device
- Check that Face ID/Touch ID/Windows Hello is set up

### **Testing on localhost**
- Use `127.0.0.1` instead of `localhost` in `.env`
- Some browsers restrict WebAuthn on `localhost`

---

## 📊 Monitoring

Track passkey adoption with these queries:

```sql
-- Total passkeys registered
SELECT COUNT(*) FROM passkeys WHERE is_active = 1;

-- Users with passkeys
SELECT COUNT(DISTINCT user_id) FROM passkeys WHERE is_active = 1;

-- Most used passkeys
SELECT name, last_used_at, sign_count
FROM passkeys
WHERE is_active = 1
ORDER BY sign_count DESC
LIMIT 10;

-- Passkey adoption rate
SELECT
  (SELECT COUNT(DISTINCT user_id) FROM passkeys WHERE is_active = 1) * 100.0 /
  (SELECT COUNT(*) FROM users) as adoption_percentage;
```

---

## 🎓 User Education

Educate users about passkeys:

**What is a Passkey?**
> A passkey is a modern, secure way to sign in without a password. Instead of typing a password, you just use Face ID, Touch ID, or a security key. It's faster, more secure, and impossible to forget!

**How is it more secure than a password?**
> - Passkeys can't be phished (they only work on the real BITfisher website)
> - They can't be stolen in a data breach (your private key never leaves your device)
> - They can't be guessed or brute-forced (no password to crack)
> - They're protected by your biometrics (Face ID, Touch ID)

**Do I still need a password?**
> Yes, as a backup. But once you have a passkey, you can use it as your primary login method!

---

## 🏆 Success Metrics

Target adoption rates:

- **Week 1**: 10% of active users have passkeys
- **Month 1**: 30% of active users have passkeys
- **Month 3**: 60% of active users have passkeys
- **Month 6**: 80% of active users have passkeys

**Why it matters:**
- Fewer password resets (saves support time)
- Reduced account takeovers (better security)
- Faster login times (better UX)

---

## 🔄 Next Steps (Optional Enhancements)

1. **Passkey-Only Accounts**: Allow users to disable password login
2. **Conditional UI**: Auto-prompt passkey on returning users
3. **Device Management**: Show device details (browser, OS)
4. **Backup Passkeys**: Encourage users to add 2+ passkeys
5. **Email Alerts**: Notify when new passkey is added
6. **Admin Dashboard**: Track passkey adoption metrics

---

## 📚 Resources

- [WebAuthn Guide](https://webauthn.guide/)
- [FIDO Alliance](https://fidoalliance.org/)
- [Passkeys.dev](https://passkeys.dev/)
- [Can I Use WebAuthn](https://caniuse.com/webauthn)

---

**Ready to test?** Start with step 1 and enjoy world-class authentication! 🚀
