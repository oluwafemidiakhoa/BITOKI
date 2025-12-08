#!/usr/bin/env python
"""Setup verification script for BITOKI trading bot."""

import sys
from pathlib import Path


def check_file(path: str, required: bool = True) -> bool:
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✅" if exists else ("❌" if required else "⚠️ ")
    print(f"{status} {path}: {'Found' if exists else 'Missing'}")
    return exists


def check_env_configured() -> bool:
    """Check if environment variables are configured."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False

    with open(env_file) as f:
        content = f.read()

    has_key = "EXCHANGE_API_KEY=" in content and "your_api_key" not in content.lower()
    has_secret = "EXCHANGE_API_SECRET=" in content and "your_api_secret" not in content.lower()

    if has_key and has_secret:
        print("✅ API credentials appear to be configured")
        return True
    else:
        print("⚠️  API credentials not configured (OK for dry run)")
        return False


def main():
    """Run setup verification."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            BITOKI Setup Verification                          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    all_good = True

    print("\n📁 Checking required files...\n")
    all_good &= check_file("pyproject.toml")
    all_good &= check_file("config/strategy_config.yaml")
    all_good &= check_file("src/bitoki/main.py")
    all_good &= check_file("src/bitoki/strategy.py")
    all_good &= check_file("run.py")

    print("\n📁 Checking optional files...\n")
    check_file(".env", required=False)
    check_file("README.md", required=False)
    check_file("SETUP.md", required=False)

    print("\n🔧 Checking configuration...\n")

    # Check .env
    env_configured = check_env_configured()

    # Check config file
    config_file = Path("config/strategy_config.yaml")
    if config_file.exists():
        with open(config_file) as f:
            config_content = f.read()

        # Check trade mode
        if 'trade_mode: "live"' in config_content:
            print("⚠️  Trade mode set to LIVE - real money at risk!")
        elif 'trade_mode: "dry_run"' in config_content:
            print("✅ Trade mode set to DRY_RUN - safe for testing")
        else:
            print("⚠️  Could not detect trade mode in config")

        # Check sandbox mode
        if "sandbox: true" in config_content:
            print("✅ Sandbox mode enabled - using testnet")
        elif "sandbox: false" in config_content:
            print("⚠️  Sandbox mode disabled - using LIVE exchange")
        else:
            print("⚠️  Could not detect sandbox mode")

    print("\n📦 Checking Python dependencies...\n")

    try:
        import ccxt
        print("✅ ccxt installed")
    except ImportError:
        print("❌ ccxt not installed - run: uv pip install -e .")
        all_good = False

    try:
        import pandas
        print("✅ pandas installed")
    except ImportError:
        print("❌ pandas not installed - run: uv pip install -e .")
        all_good = False

    try:
        import yaml
        print("✅ pyyaml installed")
    except ImportError:
        print("❌ pyyaml not installed - run: uv pip install -e .")
        all_good = False

    try:
        from loguru import logger
        print("✅ loguru installed")
    except ImportError:
        print("❌ loguru not installed - run: uv pip install -e .")
        all_good = False

    print("\n" + "="*60)

    if all_good:
        print("\n✅ Setup verification PASSED!")
        print("\nYou can now run the bot with:")
        print("  uv run python run.py")

        if not env_configured:
            print("\n⚠️  Note: API credentials not configured")
            print("   For live trading, edit .env file with your API keys")
            print("   For testing, you can run in dry_run mode without credentials")

    else:
        print("\n❌ Setup verification FAILED")
        print("\nPlease fix the issues above and run this script again")
        print("For help, see: SETUP.md or README.md")

    print("\n" + "="*60 + "\n")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
