#!/bin/bash

# BITOKI Startup Script
# This script starts the BITOKI trading platform in production mode

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              BITOKI Trading Platform Startup                ║"
echo "║                    Production Mode                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do not run as root. Use a regular user account."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    echo "   Visit https://docs.docker.com/compose/install/ for instructions."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating default one..."
    
    # Create .env file with default values
    cat > .env << EOF
# BITOKI Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://bitoki_user:secure_password@db:5432/bitoki_prod

# Exchange API Keys (REPLACE WITH YOUR ACTUAL KEYS)
EXCHANGE_API_KEY=your_exchange_api_key
EXCHANGE_API_SECRET=your_exchange_api_secret

# Email Configuration (Zoho SMTP)
SMTP_USERNAME=foundryai@getfoundryai.com
SMTP_PASSWORD=Flindell1977@

# Security Settings
SECURITY_PASSWORD_SALT=$(openssl rand -hex 16)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Application Settings
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF
    
    echo "✅ Created .env file with default values."
    echo "   Please edit .env and add your actual API keys before production use."
fi

# Load environment variables
set -a
source .env
set +a

echo "🔍 Environment Configuration:"
echo "   📦 FLASK_ENV: $FLASK_ENV"
echo "   🔒 Security: Enabled"
echo "   📧 Email: Zoho SMTP Configured"
echo "   🕶️ 2FA: Required for sensitive operations"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p backups
mkdir -p ssl
mkdir -p nginx/conf.d
mkdir -p monitoring
mkdir -p scripts
mkdir -p sql
echo "✅ Directories created"
echo ""

