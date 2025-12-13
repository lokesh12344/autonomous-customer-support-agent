"""
Delete all incomplete PaymentIntents from Stripe test account
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

def delete_all_payment_intents():
    """Delete all PaymentIntents from Stripe test account."""
    print("=" * 60)
    print("🗑️  Stripe Payment Deletion Tool")
    print("=" * 60)
    print(f"✅ Using Stripe API Key: {stripe.api_key[:20]}...")
    print()
    
    # Confirm before proceeding
    confirm = input("⚠️  This will delete ALL PaymentIntents from your Stripe test account.\n   Continue? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Cancelled.")
        return
    
    print()
    print("🔍 Fetching all PaymentIntents...")
    
    deleted_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Fetch all payment intents (Stripe returns max 100 at a time)
        has_more = True
        starting_after = None
        
        while has_more:
            if starting_after:
                payment_intents = stripe.PaymentIntent.list(limit=100, starting_after=starting_after)
            else:
                payment_intents = stripe.PaymentIntent.list(limit=100)
            
            if not payment_intents.data:
                break
            
            for payment_intent in payment_intents.data:
                pi_id = payment_intent.id
                status = payment_intent.status
                amount = payment_intent.amount / 100
                
                try:
                    # Cancel first if it's cancelable, then we won't be able to truly delete
                    # Note: Stripe doesn't allow deleting PaymentIntents, only canceling
                    if status in ['requires_payment_method', 'requires_confirmation', 'requires_action']:
                        stripe.PaymentIntent.cancel(pi_id)
                        print(f"  ✅ Cancelled {pi_id} (${amount:.2f}, {status})")
                        deleted_count += 1
                    elif status == 'canceled':
                        print(f"  ⏭️  Already cancelled {pi_id} (${amount:.2f})")
                        skipped_count += 1
                    else:
                        print(f"  ⏭️  Cannot cancel {pi_id} (${amount:.2f}, {status})")
                        skipped_count += 1
                        
                except stripe.error.StripeError as e:
                    print(f"  ❌ Error with {pi_id}: {str(e)}")
                    error_count += 1
            
            # Check if there are more results
            has_more = payment_intents.has_more
            if has_more and payment_intents.data:
                starting_after = payment_intents.data[-1].id
    
    except stripe.error.StripeError as e:
        print(f"\n❌ Stripe API Error: {str(e)}")
        return
    
    print()
    print("=" * 60)
    print("📊 Summary:")
    print(f"  ✅ Cancelled: {deleted_count} payments")
    print(f"  ⏭️  Skipped: {skipped_count} payments")
    print(f"  ❌ Errors: {error_count} payments")
    print("=" * 60)
    print()
    print("✅ Done! Your Stripe test account is cleaned up.")
    print("   Note: Stripe doesn't allow permanent deletion of PaymentIntents,")
    print("   but cancelled ones won't appear in your active payments list.")

if __name__ == "__main__":
    delete_all_payment_intents()
