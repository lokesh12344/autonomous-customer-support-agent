"""Product replacement workflow tools."""

from langchain.tools import tool
from datetime import datetime
from app.services.database import get_db_connection
from app.services.escalation import EscalationManager
from app.services.email_service import email_service
from app.services.slack_service import slack_service


@tool
def request_product_replacement(input_string: str) -> str:
    """
    Request a product replacement for a delivered order.
    
    This tool creates a support ticket for replacement requests and notifies the support team.
    Valid reasons: 'defective_product', 'wrong_item', 'damaged_delivery', 'quality_issue'
    
    Args:
        input_string: Pipe-separated string "order_id|customer_email|reason"
                     Example: "ORD0001|customer@example.com|defective_product"
                     Reason is optional (default: defective_product)
    
    Returns:
        str: Confirmation message with ticket ID
        
    Example:
        request_product_replacement("ORD0001|customer@example.com|damaged_delivery")
    """
    try:
        # Parse input string
        parts = input_string.split("|")
        if len(parts) < 2:
            return "❌ Invalid input format. Expected: order_id|customer_email|reason"
        
        order_id = parts[0].strip()
        customer_email = parts[1].strip()
        reason = parts[2].strip() if len(parts) > 2 else "defective_product"
        # Validate order exists and is eligible for replacement
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.id, o.order_id, o.amount, o.status, o.product_name, c.email
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            return f"❌ Order {order_id} not found. Please check the order number and try again."
        
        order_status = order[3]
        product_name = order[4] if order[4] else "Unknown Product"
        amount = order[2]
        
        # Check if order is eligible for replacement (must be delivered)
        if order_status not in ["delivered", "shipped"]:
            return f"❌ Order {order_id} is not eligible for replacement. Current status: {order_status}. Only delivered orders can be replaced."
        
        # Map reason codes to human-readable descriptions
        reason_map = {
            "defective_product": "Defective Product",
            "wrong_item": "Wrong Item Received",
            "damaged_delivery": "Damaged During Delivery",
            "quality_issue": "Quality Issue"
        }
        
        reason_description = reason_map.get(reason, reason)
        
        # Create detailed issue description
        issue_description = f"""
**Replacement Request**

Product: {product_name}
Order Amount: ${amount:.2f}
Reason: {reason_description}

Customer has requested a replacement for order {order_id}. Please verify the issue and arrange for:
1. Return/pickup of defective item (if applicable)
2. Shipment of replacement product
3. Customer communication regarding timeline
"""
        
        # Create support ticket with high priority for replacements
        session_id = f"replacement_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        ticket_id = EscalationManager.create_ticket(
            session_id=session_id,
            customer_id=None,
            issue_type="product_replacement",
            description=issue_description.strip(),
            priority="high"  # Replacements are high priority
        )
        
        # Send email notification
        if customer_email:
            email_service.send_ticket_created_notification(
                to_email=customer_email,
                ticket_id=ticket_id,
                order_id=order_id,
                customer_name="Customer"
            )
        
        # Send Slack notification for replacement request
        slack_service.send_replacement_request_notification(
            ticket_id=ticket_id,
            order_id=order_id,
            product_name=product_name,
            reason=reason_description,
            customer_email=customer_email,
            amount=amount
        )
        
        conn.close()
        
        return f"""
✅ **Replacement Request Submitted**

**Ticket ID:** {ticket_id}
**Order ID:** {order_id}
**Product:** {product_name}
**Reason:** {reason_description}

Your replacement request has been submitted to our support team. They will:
1. Review your case within 4 hours
2. Arrange pickup of the defective item (if needed)
3. Ship the replacement product
4. Send you tracking details via email

You'll receive a confirmation email at {customer_email} with next steps.

Is there anything else I can help you with?
"""
        
    except Exception as e:
        return f"❌ Error processing replacement request: {str(e)}"
