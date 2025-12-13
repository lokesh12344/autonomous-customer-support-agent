#!/usr/bin/env python3
"""
Create real Stripe test payment intents for existing orders.
This script creates actual Stripe PaymentIntents in test mode and updates the database.
"""

import sqlite3
import stripe
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.database import get_db_connection
from app.utils.config import settings

# Initialize Stripe with test API key
if not settings.stripe_api_key:
    print("❌ Error: STRIPE_API_KEY not configured in .env")
    sys.exit(1)

stripe.api_key = settings.stripe_api_key
print(f"✅ Using Stripe API Key: {settings.stripe_api_key[:20]}...")


def create_payment_intent_for_order(order_id, amount, customer_email):
    """Create a real Stripe PaymentIntent for an order."""
    try:
        # Create PaymentIntent in test mode
        # Amount must be in cents (multiply by 100)
        amount_cents = int(amount * 100)
        
        # Use Stripe test card tokens with automatic payment methods
        # Disable redirect-based payment methods to avoid needing return_url
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            payment_method_types=["card"],  # Only card payments, no redirects
            payment_method_data={
                "type": "card",
                "card": {
                    "token": "tok_visa"  # Stripe test token for Visa
                }
            },
            confirm=True,  # Automatically confirm the payment
            description=f"Order {order_id}",
            metadata={
                "order_id": order_id,
                "customer_email": customer_email
            }
        )
        
        return payment_intent
        
    except stripe.error.StripeError as e:
        print(f"  ❌ Stripe error for {order_id}: {str(e)}")
        return None
    except Exception as e:
        print(f"  ❌ Error for {order_id}: {str(e)}")
        return None


def update_database():
    """Update database with real Stripe payment IDs."""
    print("\n🔄 Creating Stripe PaymentIntents for orders...\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all orders with their customers
    cursor.execute("""
        SELECT o.order_id, o.amount, c.email, p.order_id as has_payment
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE o.status = 'delivered'
        ORDER BY o.order_id
    """)
    
    orders = cursor.fetchall()
    total = len(orders)
    success_count = 0
    skip_count = 0
    
    for idx, order in enumerate(orders, 1):
        order_id = order['order_id']
        amount = order['amount']
        email = order['email']
        has_payment = order['has_payment']
        
        print(f"[{idx}/{total}] Processing {order_id} (${amount:.2f})...")
        
        # Create Stripe PaymentIntent
        payment_intent = create_payment_intent_for_order(order_id, amount, email)
        
        if payment_intent:
            payment_id = payment_intent.id
            status = payment_intent.status
            
            # Update or insert payment record
            if has_payment:
                cursor.execute("""
                    UPDATE payments 
                    SET stripe_payment_id = ?, status = ?, amount = ?
                    WHERE order_id = ?
                """, (payment_id, status, amount, order_id))
                print(f"  ✅ Updated: {payment_id} ({status})")
            else:
                cursor.execute("""
                    INSERT INTO payments (order_id, stripe_payment_id, amount, status)
                    VALUES (?, ?, ?, ?)
                """, (order_id, payment_id, amount, status))
                print(f"  ✅ Created: {payment_id} ({status})")
            
            success_count += 1
        else:
            skip_count += 1
            print(f"  ⏭️  Skipped {order_id}")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully created: {success_count} payments")
    print(f"⏭️  Skipped: {skip_count} payments")
    print(f"{'='*60}\n")


def verify_payments():
    """Verify that payments were created correctly."""
    print("🔍 Verifying payments in database...\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN stripe_payment_id LIKE 'pi_%' THEN 1 ELSE 0 END) as real_stripe,
               SUM(CASE WHEN status = 'succeeded' THEN 1 ELSE 0 END) as succeeded
        FROM payments
    """)
    
    stats = cursor.fetchone()
    
    print(f"📊 Payment Statistics:")
    print(f"  Total Payments: {stats['total']}")
    print(f"  Real Stripe IDs: {stats['real_stripe']}")
    print(f"  Succeeded: {stats['succeeded']}")
    
    # Show sample payments
    print(f"\n📋 Sample Payments:")
    cursor.execute("""
        SELECT o.order_id, p.stripe_payment_id, p.amount, p.status
        FROM payments p
        JOIN orders o ON p.order_id = o.order_id
        WHERE p.stripe_payment_id LIKE 'pi_%'
        ORDER BY o.order_id
        LIMIT 5
    """)
    
    for payment in cursor.fetchall():
        print(f"  {payment['order_id']}: {payment['stripe_payment_id']} - ${payment['amount']:.2f} ({payment['status']})")
    
    conn.close()
    print()


def main():
    """Main function."""
    print("="*60)
    print("🚀 Stripe Test Payment Creator")
    print("="*60)
    print("\nThis will create real Stripe PaymentIntents in test mode")
    print("for your orders and update the database.")
    print("\nNote: This uses the Stripe test API key from your .env file.")
    print("="*60)
    
    response = input("\n⚠️  Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cancelled.")
        return
    
    update_database()
    verify_payments()
    
    print("✅ All done! Your orders now have real Stripe payment IDs.")
    print("\n💡 You can now test refunds with the AI agent:")
    print("   'I want refund for ORD0001, email: john.doe@example.com'")
    print()


if __name__ == "__main__":
    main()
