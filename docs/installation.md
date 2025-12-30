# Installation Guide

This guide will help you install and set up the BITfisher trading platform.

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **RAM**: 4GB (8GB recommended for production)
- **Disk Space**: 2GB
- **Processor**: Dual-core 2GHz or better

### Production Requirements
- **Operating System**: Ubuntu 22.04 LTS (recommended)
- **Python**: 3.11
- **RAM**: 8GB+
- **Disk Space**: 10GB+
- **Processor**: Quad-core 2.5GHz or better
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+

## 🐍 Python Installation

### Windows

1. **Download Python**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. **Run installer**: Check "Add Python to PATH"
3. **Verify installation**:
   ```bash
   python --version
   pip --version
   ```

### macOS

```bash
# Install using Homebrew
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

### Linux (Ubuntu/Debian)

```bash
# Update packages
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install additional dependencies
sudo apt install -y build-essential libpq-dev libssl-dev libffi-dev

# Verify installation
python3 --version
pip3 --version
```

## 📦 Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/oluwafemidiakhoa/BITfisher.git
cd BITfisher
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```ini
# Application settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database settings
DATABASE_URL=sqlite:///bitoki.db

# Exchange API (use sandbox for testing)
EXCHANGE_API_KEY=your-api-key
EXCHANGE_API_SECRET=your-api-secret
EXCHANGE_NAME=binance
SANDBOX=True

# Email settings (Zoho SMTP)
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=foundryai@getfoundryai.com
SMTP_PASSWORD=Flindell1977@
SMTP_USE_TLS=True

# Security settings
ENCRYPTION_KEY=your-encryption-key-here
SECURITY_PASSWORD_SALT=your-salt-here
```

## 🚀 Running the Application

### Development Mode

```bash
# Start the development server
python app.py

# Or use the startup script
./start_local.sh
```

The application will be available at: [http://117.0.0.1:5000](http://117.0.0.1:5000)

### Production Mode

```bash
# Use the production startup script
docker-compose -f docker-compose.prod.yml up --build
```

The application will be available at: [http://localhost:8000](http://localhost:8000)

## 📦 Docker Installation

### Install Docker

#### Windows/macOS
Download from: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

#### Linux (Ubuntu)

```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install Docker
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Build and Run with Docker

```bash
# Build the Docker image
docker build -t bitoki .

# Run the container
docker run -d -p 5000:5000 --name bitoki bitoki

# Or use Docker Compose
docker-compose up --build
```

## 🔧 Database Setup

### SQLite (Development)

No setup required - SQLite database will be created automatically.

### PostgreSQL (Production)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE bitoki_prod;"
sudo -u postgres psql -c "CREATE USER bitoki_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bitoki_prod TO bitoki_user;"

# Update .env file
DATABASE_URL=postgresql://bitoki_user:secure_password@localhost:5432/bitoki_prod
```

## 📊 Monitoring Setup

### Prometheus

```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Run Prometheus
./prometheus --config.file=prometheus.yml
```

### Grafana

```bash
# Install Grafana
wget https://dl.grafana.com/oss/release/grafana_10.2.0_amd64.deb
sudo dpkg -i grafana_10.2.0_amd64.deb

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Access Grafana at: [http://localhost:3000](http://localhost:3000) (admin/admin)

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ --cov=src --cov-report=html

# Run specific tests
pytest tests/test_security.py -v
```

## 🔒 Security Setup

### Generate Encryption Keys

```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Configure 2FA

```bash
# Test 2FA setup
curl -X POST http://localhost:5000/api/security/setup-2fa \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "method": "totp"}'
```

## 📚 Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Find and kill process on port 5000
sudo lsof -i :5000
kill -9 <PID>
```

**2. Missing dependencies**
```bash
pip install -r requirements.txt
```

**3. Database connection issues**
```bash
# Check database URL in .env
# Verify database is running
```

**4. Email not sending**
```bash
# Check SMTP settings in .env
# Test with console output first
```

## 🎉 Next Steps

1. **Explore the API**: [http://localhost:5000/api](http://localhost:5000/api)
2. **Set up monitoring**: Configure Prometheus and Grafana
3. **Enable security features**: Configure 2FA and encryption
4. **Deploy to production**: Use Docker for easy deployment
5. **Contribute**: Check out our [contribution guide](development/contributing.md)

---

**Need help?** Check our [FAQ](troubleshooting/faq.md) or open an issue on GitHub.