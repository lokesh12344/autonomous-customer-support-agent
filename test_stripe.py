#!/usr/bin/env python3
"""
Test script for Stripe payment tools.
"""

import sys
# Import the underlying functions, not the tool wrappers
from app.tools.stripe_tools import initiate_refund, check_payment_status

# Your test payment ID from Stripe dashboard
TEST_PAYMENT_ID = "pi_3SdalT4b0ymn3LLY1aI0Y1e6"


def test_check_payment_status():
    """Test checking payment status."""
    print("=" * 60)
    print("TEST 1: Checking Payment Status")
    print("=" * 60)
    
    # Call the tool's underlying function
    result = check_payment_status.func(TEST_PAYMENT_ID)
    
    print(f"\n✅ Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    return result


def test_initiate_refund(payment_id, amount=None, reason="Test refund"):
    """Test initiating a refund."""
    print("\n" + "=" * 60)
    print("TEST 2: Initiating Refund")
    print("=" * 60)
    print(f"Payment ID: {payment_id}")
    print(f"Amount: {amount or 'FULL REFUND'}")
    print(f"Reason: {reason}")
    
    # Ask for confirmation before refunding
    confirm = input("\n⚠️  This will actually refund the payment. Continue? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Refund cancelled.")
        return None
    
    # Call the tool's underlying function
    result = initiate_refund.func(payment_id, amount=amount, reason=reason)
    
    print(f"\n✅ Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    return result


def main():
    """Run all tests."""
    print("\n🧪 Stripe Tools Test Suite\n")
    
    # Test 1: Check payment status
    try:
        status_result = test_check_payment_status()
        
        if status_result.get("status") == "error":
            print("\n❌ Payment status check failed!")
            print("Make sure:")
            print("  1. Your Stripe API key is set in .env")
            print("  2. The payment ID is correct")
            print("  3. You're using the correct test/live mode")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error checking payment status: {e}")
        sys.exit(1)
    
    # Test 2: Initiate refund (with confirmation)
    print("\n" + "=" * 60)
    print("Optional: Test Refund")
    print("=" * 60)
    
    test_refund = input("\nDo you want to test the refund function? (yes/no): ")
    
    if test_refund.lower() == "yes":
        # Prompt for partial or full refund
        refund_type = input("Partial or full refund? (partial/full): ")
        
        if refund_type.lower() == "partial":
            amount_str = input("Enter amount in dollars (e.g., 5.00): ")
            try:
                amount = float(amount_str)
            except ValueError:
                print("❌ Invalid amount")
                sys.exit(1)
        else:
            amount = None
        
        try:
            refund_result = test_initiate_refund(
                TEST_PAYMENT_ID,
                amount=amount,
                reason="Testing refund functionality"
            )
        except Exception as e:
            print(f"\n❌ Error initiating refund: {e}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
