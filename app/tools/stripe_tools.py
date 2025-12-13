"""Stripe payment tools for the ReAct agent."""

import stripe
from typing import Dict, Any, Optional
from langchain.tools import tool

from app.utils.config import settings


# Initialize Stripe with API key from config
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key


@tool
def initiate_refund(payment_id: str, amount: Optional[float] = None, reason: str = "") -> str:
    """
    Initiate a refund for a Stripe payment with safety guardrails.
    
    SAFETY GUARDRAILS:
    - Maximum refund limit: ₹10,000 (INR) or $120 (USD)
    - Requires verification of payment existence
    - Only processes refunds for succeeded payments
    - Validates payment is not already fully refunded
    
    Args:
        payment_id: The Stripe payment intent ID
        amount: Optional partial refund amount in dollars (None for full refund)
        reason: Reason for the refund
        
    Returns:
        Formatted refund status message
    """
    try:
        # Safety Guardrail 1: Verify payment exists
        payment_intent = stripe.PaymentIntent.retrieve(payment_id)
        
        # Safety Guardrail 2: Check payment status
        if payment_intent.status != "succeeded":
            return f"❌ Cannot refund payment {payment_id}. Payment status is '{payment_intent.status}'. Only succeeded payments can be refunded."
        
        # Safety Guardrail 3: Check if already refunded
        if payment_intent.amount_received == 0:
            return f"❌ Payment {payment_id} has already been fully refunded."
        
        # Calculate refund amount
        if amount:
            refund_amount = amount
        else:
            # Full refund: use remaining refundable amount
            refund_amount = (payment_intent.amount - payment_intent.amount_refunded) / 100
        
        # Safety Guardrail 4: Enforce refund limit
        REFUND_LIMIT_USD = 120
        REFUND_LIMIT_INR = 10000
        
        currency = payment_intent.currency.upper()
        
        if currency == "USD" and refund_amount > REFUND_LIMIT_USD:
            return f"❌ Refund amount ${refund_amount:.2f} exceeds maximum limit of ${REFUND_LIMIT_USD}. Please create a support ticket for high-value refunds."
        elif currency == "INR" and refund_amount > REFUND_LIMIT_INR:
            return f"❌ Refund amount ₹{refund_amount:.2f} exceeds maximum limit of ₹{REFUND_LIMIT_INR}. Please create a support ticket for high-value refunds."
        
        # Safety Guardrail 5: Validate refund amount doesn't exceed available
        max_refundable = (payment_intent.amount - payment_intent.amount_refunded) / 100
        if refund_amount > max_refundable:
            return f"❌ Refund amount exceeds available refundable amount. Maximum refundable: {currency} {max_refundable:.2f}"
        
        # Convert amount to cents (Stripe requires integers)
        amount_cents = int(refund_amount * 100)
        
        # Create the refund
        refund = stripe.Refund.create(
            payment_intent=payment_id,
            amount=amount_cents,
            reason=reason or "requested_by_customer"
        )
        
        # Format success response
        symbol = "₹" if currency == "INR" else "$"
        return f"""
✅ **Refund Initiated Successfully**

**Refund ID:** {refund.id}
**Payment ID:** {payment_id}
**Amount:** {symbol}{refund_amount:.2f} {currency}
**Status:** {refund.status}
**Reason:** {reason or 'Customer request'}

The refund has been processed and will appear in the customer's account within 5-7 business days depending on their bank.
"""
        
    except stripe.error.InvalidRequestError as e:
        return f"❌ Invalid refund request: {str(e)}"
    except stripe.error.StripeError as e:
        return f"❌ Stripe error processing refund: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error initiating refund: {str(e)}"


@tool
def check_payment_status(payment_id: str) -> Dict[str, Any]:
    """
    Check the status of a Stripe payment.
    
    Args:
        payment_id: The Stripe payment intent ID
        
    Returns:
        Dict containing payment status and details
    """
    try:
        # Retrieve the payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_id)
        
        # Extract charge information
        charges = payment_intent.get("charges", {}).get("data", [])
        charge_amount = charges[0]["amount"] / 100 if charges else None
        
        # Return structured payment information
        return {
            "payment_id": payment_id,
            "status": payment_intent.status,
            "amount": charge_amount or (payment_intent.amount / 100 if payment_intent.amount else None),
            "currency": payment_intent.currency,
            "customer": payment_intent.get("customer"),
            "description": payment_intent.get("description"),
            "created": payment_intent.created
        }
        
    except stripe.error.InvalidRequestError as e:
        return {
            "status": "error",
            "error_type": "invalid_request",
            "message": str(e)
        }
    except stripe.error.StripeError as e:
        return {
            "status": "error",
            "error_type": "stripe_error",
            "message": str(e)
        }


# Export tools as a list for easy registration
stripe_tools = [
    initiate_refund,
    check_payment_status,
]
