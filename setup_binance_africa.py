#!/usr/bin/env python3
"""Setup script to configure Binance API for African markets."""

import os
import sys
from pathlib import Path

def setup_binance_for_africa():
    """Interactive setup for Binance API in African markets."""
    
    print("🌍 BITOKI - Binance Setup for Africa")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env first")
        return False
    
    print("📖 Reading current .env configuration...")
    
    # Read current .env
    env_content = env_file.read_text()
    lines = env_content.split('\n')
    
    # Check API key configuration
    api_key_set = any('EXCHANGE_API_KEY=' in line and 'your_api_key_here' not in line for line in lines)
    api_secret_set = any('EXCHANGE_API_SECRET=' in line and 'your_api_secret_here' not in line for line in lines)
    
    print(f"✅ API Key configured: {api_key_set}")
    print(f"✅ API Secret configured: {api_secret_set}")
    
    if not api_key_set or not api_secret_set:
        print("\n🔑 Binance API Setup Required:")
        print("1. Go to https://www.binance.com/en/my/settings/api-management")
        print("2. Create a new API key with these permissions:")
        print("   ✅ Read Info")
        print("   ✅ Spot & Margin Trading")
        print("   ❌ Futures (disabled for safety)")
        print("   ❌ Withdrawals (disabled for security)")
        print()
        
        if input("Do you want to update your API credentials now? (y/n): ").lower() == 'y':
            api_key = input("Enter your Binance API Key: ").strip()
            api_secret = input("Enter your Binance API Secret: ").strip()
            
            if api_key and api_secret:
                # Update .env file
                new_content = []
                for line in lines:
                    if line.startswith('EXCHANGE_API_KEY='):
                        line = f'EXCHANGE_API_KEY={api_key}'
                    elif line.startswith('EXCHANGE_API_SECRET='):
                        line = f'EXCHANGE_API_SECRET={api_secret}'
                    new_content.append(line)
                
                env_file.write_text('\n'.join(new_content))
                print("✅ API credentials updated successfully!")
            else:
                print("❌ Invalid credentials provided")
                return False
    
    # Verify trading mode
    trade_mode = next((line.split('=')[1] for line in lines if line.startswith('TRADE_MODE=')), 'dry_run')
    print(f"📊 Trading Mode: {trade_mode}")
    
    if trade_mode != 'live':
        print("⚠️ Currently in dry_run mode - no real trades will be executed")
        if input("Switch to live trading? (y/n): ").lower() == 'y':
            new_content = []
            for line in lines:
                if line.startswith('TRADE_MODE='):
                    line = 'TRADE_MODE=live'
                new_content.append(line)
            env_file.write_text('\n'.join(new_content))
            print("✅ Switched to live trading mode!")
    
    print("\n🚀 Setup Complete!")
    print("Please restart the application:")
    print("  python app.py")
    print()
    print("🌍 Popular trading pairs for Africa:")
    print("  • BTC/USDT (Most liquid)")
    print("  • ETH/USDT (Popular altcoin)")  
    print("  • BNB/USDT (Lower fees)")
    print("  • SOL/USDT (Fast transactions)")
    
    return True

def test_binance_connection():
    """Test Binance API connection."""
    try:
        import ccxt
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv('EXCHANGE_API_KEY')
        api_secret = os.getenv('EXCHANGE_API_SECRET')
        
        if not api_key or not api_secret or 'your_api' in api_key:
            print("❌ API credentials not configured")
            return False
        
        print("🔗 Testing Binance connection...")
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Test API connection
        balance = exchange.fetch_balance()
        print("✅ Connected to Binance successfully!")
        print(f"📊 Account currencies: {len(balance['info']['balances'])} assets")
        
        # Test market data
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"💰 BTC Price: ${ticker['last']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        if "451" in str(e):
            print("🌍 Note: Some regions may need VPN for initial setup")
        return False

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Setup Binance API")
    print("2. Test connection")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        setup_binance_for_africa()
    elif choice == "2":
        test_binance_connection()
    else:
        print("Invalid choice")