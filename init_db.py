"""Initialize the database with all tables."""

from app import app, db
from models import User, Wallet, Transaction, KYCDocument, BankAccount, Trade, GiftCardTrade, SavingsPlan, ActivityLog

def init_database():
    """Create all database tables."""
    with app.app_context():
        # Create all tables
        db.create_all()

        print("SUCCESS: Database tables created successfully!")
        print("\nTables created:")
        print("- users")
        print("- wallets")
        print("- transactions")
        print("- kyc_documents")
        print("- bank_accounts")
        print("- trades")
        print("- giftcard_trades")
        print("- savings_plans")
        print("- activity_logs")

        # Create admin user (optional)
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@bitoki.ng',
                is_active=True,
                email_verified=True,
                kyc_level=3
            )
            admin.set_password('Change_This_Password_123!')
            db.session.add(admin)
            db.session.commit()  # Commit admin first to get ID

            # Create admin wallets
            currencies = ['BTC', 'ETH', 'SOL', 'USDT', 'NGN']
            for currency in currencies:
                wallet = Wallet(user_id=admin.id, currency=currency, balance=0.0)
                db.session.add(wallet)

            db.session.commit()  # Commit wallets
            print("\nSUCCESS: Admin user created!")
            print("   Username: admin")
            print("   Email: admin@bitoki.ng")
            print("   Password: Change_This_Password_123!")
            print("\nWARNING: CHANGE THE ADMIN PASSWORD IMMEDIATELY!")

        print("\nSUCCESS: Database initialization complete!")
        print("\nNext steps:")
        print("1. Update .env with your API keys")
        print("2. Run: python app_prod.py")
        print("3. Visit: http://localhost:5000")
        print("4. Register a new account")

if __name__ == '__main__':
    init_database()
