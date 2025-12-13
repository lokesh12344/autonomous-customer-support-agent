"""
Import real Stripe PaymentIntents into the database
Maps Stripe payments to existing orders
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import stripe
from dotenv import load_dotenv
from app.database import get_db_connection

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

def fetch_all_succeeded_payments():
    """Fetch all succeeded PaymentIntents from Stripe."""
    print("🔍 Fetching succeeded payments from Stripe...")
    
    succeeded_payments = []
    has_more = True
    starting_after = None
    
    while has_more:
        if starting_after:
            payment_intents = stripe.PaymentIntent.list(
                limit=100,
                starting_after=starting_after,
                status='succeeded'
            )
        else:
            payment_intents = stripe.PaymentIntent.list(
                limit=100,
                status='succeeded'
            )
        
        for pi in payment_intents.data:
            succeeded_payments.append({
                'id': pi.id,
                'amount': pi.amount / 100,  # Convert cents to dollars
                'currency': pi.currency.upper(),
                'created': pi.created,
                'description': pi.get('description', ''),
                'customer': pi.get('customer', '')
            })
        
        has_more = payment_intents.has_more
        if has_more and payment_intents.data:
            starting_after = payment_intents.data[-1].id
    
    return succeeded_payments

def get_available_orders():
    """Get orders from database that could receive Stripe payment IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get orders with their current payment info
    cursor.execute("""
        SELECT o.order_id, o.customer_id, o.order_date, o.total_amount, o.status,
               p.stripe_payment_id, p.amount as payment_amount, p.payment_status
        FROM orders o
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE o.status != 'cancelled'
        ORDER BY o.order_date DESC
    """)
    
    orders = cursor.fetchall()
    conn.close()
    
    return orders

def update_payment_in_database(order_id, stripe_payment_id, amount):
    """Update the payment record with real Stripe payment ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update payment record
        cursor.execute("""
            UPDATE payments 
            SET stripe_payment_id = ?, 
                amount = ?,
                payment_status = 'succeeded',
                payment_date = datetime('now')
            WHERE order_id = ?
        """, (stripe_payment_id, amount, order_id))
        
        # Update order status if needed
        cursor.execute("""
            UPDATE orders 
            SET status = 'delivered'
            WHERE order_id = ? AND status = 'pending'
        """, (order_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"❌ Error updating database: {e}")
        return False

def import_payments():
    """Main import process."""
    print("=" * 70)
    print("📥 Stripe Payment Import Tool")
    print("=" * 70)
    print(f"✅ Using Stripe API Key: {stripe.api_key[:20]}...")
    print()
    
    # Fetch Stripe payments
    stripe_payments = fetch_all_succeeded_payments()
    
    if not stripe_payments:
        print("❌ No succeeded payments found in Stripe.")
        return
    
    print(f"✅ Found {len(stripe_payments)} succeeded payment(s) in Stripe:\n")
    
    for i, payment in enumerate(stripe_payments, 1):
        print(f"  {i}. {payment['id']}")
        print(f"     Amount: ${payment['amount']:.2f} {payment['currency']}")
        print(f"     Description: {payment['description'] or 'N/A'}")
        print()
    
    # Fetch database orders
    orders = get_available_orders()
    
    print(f"📋 Found {len(orders)} order(s) in database:\n")
    
    # Group by amount for easier matching
    orders_by_amount = {}
    for order in orders:
        order_id, customer_id, order_date, total_amount, status, stripe_id, payment_amount, payment_status = order
        amount_key = f"${total_amount:.2f}"
        if amount_key not in orders_by_amount:
            orders_by_amount[amount_key] = []
        orders_by_amount[amount_key].append(order)
    
    for amount, order_list in sorted(orders_by_amount.items()):
        print(f"  Amount {amount}: {len(order_list)} order(s)")
        for order in order_list[:3]:  # Show first 3
            order_id, customer_id, _, total_amount, status, stripe_id, _, _ = order
            current_id = stripe_id[:25] + "..." if stripe_id and len(stripe_id) > 25 else stripe_id or "None"
            print(f"    - {order_id} (Customer: {customer_id}, Status: {status}, Current ID: {current_id})")
    
    print()
    print("=" * 70)
    print("💡 Manual Mapping:")
    print("   Enter mappings as: payment_number order_id")
    print("   Example: 1 ORD0001")
    print("   Type 'done' when finished")
    print("=" * 70)
    print()
    
    mappings = []
    while True:
        try:
            user_input = input("Enter mapping (or 'done'): ").strip()
            
            if user_input.lower() == 'done':
                break
            
            parts = user_input.split()
            if len(parts) != 2:
                print("❌ Invalid format. Use: payment_number order_id")
                continue
            
            payment_num = int(parts[0])
            order_id = parts[1].upper()
            
            if payment_num < 1 or payment_num > len(stripe_payments):
                print(f"❌ Payment number must be between 1 and {len(stripe_payments)}")
                continue
            
            # Verify order exists
            order_exists = any(o[0] == order_id for o in orders)
            if not order_exists:
                print(f"❌ Order {order_id} not found in database")
                continue
            
            mappings.append((payment_num - 1, order_id))
            payment = stripe_payments[payment_num - 1]
            print(f"✅ Mapped: {payment['id']} (${payment['amount']:.2f}) → {order_id}")
            
        except ValueError:
            print("❌ Invalid input. Payment number must be a number.")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user.")
            return
    
    if not mappings:
        print("\n❌ No mappings provided. Exiting.")
        return
    
    # Apply mappings
    print()
    print("=" * 70)
    print("💾 Applying mappings to database...")
    print("=" * 70)
    
    success_count = 0
    for payment_idx, order_id in mappings:
        payment = stripe_payments[payment_idx]
        print(f"\n📝 Updating {order_id}...")
        print(f"   Payment ID: {payment['id']}")
        print(f"   Amount: ${payment['amount']:.2f}")
        
        if update_payment_in_database(order_id, payment['id'], payment['amount']):
            print(f"   ✅ Successfully updated")
            success_count += 1
        else:
            print(f"   ❌ Failed to update")
    
    print()
    print("=" * 70)
    print(f"✅ Import complete! Updated {success_count}/{len(mappings)} order(s)")
    print("=" * 70)

if __name__ == "__main__":
    try:
        import_payments()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
        sys.exit(0)
