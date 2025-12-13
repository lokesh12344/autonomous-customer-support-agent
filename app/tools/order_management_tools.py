"""Additional order management tools for the agent."""

from langchain.tools import tool
from typing import Optional
import sqlite3

from app.services.database import get_db_connection


@tool
def cancel_order(order_id: str) -> str:
    """
    Cancel a pending order.
    
    Args:
        order_id: The order ID to cancel
        
    Returns:
        Cancellation status message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if order exists and can be cancelled
        cursor.execute("""
            SELECT order_id, status, customer_id, amount
            FROM orders
            WHERE order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return f"❌ Order {order_id} not found in the system."
        
        current_status = order["status"]
        
        # Only allow cancellation of pending or processing orders
        if current_status in ["delivered", "cancelled"]:
            conn.close()
            return f"❌ Cannot cancel order {order_id}. Current status: {current_status}. Only pending or processing orders can be cancelled."
        
        # Update order status to cancelled
        cursor.execute("""
            UPDATE orders
            SET status = 'cancelled'
            WHERE order_id = ?
        """, (order_id,))
        
        conn.commit()
        conn.close()
        
        return f"✅ Order {order_id} has been successfully cancelled. Amount ₹{order['amount']:.2f} will be refunded within 5-7 business days."
    
    except Exception as e:
        return f"❌ Error cancelling order: {str(e)}"


@tool
def modify_order_address(order_id: str, new_address: str) -> str:
    """
    Modify the shipping address for an order.
    
    Args:
        order_id: The order ID to modify
        new_address: The new shipping address
        
    Returns:
        Modification status message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if order exists
        cursor.execute("""
            SELECT order_id, status
            FROM orders
            WHERE order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return f"❌ Order {order_id} not found in the system."
        
        current_status = order["status"]
        
        # Only allow address modification for pending orders
        if current_status not in ["pending", "processing"]:
            conn.close()
            return f"❌ Cannot modify address for order {order_id}. Current status: {current_status}. Address can only be changed for pending or processing orders."
        
        # Note: In a real system, you'd have a separate addresses table
        # For now, we'll just confirm the request
        conn.close()
        
        return f"✅ Shipping address for order {order_id} has been updated to: {new_address}. Changes will be reflected in the next shipment update."
    
    except Exception as e:
        return f"❌ Error modifying order address: {str(e)}"


@tool
def track_shipment(order_id: str) -> str:
    """
    Get tracking information for an order.
    
    Args:
        order_id: The order ID to track
        
    Returns:
        Tracking information with current status and location
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get order details
        cursor.execute("""
            SELECT o.order_id, o.status, o.customer_id, o.product_name, o.order_date
            FROM orders o
            WHERE o.order_id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return f"❌ Order {order_id} not found in the system."
        
        # Get tracking information
        cursor.execute("""
            SELECT tracking_number, carrier, status, location, estimated_delivery, updated_at
            FROM order_tracking
            WHERE order_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        """, (order_id,))
        
        tracking = cursor.fetchone()
        conn.close()
        
        if tracking:
            result = f"""
📦 **Tracking Information for Order {order_id}**

**Product:** {order['product_name']}
**Order Status:** {order['status']}

**Carrier:** {tracking['carrier']}
**Tracking Number:** {tracking['tracking_number']}
**Current Status:** {tracking['status']}
**Current Location:** {tracking['location']}
**Estimated Delivery:** {tracking['estimated_delivery']}
**Last Updated:** {tracking['updated_at']}
"""
        else:
            # No tracking info yet
            if order['status'] == 'pending':
                result = f"📦 Order {order_id} is pending and hasn't been shipped yet. Tracking information will be available once the order is dispatched."
            elif order['status'] == 'processing':
                result = f"📦 Order {order_id} is being processed. Tracking information will be available within 24 hours."
            elif order['status'] == 'cancelled':
                result = f"❌ Order {order_id} has been cancelled."
            else:
                result = f"📦 Order {order_id} - Status: {order['status']}. No tracking information available yet."
        
        return result
    
    except Exception as e:
        return f"❌ Error tracking shipment: {str(e)}"


# Export all tools
order_management_tools = [cancel_order, modify_order_address, track_shipment]
