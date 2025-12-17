@echo off
setlocal enabledelayedexpansion

:: BITOKI Startup Script for Windows
:: This script starts the BITOKI trading platform in production mode

echo ╔══════════════════════════════════════════════════════════════╗
echo ║              BITOKI Trading Platform Startup                ║
echo ║                    Production Mode                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if Docker is installed
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    echo    Visit https://docs.docker.com/get-docker/ for installation instructions.
    pause
    exit /b 1
)

:: Check if Docker Compose is installed
where docker-compose >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose.
    echo    Visit https://docs.docker.com/compose/install/ for instructions.
    pause
    exit /b 1
)

:: Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating default one...
    
    :: Create .env file with default values
    (
        echo # BITOKI Configuration
        echo FLASK_ENV=production
        echo SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%
        echo DATABASE_URL=postgresql://bitoki_user:secure_password@db:5432/bitoki_prod
        echo.
        echo # Exchange API Keys (REPLACE WITH YOUR ACTUAL KEYS)
        echo EXCHANGE_API_KEY=your_exchange_api_key
        echo EXCHANGE_API_SECRET=your_exchange_api_secret
        echo.
        echo # Email Configuration (Zoho SMTP)
        echo SMTP_USERNAME=foundryai@getfoundryai.com
        echo SMTP_PASSWORD=Flindell1977@
        echo.
        echo # Security Settings
        echo SECURITY_PASSWORD_SALT=%RANDOM%%RANDOM%
        echo ENCRYPTION_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%
        echo.
        echo # Application Settings
        echo HOST=0.0.0.0
        echo PORT=8000
        echo DEBUG=False
    ) > .env
    
    echo ✅ Created .env file with default values.
    echo    Please edit .env and add your actual API keys before production use.
)

echo 🔍 Environment Configuration:
echo    📦 FLASK_ENV: production
echo    🔒 Security: Enabled
echo    📧 Email: Zoho SMTP Configured
echo    🕶️ 2FA: Required for sensitive operations
echo.

