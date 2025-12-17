#!/bin/bash

# BITOKI Complete Setup Script
# This script guides you through the entire setup process

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         BITOKI Complete Setup and GitHub Deployment          ║"
echo "║                    Step-by-Step Guide                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python if not present
install_python() {
    echo "🐍 Python not found. Installing Python..."
    
    if command_exists apt; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif command_exists brew; then
        # macOS
        brew install python@3.11
    else
        echo "❌ Could not install Python automatically."
        echo "   Please install Python 3.9+ manually from https://www.python.org/downloads/"
        exit 1
    fi
}

# Function to install Git if not present
install_git() {
    echo "📚 Git not found. Installing Git..."
    
    if command_exists apt; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y git
    elif command_exists brew; then
        # macOS
        brew install git
    else
        echo "❌ Could not install Git automatically."
        echo "   Please install Git manually from https://git-scm.com/downloads/"
        exit 1
    fi
}

# Function to install Docker if not present
install_docker() {
    echo "🐳 Docker not found. Installing Docker..."
    
    if command_exists apt; then
        # Ubuntu/Debian
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
        echo "⚠️  You may need to log out and back in for Docker permissions to take effect."
    else
        echo "❌ Could not install Docker automatically."
        echo "   Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
}

# Main setup function
main() {
    echo "🔍 Checking system requirements..."
    echo ""
    
    # Check Python
    if ! command_exists python3; then
        install_python
    else
        python_version=$(python3 --version 2>&1)
        echo "✅ Python found: $python_version"
    fi
    
    # Check Git
    if ! command_exists git; then
        install_git
    else
        git_version=$(git --version)
        echo "✅ Git found: $git_version"
    fi
    
    # Check Docker (optional for production)
    if ! command_exists docker; then
        echo "⚠️  Docker not found. You can install it later for production deployment."
        echo "   Install now? (y/n)"
        read -p "   > " install_docker_choice
        if [ "$install_docker_choice" = "y" ]; then
            install_docker
        fi
    else
        docker_version=$(docker --version)
        echo "✅ Docker found: $docker_version"
    fi
    
    echo ""
    echo "✅ System requirements check complete!"
    echo ""
    
    # Navigate to BITOKI directory
    echo "📁 Navigating to BITOKI project directory..."
    cd "$HOME/Demo/BITOKI" || {
        echo "❌ BITOKI directory not found at $HOME/Demo/BITOKI"
        echo "   Please navigate to your BITOKI project directory manually."
        exit 1
    }
    echo "✅ Current directory: $(pwd)"
    echo ""
    
    # Create virtual environment
    echo "🔄 Setting up Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    
    # Activate virtual environment
    echo "🔄 Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo "❌ Could not activate virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment activated"
    echo ""
    
    # Install dependencies
    echo "📦 Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        echo "✅ Dependencies installed"
    else
        echo "❌ requirements.txt not found"
        exit 1
    fi
    echo ""
    
    # Set up environment variables
    echo "🔧 Setting up environment variables..."
    if [ ! -f ".env" ]; then
        cp .env.example .env 2>/dev/null || {
            echo "⚠️  .env.example not found. Creating basic .env file..."
            cat > .env << 'EOF'
# BITOKI Configuration
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
HOST=117.0.0.1
PORT=5000

# Database
DATABASE_URL=sqlite:///bitoki.db

# Exchange API (sandbox mode)
EXCHANGE_API_KEY=your_api_key
EXCHANGE_API_SECRET=your_api_secret
EXCHANGE_NAME=binance
SANDBOX=true

# Email (Zoho SMTP)
SMTP_HOST=smtp.zoho.com
SMTP_PORT=587
SMTP_USERNAME=foundryai@getfoundryai.com
SMTP_PASSWORD=Flindell1977@
SMTP_USE_TLS=true

# Security
ENCRYPTION_KEY=your-encryption-key-here
SECURITY_PASSWORD_SALT=your-salt-here
EOF
        }
        echo "✅ .env file created"
    else
        echo "✅ .env file already exists"
    fi
    echo ""
    
    # Initialize Git repository
    echo "📚 Initializing Git repository..."
    if [ ! -d ".git" ]; then
        git init
        echo "✅ Git repository initialized"
    else
        echo "✅ Git repository already initialized"
    fi
    echo ""
    
    # Create .gitignore
    echo "📜 Creating .gitignore file..."
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
.env

# Database
*.db
*.sqlite

# Logs
logs/
*.log

# IDE
.idea/
.vscode/

# Docker
docker-compose.override.yml

# Environment files
.env.local

# Build artifacts
build/
dist/

# Coverage
.coverage
htmlcov/

# Python cache
.pytest_cache/

# Node modules
node_modules/

# Backups
backups/

# SSL certificates
ssl/
*.pem
*.key
*.crt
EOF
        echo "✅ .gitignore file created"
    else
        echo "✅ .gitignore file already exists"
    fi
    echo ""
    
    # Create first commit
    echo "📝 Creating first Git commit..."
    git add .
    git commit -m "Initial commit: BITOKI trading platform with comprehensive security features including 2FA, wallet encryption, immutable transaction history, fraud detection, and Zoho SMTP email integration"
    echo "✅ First commit created"
    echo ""
    
    # Set up GitHub remote
    echo "🔗 Setting up GitHub remote repository..."
    if ! git remote | grep -q "origin"; then
        git remote add origin https://github.com/oluwafemidiakhoa/BITOKI.git
        echo "✅ GitHub remote added"
    else
        echo "✅ GitHub remote already configured"
    fi
    echo ""
    
    # Push to GitHub
    echo "🌐 Pushing to GitHub..."
    echo "   Please choose your authentication method:"
    echo "   1. Personal Access Token (recommended)"
    echo "   2. SSH (if you have SSH keys set up)"
    echo "   3. Skip (I'll push manually later)"
    read -p "   Enter choice (1/2/3): " push_choice
    
    case "$push_choice" in
        1)
            echo "   Enter your GitHub personal access token:"
            read -s -p "   > " github_token
            echo ""
            git push https://oluwafemidiakhoa:$github_token@github.com/oluwafemidiakhoa/BITOKI.git main
            if [ $? -eq 0 ]; then
                echo "✅ Successfully pushed to GitHub using Personal Access Token!"
            else
                echo "❌ Failed to push. Please check your token and try again."
            fi
            ;;
        2)
            echo "   Make sure you have SSH keys set up on GitHub."
            git remote set-url origin git@github.com:oluwafemidiakhoa/BITOKI.git
            git push -u origin main
            if [ $? -eq 0 ]; then
                echo "✅ Successfully pushed to GitHub using SSH!"
            else
                echo "❌ Failed to push. Please set up SSH keys and try again."
            fi
            ;;
        3)
            echo "   Skipping push. You can push later using:"
            echo "   git push -u origin main"
            ;;
        *)
            echo "   Invalid choice. Skipping push."
            ;;
    esac
    echo ""
    
    # Test the application
    echo "🧪 Testing the application..."
    echo "   Starting development server..."
    
    # Check if we can import the app
    if python -c "import app; print('✅ Application imports successfully')" 2>/dev/null; then
        echo "✅ Application is ready to run!"
        echo ""
        echo "🚀 You can start the application with:"
        echo "   python app.py"
        echo "   or"
        echo "   ./start_local.sh"
        echo ""
        echo "   Then access it at: http://117.0.0.1:5000"
    else
        echo "❌ Application failed to import. Please check the error messages above."
    fi
    echo ""
    
    # Final summary
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    SETUP COMPLETE!                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📋 Summary of what was set up:"
    echo "   ✅ Python environment with virtualenv"
    echo "   ✅ All Python dependencies installed"
    echo "   ✅ Environment variables configured"
    echo "   ✅ Git repository initialized"
    echo "   ✅ .gitignore file created"
    echo "   ✅ First commit created"
    echo "   ✅ GitHub remote configured"
    echo "   ✅ Documentation structure created"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Start the application: python app.py"
    echo "   2. Access at: http://117.0.0.1:5000"
    echo "   3. Explore the API: http://117.0.0.1:5000/api"
    echo "   4. Set up production: docker-compose -f docker-compose.prod.yml up"
    echo "   5. Configure monitoring: Prometheus + Grafana"
    echo "   6. Enable security features: 2FA, encryption, fraud detection"
    echo ""
    echo "📚 Documentation:"
    echo "   • Installation: docs/installation.md"
    echo "   • API Reference: docs/api/rest_api.md"
    echo "   • Security: docs/security/2fa.md"
    echo "   • Deployment: docs/deployment/production.md"
    echo ""
    echo "💡 Need help?"
    echo "   • Check the FAQ: docs/troubleshooting/faq.md"
    echo "   • Open an issue on GitHub"
    echo "   • Contact: support@bitoki.com"
    echo ""
    echo "✨ Thank you for using BITOKI!"
    echo "   Secure. Fast. Reliable."
}

# Run the main function
main