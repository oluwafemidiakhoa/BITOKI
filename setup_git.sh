#!/bin/bash

# BITOKI Git Setup and Push Script
# Configures Git and pushes to GitHub repository

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              BITOKI Git Setup and Deployment                 ║"
echo "║              Pushing to GitHub Repository                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    echo "   Visit https://git-scm.com/downloads for installation."
    exit 1
fi

echo "🔍 Checking Git configuration..."

# Check if user has configured Git
if ! git config --global user.name &> /dev/null; then
    echo "⚠️  Git username not configured. Please set your Git username:"
    read -p "   Enter your name: " git_name
    git config --global user.name "$git_name"
    echo "✅ Git username configured"
fi

if ! git config --global user.email &> /dev/null; then
    echo "⚠️  Git email not configured. Please set your Git email:"
    read -p "   Enter your email: " git_email
    git config --global user.email "$git_email"
    echo "✅ Git email configured"
fi

echo ""
echo "📁 Initializing Git repository..."

# Initialize Git repository if not already initialized
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

echo ""
echo "📜 Creating .gitignore file..."

# Create .gitignore file
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environment
venv/
.env
.env*
.venv

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# IDE
.idea/
.vscode/
*.swp
*.swo

# Mac
.DS_Store

# Windows
Thumbs.db

# Docker
docker-compose.override.yml

# Environment files
.env
.env.local
.env.development
.env.test
.env.production

# Build artifacts
build/
dist/

# Coverage
.coverage
htmlcov/

# Jupyter
.ipynb_checkpoints/

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

# Config overrides
config/local_config.yaml
config/production_config.yaml

# Docker override
docker-compose.override.yml

# IDE specific
.idea/
.vscode/
*.iml

# Python compiled files
*.pyc
*.pyo
*.pyd

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# celery
celerybeat-schedule

# SageMath
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project
.spyderproject
.spyproject

# Rope project
.ropeproject

# mkdocs
/site

# mypy
.mypy_cache/
.dmypy.json

# pytype
.pytype/

# pyright
.pyrightconfig.json
EOF

echo "✅ .gitignore file created"

echo ""
echo "📋 Checking repository status..."

# Check current Git status
git status

echo ""
echo "🔄 Adding files to Git..."

# Add all files to Git
git add .
echo "✅ All files added to Git"

echo ""
echo "💬 Enter commit message:"
read -p "   > " commit_message

if [ -z "$commit_message" ]; then
    commit_message="Initial commit: BITOKI trading platform with security features"
    echo "   Using default commit message: $commit_message"
fi

echo ""
echo "📝 Committing changes..."
git commit -m "$commit_message"
echo "✅ Changes committed"

echo ""
echo "🔗 Setting up remote repository..."

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "   Remote 'origin' already exists"
    git remote -v
else
    # Ask for GitHub repository URL
    echo "   Enter your GitHub repository URL:"
    read -p "   > " repo_url
    
    if [ -z "$repo_url" ]; then
        repo_url="https://github.com/oluwafemidiakhoa/BITOKI.git"
        echo "   Using default repository: $repo_url"
    fi
    
    git remote add origin "$repo_url"
    echo "✅ Remote repository added"
fi

echo ""
echo "🌐 Pushing to GitHub..."

# Push to GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🎉 BITOKI repository is now on GitHub:"
    echo "   https://github.com/oluwafemidiakhoa/BITOKI"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Set up GitHub Actions for CI/CD"
    echo "   2. Configure branch protection rules"
    echo "   3. Add collaborators to your repository"
    echo "   4. Set up GitHub Pages for documentation"
else
    echo "❌ Failed to push to GitHub"
    echo "   Please check your internet connection and GitHub credentials"
    echo "   You may need to set up SSH keys or use a personal access token"
fi

echo ""
echo "📚 Git Setup Complete!"
echo "   Repository: https://github.com/oluwafemidiakhoa/BITOKI"
echo "   Branch: main"
echo "   Status: Ready for collaboration"

echo ""
echo "💡 Tips for GitHub:"
echo "   • Use 'git pull' before making changes to stay updated"
echo "   • Create feature branches: git checkout -b feature/your-feature"
echo "   • Use descriptive commit messages"
echo "   • Set up issues and project boards for task tracking"
echo "   • Enable GitHub Actions for automated testing"

echo ""
echo "✅ Git setup and push completed successfully!"