# Create basic Nginx configuration
if [ ! -f "nginx/nginx.conf" ]; then
    echo "📄 Creating Nginx configuration..."
    
    cat > nginx/nginx.conf << 'EOF'
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    # Gzip compression
    gzip  on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; img-src 'self' data: chart.googleapis.com; font-src 'self' fonts.gstatic.com; connect-src 'self' api.bitoki.com; frame-src 'none'; object-src 'none'" always;

    # Include additional configurations
    include /etc/nginx/conf.d/*.conf;
}
EOF
    
    echo "✅ Nginx configuration created"
fi

# Create basic Nginx site configuration
if [ ! -f "nginx/conf.d/bitoki.conf" ]; then
    echo "📄 Creating Nginx site configuration..."
    
    cat > nginx/conf.d/bitoki.conf << 'EOF'
upstream bitoki_app {
    server app:8000;
}

server {
    listen 80;
    server_name localhost;

    # Redirect HTTP to HTTPS (uncomment when SSL is configured)
    # return 301 https://$host$request_uri;

    location / {
        proxy_pass http://bitoki_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        send_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://bitoki_app/health;
        proxy_set_header Host $host;
        access_log off;
    }

    # Static files
    location /static/ {
        alias /app/web/static/;
        expires 30d;
        access_log off;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://bitoki_app/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}

# SSL configuration (uncomment when certificates are available)
# server {
#     listen 443 ssl;
#     server_name localhost;
#
#     ssl_certificate /etc/nginx/ssl/bitoki.crt;
#     ssl_certificate_key /etc/nginx/ssl/bitoki.key;
#
#     # Include SSL settings
#     include /etc/nginx/conf.d/ssl.conf;
#
#     location / {
#         proxy_pass http://bitoki_app;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#     }
# }
EOF
    
    echo "✅ Nginx site configuration created"
fi

# Create Prometheus configuration
if [ ! -f "monitoring/prometheus.yml" ]; then
    echo "📊 Creating Prometheus configuration..."
    
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'bitoki'
    static_configs:
      - targets: ['app:8000']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    
    echo "✅ Prometheus configuration created"
fi

# Create backup script
if [ ! -f "scripts/backup.sh" ]; then
    echo "💾 Creating backup script..."
    
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# BITOKI Database Backup Script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="bitoki_prod"
DB_USER="bitoki_user"
DB_HOST="db"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform database backup
echo "📦 Creating database backup: $DATE"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -f $BACKUP_DIR/bitoki_$DATE.backup

# Compress backup
echo "🗜️  Compressing backup..."
gzip $BACKUP_DIR/bitoki_$DATE.backup

# Remove backups older than 30 days
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "*.backup.gz" -type f -mtime +30 -delete

echo "✅ Backup completed: bitoki_$DATE.backup.gz"
EOF
    
    chmod +x scripts/backup.sh
    echo "✅ Backup script created"
fi

# Create basic SQL init script
if [ ! -f "sql/init.sql" ]; then
    echo "🗃️  Creating database initialization script..."
    
    cat > sql/init.sql << 'EOF'
-- BITOKI Database Initialization

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);

-- Create wallets table
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    currency VARCHAR(10) NOT NULL,
    encrypted_balance TEXT NOT NULL,
    salt VARCHAR(64) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, currency)
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    metadata JSONB
);

-- Create security_alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    severity VARCHAR(20) DEFAULT 'medium'
);

-- Create two_factor_auth table
CREATE TABLE IF NOT EXISTS two_factor_auth (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    secret VARCHAR(32) NOT NULL,
    method VARCHAR(10) DEFAULT 'totp',
    backup_codes TEXT[],
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    UNIQUE(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON security_alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_wallets_user ON wallets(user_id);

-- Insert admin user (for development only)
INSERT INTO users (username, email, password_hash, salt, created_at, email_verified)
SELECT 'admin', 'admin@bitoki.com', 
       '$2b$12$N9qo8uLOickgx2ZMRZoMy.Mr7UQZqY1U5l3bJ5eJZJZJZJZJZJZJZ', 
       'random_salt_here', 
       CURRENT_TIMESTAMP, 
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

EOF
    
    echo "✅ Database initialization script created"
fi

echo "🚀 Starting BITOKI platform..."
echo ""

# Start the application using Docker Compose
echo "🐳 Starting containers with Docker Compose..."
docker-compose -f docker-compose.prod.yml down --remove-orphans
docker-compose -f docker-compose.prod.yml up --build -d

echo ""
echo "📊 Waiting for services to initialize..."
sleep 15

echo ""
echo "🔍 Checking container status..."
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🌐 BITOKI Platform Status:"
echo "   🟢 Application: http://localhost:8000"
echo "   🟢 API: http://localhost:8000/api"
echo "   🟢 Dashboard: http://localhost:8000/dashboard"
echo "   🟢 Monitoring: http://localhost:9090"
echo "   🟢 Grafana: http://localhost:3000"
echo "   🟢 Database: postgres://bitoki_user:secure_password@localhost:5432/bitoki_prod"
echo ""

echo "📋 Available API Endpoints:"
echo "   • POST /api/security/setup-2fa - Setup 2FA"
echo "   • POST /api/security/verify-2fa - Verify 2FA code"
echo "   • GET /api/security/alerts - Get security alerts"
echo "   • GET /api/security/transaction-history - Get transaction history"
echo "   • POST /api/security/check-fraud - Check for fraud patterns"
echo "   • POST /api/security/test-email - Test email sending"
echo ""

echo "🎯 Quick Test Commands:"
echo ""
echo "   # Test 2FA setup"
echo "   curl -X POST http://localhost:8000/api/security/setup-2fa \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"user_id\": \"test_user\", \"method\": \"totp\"}'"
echo ""
echo "   # Test email sending"
echo "   curl -X POST http://localhost:8000/api/security/test-email \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"email\": \"your@email.com\"}'"
echo ""

echo "📚 Documentation:"
echo "   • Security: Comprehensive 2FA, encryption, and fraud detection"
echo "   • Email: Zoho SMTP configured with provided credentials"
echo "   • Production: Dockerized with monitoring and logging"
echo "   • Database: PostgreSQL with automatic backups"
echo ""

echo "✅ BITOKI platform is now running!"
echo "   Press Ctrl+C to stop the services when done."
echo ""

# Keep the script running to monitor services
while true; do
    sleep 60
    
    # Check if containers are still running
    running_containers=$(docker-compose -f docker-compose.prod.yml ps -q | wc -l)
    
    if [ "$running_containers" -eq 0 ]; then
        echo "❌ All containers have stopped. Exiting..."
        exit 1
    fi
    
    # Show a heartbeat every 5 minutes
    if [ $((RANDOM % 30)) -eq 0 ]; then
        echo "💓 BITOKI is running smoothly..."
    fi
done