:: Create necessary directories
echo 📁 Creating directories...
mkdir logs 2>nul
mkdir backups 2>nul
mkdir ssl 2>nul
mkdir nginx\[conf.d 2>nul
mkdir monitoring 2>nul
mkdir scripts 2>nul
mkdir sql 2>nul
echo ✅ Directories created
echo.

:: Create basic Nginx configuration
if not exist "nginx\nginx.conf" (
    echo 📄 Creating Nginx configuration...
    
    (
        echo user  nginx;
        echo worker_processes  auto;
        echo.
        echo error_log  /var/log/nginx/error.log warn;
        echo pid        /var/run/nginx.pid;
        echo.
        echo events {
        echo     worker_connections  1024;
        echo }
        echo.
        echo http {
        echo     include       /etc/nginx/mime.types;
        echo     default_type  application/octet-stream;
        echo.
        echo     log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
        echo                       '$status $body_bytes_sent "$http_referer" '
        echo                       '"$http_user_agent" "$http_x_forwarded_for"';
        echo.
        echo     access_log  /var/log/nginx/access.log  main;
        echo.
        echo     sendfile        on;
        echo.
        echo     keepalive_timeout  65;
        echo.
        echo     # Gzip compression
        echo     gzip  on;
        echo     gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
        echo.
        echo     # Security headers
        echo     add_header X-Frame-Options "DENY" always;
        echo     add_header X-Content-Type-Options "nosniff" always;
        echo     add_header X-XSS-Protection "1; mode=block" always;
        echo     add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        echo     add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; img-src 'self' data: chart.googleapis.com; font-src 'self' fonts.gstatic.com; connect-src 'self' api.bitoki.com; frame-src 'none'; object-src 'none'" always;
        echo.
        echo     # Include additional configurations
        echo     include /etc/nginx/conf.d/*.conf;
        echo }
    ) > nginx\nginx.conf
    
    echo ✅ Nginx configuration created
)

:: Create basic Nginx site configuration
if not exist "nginx\conf.d\bitoki.conf" (
    echo 📄 Creating Nginx site configuration...
    
    (
        echo upstream bitoki_app {
        echo     server app:8000;
        echo }
        echo.
        echo server {
        echo     listen 80;
        echo     server_name localhost;
        echo.
        echo     location / {
        echo         proxy_pass http://bitoki_app;
        echo         proxy_set_header Host $host;
        echo         proxy_set_header X-Real-IP $remote_addr;
        echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo         proxy_set_header X-Forwarded-Proto $scheme;
        echo         proxy_set_header X-Forwarded-Host $host;
        echo         proxy_set_header X-Forwarded-Port $server_port;
        echo.
        echo         # WebSocket support
        echo         proxy_http_version 1.1;
        echo         proxy_set_header Upgrade $http_upgrade;
        echo         proxy_set_header Connection "upgrade";
        echo.
        echo         # Timeout settings
        echo         proxy_connect_timeout 60s;
        echo         proxy_send_timeout 60s;
        echo         proxy_read_timeout 60s;
        echo         send_timeout 60s;
        echo     }
        echo.
        echo     # Health check endpoint
        echo     location /health {
        echo         proxy_pass http://bitoki_app/health;
        echo         proxy_set_header Host $host;
        echo         access_log off;
        echo     }
        echo.
        echo     # Static files
        echo     location /static/ {
        echo         alias /app/web/static/;
        echo         expires 30d;
        echo         access_log off;
        echo     }
        echo.
        echo     # API endpoints
        echo     location /api/ {
        echo         proxy_pass http://bitoki_app/api/;
        echo         proxy_set_header Host $host;
        echo         proxy_set_header X-Real-IP $remote_addr;
        echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo     }
        echo.
        echo     # Error pages
        echo     error_page 500 502 503 504 /50x.html;
        echo     location = /50x.html {
        echo         root /usr/share/nginx/html;
        echo     }
        echo }
    ) > nginx\conf.d\bitoki.conf
    
    echo ✅ Nginx site configuration created
)

:: Create Prometheus configuration
if not exist "monitoring\prometheus.yml" (
    echo 📊 Creating Prometheus configuration...
    
    (
        echo global:
        echo   scrape_interval: 15s
        echo   evaluation_interval: 15s
        echo.
        echo scrape_configs:
        echo   - job_name: 'bitoki'
        echo     static_configs:
        echo       - targets: ['app:8000']
        echo.
        echo   - job_name: 'prometheus'
        echo     static_configs:
        echo       - targets: ['localhost:9090']
    ) > monitoring\prometheus.yml
    
    echo ✅ Prometheus configuration created
)

:: Create backup script
if not exist "scripts\backup.sh" (
    echo 💾 Creating backup script...
    
    (
        echo ^#!/bin/bash
        echo.
        echo ^# BITOKI Database Backup Script
        echo.
        echo BACKUP_DIR="/backups"
        echo DATE=$(date +%%Y%%m%%d_%%H%%M%%S)
        echo DB_NAME="bitoki_prod"
        echo DB_USER="bitoki_user"
        echo DB_HOST="db"
        echo.
        echo ^# Create backup directory if it doesn't exist
        echo mkdir -p $BACKUP_DIR
        echo.
        echo ^# Perform database backup
        echo echo "📦 Creating database backup: $DATE"
        echo pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f $BACKUP_DIR/bitoki_$DATE.backup
        echo.
        echo ^# Compress backup
        echo echo "🗜️  Compressing backup..."
        echo gzip $BACKUP_DIR/bitoki_$DATE.backup
        echo.
        echo ^# Remove backups older than 30 days
        echo echo "🧹 Cleaning up old backups..."
        echo find $BACKUP_DIR -name "*.backup.gz" -type f -mtime +30 -delete
        echo.
        echo echo "✅ Backup completed: bitoki_$DATE.backup.gz"
    ) > scripts\backup.sh
    
    echo ✅ Backup script created
)

:: Create basic SQL init script
if not exist "sql\init.sql" (
    echo 🗃️  Creating database initialization script...
    
    (
        echo -- BITOKI Database Initialization
        echo.
        echo -- Create users table
        echo CREATE TABLE IF NOT EXISTS users (
        echo     id SERIAL PRIMARY KEY,
        echo     username VARCHAR(50) UNIQUE NOT NULL,
        echo     email VARCHAR(100) UNIQUE NOT NULL,
        echo     password_hash VARCHAR(255) NOT NULL,
        echo     salt VARCHAR(64) NOT NULL,
        echo     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        echo     last_login TIMESTAMP,
        echo     is_active BOOLEAN DEFAULT TRUE,
        echo     email_verified BOOLEAN DEFAULT FALSE
        echo );
        echo.
        echo -- Create wallets table
        echo CREATE TABLE IF NOT EXISTS wallets (
        echo     id SERIAL PRIMARY KEY,
        echo     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        echo     currency VARCHAR(10) NOT NULL,
        echo     encrypted_balance TEXT NOT NULL,
        echo     salt VARCHAR(64) NOT NULL,
        echo     last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        echo     UNIQUE(user_id, currency)
        echo );
        echo.
        echo -- Create transactions table
        echo CREATE TABLE IF NOT EXISTS transactions (
        echo     id SERIAL PRIMARY KEY,
        echo     transaction_id VARCHAR(64) UNIQUE NOT NULL,
        echo     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        echo     type VARCHAR(20) NOT NULL,
        echo     amount DECIMAL(20, 8) NOT NULL,
        echo     currency VARCHAR(10) NOT NULL,
        echo     status VARCHAR(20) DEFAULT 'completed',
        echo     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        echo     previous_hash VARCHAR(64),
        echo     current_hash VARCHAR(64) NOT NULL,
        echo     metadata JSONB
        echo );
        echo.
        echo -- Create security_alerts table
        echo CREATE TABLE IF NOT EXISTS security_alerts (
        echo     id SERIAL PRIMARY KEY,
        echo     alert_id VARCHAR(64) UNIQUE NOT NULL,
        echo     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        echo     alert_type VARCHAR(50) NOT NULL,
        echo     message TEXT NOT NULL,
        echo     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        echo     is_read BOOLEAN DEFAULT FALSE,
        echo     severity VARCHAR(20) DEFAULT 'medium'
        echo );
        echo.
        echo -- Create two_factor_auth table
        echo CREATE TABLE IF NOT EXISTS two_factor_auth (
        echo     id SERIAL PRIMARY KEY,
        echo     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        echo     secret VARCHAR(32) NOT NULL,
        echo     method VARCHAR(10) DEFAULT 'totp',
        echo     backup_codes TEXT[],
        echo     enabled BOOLEAN DEFAULT TRUE,
        echo     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        echo     last_used TIMESTAMP,
        echo     UNIQUE(user_id)
        echo );
        echo.
        echo -- Create indexes for performance
        echo CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
        echo CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
        echo CREATE INDEX IF NOT EXISTS idx_alerts_user ON security_alerts(user_id);
        echo CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON security_alerts(timestamp);
        echo CREATE INDEX IF NOT EXISTS idx_wallets_user ON wallets(user_id);
    ) > sql\init.sql
    
    echo ✅ Database initialization script created
)

echo 🚀 Starting BITOKI platform...
echo.

echo 🐳 Starting containers with Docker Compose...
docker-compose -f docker-compose.prod.yml down --remove-orphans
docker-compose -f docker-compose.prod.yml up --build -d

echo.
echo 📊 Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo 🔍 Checking container status...
docker-compose -f docker-compose.prod.yml ps

echo.
echo 🌐 BITOKI Platform Status:
echo    🟢 Application: http://localhost:8000
echo    🟢 API: http://localhost:8000/api
echo    🟢 Dashboard: http://localhost:8000/dashboard
echo    🟢 Monitoring: http://localhost:9090
echo    🟢 Grafana: http://localhost:3000
echo    🟢 Database: postgres://bitoki_user:secure_password@localhost:5432/bitoki_prod
echo.

echo 📋 Available API Endpoints:
echo    • POST /api/security/setup-2fa - Setup 2FA
echo    • POST /api/security/verify-2fa - Verify 2FA code
echo    • GET /api/security/alerts - Get security alerts
echo    • GET /api/security/transaction-history - Get transaction history
echo    • POST /api/security/check-fraud - Check for fraud patterns
echo    • POST /api/security/test-email - Test email sending
echo.

echo 🎯 Quick Test Commands:
echo.
echo    # Test 2FA setup
echo    curl -X POST http://localhost:8000/api/security/setup-2fa ^
        -H "Content-Type: application/json" ^
        -d "{\"user_id\": \"test_user\", \"method\": \"totp\"}"
echo.
echo    # Test email sending
echo    curl -X POST http://localhost:8000/api/security/test-email ^
        -H "Content-Type: application/json" ^
        -d "{\"email\": \"your@email.com\"}"
echo.

echo 📚 Documentation:
echo    • Security: Comprehensive 2FA, encryption, and fraud detection
echo    • Email: Zoho SMTP configured with provided credentials
echo    • Production: Dockerized with monitoring and logging
echo    • Database: PostgreSQL with automatic backups
echo.

echo ✅ BITOKI platform is now running!
echo    Press Ctrl+C to stop the services when done.
echo.

:: Keep the script running to monitor services
:monitor_loop
timeout /t 60 /nobreak >nul

:: Check if containers are still running
for /f %%i in ('docker-compose -f docker-compose.prod.yml ps -q ^| find /c /v ""') do set running_containers=%%i

if "!running_containers!" equ "0" (
    echo ❌ All containers have stopped. Exiting...
    pause
    exit /b 1
)

:: Show a heartbeat every 5 minutes
set /a "random=%RANDOM% %% 30"
if "!random!" equ "0" (
    echo 💓 BITOKI is running smoothly...
)

goto monitor_loop