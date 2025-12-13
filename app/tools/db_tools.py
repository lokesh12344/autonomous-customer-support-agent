"""Database tools for the ReAct agent."""

from typing import Optional, Dict, Any, List
from langchain.tools import tool
import sqlite3

from app.services.database import get_db_connection


@tool
def fetch_customer(customer_id: str) -> Dict[str, Any]:
    """
    Fetch customer information from the database.
    
    Args:
        customer_id: The unique customer identifier
        
    Returns:
        Dict containing customer information or error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT customer_id, name, email, phone, created_at
            FROM customers
            WHERE customer_id = ?
        """, (customer_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "status": "success",
                "customer_id": row["customer_id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "created_at": row["created_at"]
            }
        else:
            return {
                "status": "not_found",
                "message": f"Customer {customer_id} not found"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def fetch_order(order_id: str) -> Dict[str, Any]:
    """
    Fetch order information from the database.
    
    Args:
        order_id: The unique order identifier
        
    Returns:
        Dict containing order information or error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT order_id, customer_id, product_name, status, amount, order_date
            FROM orders
            WHERE order_id = ?
        """, (order_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "status": "success",
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "product_name": row["product_name"],
                "order_status": row["status"],
                "amount": row["amount"],
                "order_date": row["order_date"]
            }
        else:
            return {
                "status": "not_found",
                "message": f"Order {order_id} not found"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def search_orders_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    """
    Search for all orders by a specific customer.
    
    Args:
        customer_id: The customer ID to search orders for
        
    Returns:
        List of order dictionaries or error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT order_id, product_name, status, amount, order_date
            FROM orders
            WHERE customer_id = ?
            ORDER BY order_date DESC
        """, (customer_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            orders = [
                {
                    "order_id": row["order_id"],
                    "product_name": row["product_name"],
                    "status": row["status"],
                    "amount": row["amount"],
                    "order_date": row["order_date"]
                }
                for row in rows
            ]
            return orders
        else:
            return []
    
    except Exception as e:
        return [{"status": "error", "message": str(e)}]


@tool
def update_order_status(order_id: str, new_status: str) -> Dict[str, Any]:
    """
    Update the status of an order.
    
    Args:
        order_id: The order ID to update
        new_status: New status (e.g., 'processing', 'shipped', 'delivered', 'cancelled')
        
    Returns:
        Dict with update result
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                "status": "not_found",
                "message": f"Order {order_id} not found"
            }
        
        # Update the status
        cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE order_id = ?
        """, (new_status, order_id))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "order_id": order_id,
            "new_status": new_status,
            "message": f"Order {order_id} status updated to {new_status}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# Export tools as a list for easy registration
db_tools = [
    fetch_customer,
    fetch_order,
    search_orders_by_customer,
    update_order_status,
]
