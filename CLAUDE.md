# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Start development server on 127.0.0.1:5000
./start_local.sh

# Build production image
./build.sh

# Initialize database
python init_db.py
```

### Production Deployment
```bash
# Start production server with Docker Compose
docker-compose -f docker-compose.prod.yml up --build

# Start production Flask app directly
python app_prod.py
```

### Code Quality
```bash
# Format code (configured in pyproject.toml)
black --line-length 100 .

# Lint code (configured in pyproject.toml)
ruff check .

# Run with development dependencies
pip install -e ".[dev]"
```

## Architecture Overview

### Application Structure
- **Flask Web Application**: Main app in `app.py` with modular blueprint architecture
- **Database Layer**: SQLAlchemy models in `models.py` with Flask-Migrate for schema management
- **Security Module**: Comprehensive security manager in `src/bitoki/security/`
- **Trading Engine**: Cryptocurrency trading logic in `src/bitoki/trading/` and `api/trading.py`
- **API Layer**: RESTful APIs for wallet, trading, and giftcard operations in `api/`

### Key Components

#### Security Architecture
- **SecurityManager** (`src/bitoki/security/security_manager.py`): Centralized security operations
  - 2FA (TOTP) with backup codes and QR generation
  - AES-256 wallet encryption with PBKDF2 key derivation
  - Immutable transaction history with SHA-256 chaining
  - Real-time fraud detection and alert system
- **Authentication**: Flask-Login with bcrypt password hashing
- **Passkey Support**: WebAuthn implementation in `routes/passkey.py`

#### Database Models
- **User Model**: Complete user management with KYC levels, 2FA settings
- **Wallet Model**: Multi-currency wallet support with encryption
- **Transaction Model**: Immutable transaction records with cryptographic verification
- **Passkey Models**: WebAuthn credential storage in `models_passkey.py`

#### Trading System
- **Market Data**: Real-time price feeds using CCXT exchange integration
- **Trading Executor**: Automated trading strategies with risk management
- **Pattern Detection**: Technical analysis patterns in `src/bitoki/patterns/`

### Configuration System
- **Environment-based configs**: `config/local_config.yaml`, `config/production_config.yaml`
- **Strategy configs**: `config/strategy_config.yaml` for trading parameters
- **Email configs**: `config/email_config.yaml` for notification settings

## Development Guidelines

### Database Operations
```python
# Initialize new database
python init_db.py

# Add migration after model changes
flask db migrate -m "description"
flask db upgrade
```

### Security Implementation
All security operations should use the SecurityManager:
```python
from src.bitoki.security.security_manager import SecurityManager
security = SecurityManager()

# 2FA operations
security.setup_2fa(user_id, method="totp")
security.verify_2fa_code(user_id, code)

# Wallet encryption
security.encrypt_wallet_balance(user_id, currency, amount, password)
security.decrypt_wallet_balance(user_id, currency, password)
```

### Email Services
Email functionality is handled by `services/email_service.py` with template support:
- Development mode: Emails printed to console (controlled by `config/local_config.yaml`)
- Production mode: SMTP delivery via configured provider

### API Development
- Rate limiting implemented via Flask-Limiter
- CORS enabled for cross-origin requests
- RESTful API structure in `api/` directory
- Authentication required for protected endpoints

## File Structure Notes

### Template Organization
- **Base templates**: `web/templates/base.html`
- **Authentication**: `web/templates/auth/`
- **Dashboard**: `web/templates/dashboard.html`
- **Legal pages**: `web/templates/legal/`

### Static Assets
- **CSS**: `web/static/css/style.css`
- **JavaScript**: `web/static/js/` (includes passkey.js for WebAuthn)
- **Images**: `web/static/images/`

### Deployment Files
- **Docker**: `Dockerfile`, `docker-compose.prod.yml`
- **Render**: `render.yaml` for cloud deployment
- **Nginx**: Custom configuration in `nginx/`

## Environment Variables
Key environment variables used throughout the application:
- `FLASK_ENV`: development/production
- `DATABASE_URL`: Database connection string
- `MAIL_*`: Email service configuration
- `FLASK_SECRET_KEY`: Session encryption key

## Testing
No formal test suite is currently configured. Tests directory exists but is empty. Consider adding:
- Unit tests for SecurityManager operations
- API endpoint testing
- Integration tests for trading functionality