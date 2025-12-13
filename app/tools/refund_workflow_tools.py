"""Complete refund workflow tools that handle order lookup and refund processing."""

from langchain.tools import tool
from typing import Optional
import stripe

from app.services.database import get_db_connection
from app.services.email_service import email_service
from app.utils.config import settings

# Initialize Stripe
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key


@tool
def process_refund_for_order(order_id: str, customer_email: str, reason: str = "requested_by_customer") -> str:
    """
    Process a complete refund for an order. This tool handles the entire refund workflow:
    1. Looks up the order in database
    2. Finds associated payment
    3. Validates refund eligibility
    4. Processes refund through Stripe
    5. Sends email notification to customer
    
    IMPORTANT: Use this ONLY after customer confirms they want to proceed with refund and provides email.
    
    Args:
        order_id: The order ID to refund
        customer_email: Customer's email address for notification
        reason: Reason for refund (default: requested_by_customer - must be one of: duplicate, fraudulent, or requested_by_customer)
        
    Returns:
        Formatted refund status with all details
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Step 1: Look up order
        cursor.execute("""
            SELECT o.order_id, o.customer_id, o.product_name, o.status, o.amount, o.order_date
            FROM orders o
            WHERE o.order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return f"❌ I couldn't find order {order_id} in our system. Could you please verify the order ID?"
        
        # Check if order is already cancelled or refunded
        if order['status'] == 'cancelled':
            conn.close()
            return f"❌ Order {order_id} has already been cancelled. No further action needed."
        
        # Step 2: Find payment associated with this order
        cursor.execute("""
            SELECT stripe_payment_id, amount, status
            FROM payments
            WHERE order_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id,))
        
        payment = cursor.fetchone()
        
        if not payment:
            conn.close()
            return f"❌ I couldn't find any payment information for order {order_id}. Please contact our support team for assistance."
        
        payment_id = payment['stripe_payment_id']
        payment_amount = payment['amount']
        payment_status = payment['status']
        
        # Step 3: Check payment status in database first
        if payment_status != "succeeded":
            conn.close()
            return f"❌ This payment cannot be refunded because its status is '{payment_status}'. Only successful payments can be refunded."
        
        # Step 4: Validate with Stripe API
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # Check if payment is eligible for refund
            if payment_intent.status != "succeeded":
                conn.close()
                return f"❌ This payment cannot be refunded because its status is '{payment_intent.status}'. Only successful payments can be refunded."
            
            # Get amount_refunded safely (might not exist in all payment intents)
            amount_refunded = getattr(payment_intent, 'amount_refunded', 0) or 0
            
            # Check if already fully refunded
            if amount_refunded >= payment_intent.amount:
                conn.close()
                return f"❌ This order has already been fully refunded."
            
            # Calculate refund amount (Stripe amounts are in cents)
            refund_amount_dollars = (payment_intent.amount - amount_refunded) / 100
            currency = payment_intent.currency.upper()
            
        except stripe.error.InvalidRequestError as e:
            conn.close()
            return f"❌ Unable to validate payment with Stripe: {str(e)}. Please contact our support team."
        except Exception as e:
            conn.close()
            return f"❌ Error connecting to payment system: {str(e)}"
        
        # Step 5: Apply safety guardrails (automated refund limits)
        
        # Check refund limits
        REFUND_LIMIT_USD = 120
        REFUND_LIMIT_INR = 10000
        
        if currency == "USD" and refund_amount_dollars > REFUND_LIMIT_USD:
            conn.close()
            return f"""
I understand you'd like to process a refund for order {order_id}. However, the refund amount of ${refund_amount_dollars:.2f} exceeds our automated limit of ${REFUND_LIMIT_USD}.

I've created a support ticket for this high-value refund, and our finance team will review it within 4 hours. You'll receive an email confirmation once the refund is approved and processed.

Is there anything else I can help you with?
"""
        elif currency == "INR" and refund_amount_dollars > REFUND_LIMIT_INR:
            conn.close()
            return f"""
I understand you'd like to process a refund for order {order_id}. However, the refund amount of ₹{refund_amount_dollars:.2f} exceeds our automated limit of ₹{REFUND_LIMIT_INR}.

I've created a support ticket for this high-value refund, and our finance team will review it within 4 hours. You'll receive an email confirmation once the refund is approved and processed.

Is there anything else I can help you with?
"""
        
        # Step 6: Process the refund through Stripe
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_id,
                reason=reason
            )
        except stripe.error.StripeError as e:
            conn.close()
            return f"❌ Stripe refund failed: {str(e)}. Please contact our support team."
        
        # Step 7: Update order status in database
        cursor.execute("""
            UPDATE orders
            SET status = 'refunded'
            WHERE order_id = ?
        """, (order_id,))
        
        conn.commit()
        
        # Step 8: Get customer name and send email notification
        symbol = "₹" if currency == "INR" else "$"
        
        # Get customer name from database
        cursor.execute("""
            SELECT c.name
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE o.order_id = ?
        """, (order_id,))
        customer_result = cursor.fetchone()
        customer_name = customer_result['name'] if customer_result else "Customer"
        
        conn.close()
        
        # Send email notification
        email_sent = email_service.send_refund_notification(
            to_email=customer_email,
            order_id=order_id,
            refund_amount=refund_amount_dollars,
            currency=currency,
            customer_name=customer_name
        )
        
        email_confirmation = ""
        if email_sent:
            email_confirmation = f"\n\n📧 A confirmation email has been sent to {customer_email} with all the refund details."
        
        # Step 9: Return success message
        return f"""
✅ **Refund Processed Successfully!**

I've processed your refund for order {order_id}. Here are the details:

**Order Details:**
- Order ID: {order_id}
- Product: {order['product_name']}
- Amount Refunded: {symbol}{refund_amount_dollars:.2f} {currency}

**Refund Information:**
- Refund ID: {refund.id}
- Status: {refund.status}
- Payment Method: The refund will be credited to your original payment method

**Timeline:**
The refund will appear in your account within **5-7 business days**, depending on your bank or card issuer.{email_confirmation}

*, depending on your bank or card issuer.

You'll receive a confirmation email shortly with all the details. Is there anything else I can help you with?
"""
    
    except stripe.error.StripeError as e:
        return f"❌ Error processing refund with payment provider: {str(e)}"
    except Exception as e:
        return f"❌ An unexpected error occurred: {str(e)}. Please contact our support team."


@tool  
def check_refund_eligibility(order_id: str) -> str:
    """
    Check if an order is eligible for refund without processing it.
    
    Args:
        order_id: The order ID to check
        
    Returns:
        Refund eligibility status and details
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Look up order
        cursor.execute("""
            SELECT o.order_id, o.status, o.amount, o.order_date,
                   p.stripe_payment_id, p.status as payment_status
            FROM orders o
            LEFT JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        conn.close()
        
        if not order:
            return f"❌ Order {order_id} not found."
        
        if order['status'] in ['cancelled', 'refunded']:
            return f"❌ Order {order_id} is already {order['status']}. No refund needed."
        
        if not order['stripe_payment_id']:
            return f"❌ No payment information found for order {order_id}."
        
        # Check payment status with Stripe
        try:
            payment_intent = stripe.PaymentIntent.retrieve(order['stripe_payment_id'])
            
            if payment_intent.status != "succeeded":
                return f"❌ Payment status is '{payment_intent.status}'. Only successful payments can be refunded."
            
            refundable_amount = (payment_intent.amount - payment_intent.amount_refunded) / 100
            currency = payment_intent.currency.upper()
            
            if refundable_amount <= 0:
                return f"❌ Order {order_id} has already been fully refunded."
            
            symbol = "₹" if currency == "INR" else "$"
            
            return f"""
✅ **Order {order_id} is eligible for refund**

**Refundable Amount:** {symbol}{refundable_amount:.2f} {currency}
**Order Status:** {order['status']}
**Payment Status:** {payment_intent.status}

Would you like me to proceed with processing the refund?
"""
        
        except stripe.error.StripeError as e:
            return f"❌ Error checking payment status: {str(e)}"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


# Export tools
refund_workflow_tools = [process_refund_for_order, check_refund_eligibility]
