"""
Add payment method columns to payments table and import Stripe payments as new orders
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import stripe
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

def get_db_connection():
    """Get database connection."""
    db_path = project_root / "data" / "db.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

def add_payment_method_columns():
    """Add columns for payment method details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔧 Updating database schema...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(payments)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = [
        ("card_brand", "TEXT"),
        ("card_last4", "TEXT"),
        ("card_exp_month", "INTEGER"),
        ("card_exp_year", "INTEGER"),
        ("payment_method_id", "TEXT"),
        ("card_fingerprint", "TEXT"),
        ("card_country", "TEXT"),
    ]
    
    added_count = 0
    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE payments ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: {col_name}")
                added_count += 1
            except Exception as e:
                print(f"  ⚠️  Column {col_name} might already exist: {e}")
    
    conn.commit()
    conn.close()
    
    if added_count > 0:
        print(f"✅ Added {added_count} new column(s) to payments table\n")
    else:
        print("✅ All columns already exist\n")

def fetch_succeeded_payments_with_details():
    """Fetch all succeeded PaymentIntents with full details from Stripe."""
    print("🔍 Fetching succeeded payments from Stripe...\n")
    
    succeeded_payments = []
    has_more = True
    starting_after = None
    
    while has_more:
        if starting_after:
            payment_intents = stripe.PaymentIntent.list(
                limit=100,
                starting_after=starting_after,
                expand=['data.payment_method']
            )
        else:
            payment_intents = stripe.PaymentIntent.list(
                limit=100,
                expand=['data.payment_method']
            )
        
        for pi in payment_intents.data:
            if pi.status != 'succeeded':
                continue
                
            # Extract payment method details
            payment_method = pi.payment_method
            card_info = {}
            
            if payment_method and hasattr(payment_method, 'card'):
                card = payment_method.card
                card_info = {
                    'payment_method_id': payment_method.id,
                    'card_brand': card.brand,
                    'card_last4': card.last4,
                    'card_exp_month': card.exp_month,
                    'card_exp_year': card.exp_year,
                    'card_fingerprint': card.get('fingerprint', ''),
                    'card_country': card.get('country', 'US')
                }
            
            succeeded_payments.append({
                'id': pi.id,
                'amount': pi.amount / 100,
                'currency': pi.currency.upper(),
                'created': pi.created,
                'description': pi.get('description', ''),
                'customer': pi.get('customer', ''),
                **card_info
            })
        
        has_more = payment_intents.has_more
        if has_more and payment_intents.data:
            starting_after = payment_intents.data[-1].id
    
    return succeeded_payments

def get_next_order_id():
    """Get the next available order ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT order_id FROM orders ORDER BY order_id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        last_id = result[0]
        # Extract number from ORD0001 format
        num = int(last_id[3:]) + 1
        return f"ORD{num:04d}"
    else:
        return "ORD0001"

def create_order_with_payment(payment_data, customer_id="CUST001"):
    """Create a new order and payment record from Stripe data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get next order ID
        order_id = get_next_order_id()
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (order_id, customer_id, order_date, amount, status, product_name)
            VALUES (?, ?, datetime('now'), ?, 'delivered', ?)
        """, (order_id, customer_id, payment_data['amount'], payment_data.get('description', 'Test AI Refund Demo')))
        
        # Create payment with card details
        cursor.execute("""
            INSERT INTO payments (
                order_id, stripe_payment_id, amount, status,
                card_brand, card_last4, card_exp_month, card_exp_year,
                payment_method_id, card_fingerprint, card_country, created_at
            ) VALUES (?, ?, ?, 'succeeded', ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            order_id,
            payment_data['id'],
            payment_data['amount'],
            payment_data.get('card_brand', 'unknown'),
            payment_data.get('card_last4', '0000'),
            payment_data.get('card_exp_month', 12),
            payment_data.get('card_exp_year', 2030),
            payment_data.get('payment_method_id', ''),
            payment_data.get('card_fingerprint', ''),
            payment_data.get('card_country', 'US')
        ))
        
        conn.commit()
        conn.close()
        return order_id
        
    except Exception as e:
        conn.close()
        raise e

def import_stripe_payments():
    """Main import process."""
    print("=" * 70)
    print("📥 Stripe Payment Import Tool (New Orders)")
    print("=" * 70)
    print(f"✅ Using Stripe API Key: {stripe.api_key[:20]}...")
    print()
    
    # Add payment method columns
    add_payment_method_columns()
    
    # Fetch Stripe payments
    stripe_payments = fetch_succeeded_payments_with_details()
    
    if not stripe_payments:
        print("❌ No succeeded payments found in Stripe.")
        return
    
    print(f"✅ Found {len(stripe_payments)} succeeded payment(s) in Stripe:\n")
    
    for i, payment in enumerate(stripe_payments, 1):
        print(f"  {i}. Payment ID: {payment['id']}")
        print(f"     Amount: ${payment['amount']:.2f} {payment['currency']}")
        print(f"     Card: {payment.get('card_brand', 'N/A').title()} •••• {payment.get('card_last4', '0000')}")
        print(f"     Expires: {payment.get('card_exp_month', 'N/A')}/{payment.get('card_exp_year', 'N/A')}")
        print(f"     Description: {payment['description'] or 'Test AI Refund Demo'}")
        print()
    
    print("=" * 70)
    confirm = input("Import all these payments as new orders? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Cancelled.")
        return
    
    print()
    print("💾 Creating orders and importing payments...")
    print("=" * 70)
    
    success_count = 0
    for payment in stripe_payments:
        try:
            order_id = create_order_with_payment(payment)
            print(f"✅ Created {order_id}: ${payment['amount']:.2f} - {payment.get('card_brand', 'card').title()} ****{payment.get('card_last4', '0000')}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to import {payment['id']}: {e}")
    
    print()
    print("=" * 70)
    print(f"✅ Successfully imported {success_count}/{len(stripe_payments)} payment(s)")
    print("=" * 70)
    
    # Show created orders
    print("\n📋 Newly created orders:")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.amount, p.stripe_payment_id, 
               p.card_brand, p.card_last4, p.status
        FROM orders o
        JOIN payments p ON o.order_id = p.order_id
        WHERE p.stripe_payment_id LIKE 'pi_%'
        AND p.stripe_payment_id NOT LIKE 'pi_test_%'
        ORDER BY o.order_id DESC
        LIMIT 10
    """)
    
    orders = cursor.fetchall()
    conn.close()
    
    if orders:
        print()
        for order in orders:
            order_id, amount, payment_id, card_brand, card_last4, status = order
            print(f"  {order_id}: ${amount:.2f} - {card_brand.title()} ****{card_last4} ({status})")
            print(f"    Payment ID: {payment_id}")

if __name__ == "__main__":
    try:
        import_stripe_payments()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(0)
