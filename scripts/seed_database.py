#!/usr/bin/env python3
"""
Seed the database with sample data for testing.
"""

import sqlite3
from datetime import datetime, timedelta
import random
from pathlib import Path

from app.services.database import get_db_connection, initialize_db
from app.utils.config import settings


# Sample data
CUSTOMERS = [
    ("CUST001", "John Doe", "john.doe@example.com", "+1-555-0101"),
    ("CUST002", "Jane Smith", "jane.smith@example.com", "+1-555-0102"),
    ("CUST003", "Bob Johnson", "bob.johnson@example.com", "+1-555-0103"),
    ("CUST004", "Alice Williams", "alice.w@example.com", "+1-555-0104"),
    ("CUST005", "Charlie Brown", "charlie.brown@example.com", "+1-555-0105"),
    ("CUST006", "David Miller", "david.miller@example.com", "+1-555-0106"),
    ("CUST007", "Emma Davis", "emma.davis@example.com", "+1-555-0107"),
    ("CUST008", "Frank Wilson", "frank.wilson@example.com", "+1-555-0108"),
    ("CUST009", "Grace Taylor", "grace.taylor@example.com", "+1-555-0109"),
    ("CUST010", "Henry Anderson", "henry.anderson@example.com", "+1-555-0110"),
]

PRODUCTS = [
    "Premium Subscription - Monthly",
    "Premium Subscription - Annual",
    "Enterprise Plan",
    "Consulting Services",
    "Training Package",
    "API Credits - 10K",
    "API Credits - 100K",
    "Custom Integration",
    "Basic Support Plan",
    "Pro Support Plan",
    "Developer Tools Bundle",
    "Analytics Dashboard",
]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

# Products with amounts under $120 for refund testing
AFFORDABLE_PRODUCTS = [
    ("Basic Support Plan", 29.99),
    ("Premium Subscription - Monthly", 49.99),
    ("Developer Tools Bundle", 79.99),
    ("Analytics Dashboard", 89.99),
    ("API Credits - 10K", 39.99),
    ("Training Package", 99.99),
    ("Pro Support Plan", 119.99),
]


def seed_customers():
    """Insert sample customers into the database."""
    print("📝 Seeding customers...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for customer_id, name, email, phone in CUSTOMERS:
        try:
            cursor.execute("""
                INSERT INTO customers (customer_id, name, email, phone)
                VALUES (?, ?, ?, ?)
            """, (customer_id, name, email, phone))
            print(f"  ✅ Added customer: {name}")
        except sqlite3.IntegrityError:
            print(f"  ⏭️  Customer {customer_id} already exists")
    
    conn.commit()
    conn.close()


def seed_orders():
    """Insert sample orders into the database."""
    print("\n📦 Seeding orders...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    order_count = 0
    for i, (customer_id, name, _, _) in enumerate(CUSTOMERS, 1):
        # Each customer has 3-5 orders
        num_orders = random.randint(3, 5)
        
        for j in range(num_orders):
            order_count += 1
            order_id = f"ORD{order_count:04d}"
            
            # 70% chance of affordable product (under $120), 30% chance of expensive
            if random.random() < 0.7:
                product, amount = random.choice(AFFORDABLE_PRODUCTS)
            else:
                product = random.choice(PRODUCTS)
                amount = round(random.uniform(150.00, 999.99), 2)
            
            # Most orders should be "delivered" for refund testing
            if random.random() < 0.7:
                status = "delivered"
            else:
                status = random.choice(ORDER_STATUSES)
            
            # Orders from the past 90 days
            days_ago = random.randint(0, 90)
            order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                cursor.execute("""
                    INSERT INTO orders (order_id, customer_id, product_name, status, amount, order_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, customer_id, product, status, amount, order_date))
                print(f"  ✅ Added order: {order_id} for {name} - {product} (${amount})")
            except sqlite3.IntegrityError:
                print(f"  ⏭️  Order {order_id} already exists")
    
    conn.commit()
    conn.close()


def seed_payments():
    """Insert sample payments linked to orders."""
    print("\n💳 Seeding payments...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all orders
    cursor.execute("SELECT order_id, amount FROM orders")
    orders = cursor.fetchall()
    
    for order in orders:
        order_id = order["order_id"]
        amount = order["amount"]
        
        # Generate a mock Stripe payment ID
        stripe_payment_id = f"pi_test_{order_id.lower()}"
        
        # 90% of payments should be "succeeded" for refund testing
        if random.random() < 0.9:
            status = "succeeded"
        else:
            status = random.choice(["pending", "failed"])
        
        try:
            cursor.execute("""
                INSERT INTO payments (order_id, stripe_payment_id, amount, status)
                VALUES (?, ?, ?, ?)
            """, (order_id, stripe_payment_id, amount, status))
            print(f"  ✅ Added payment: {stripe_payment_id} - ${amount} ({status})")
        except sqlite3.IntegrityError:
            print(f"  ⏭️  Payment for {order_id} already exists")
    
    conn.commit()
    conn.close()


def show_stats():
    """Display database statistics."""
    print("\n📊 Database Statistics:")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM customers")
    customer_count = cursor.fetchone()["count"]
    print(f"  👥 Customers: {customer_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    order_count = cursor.fetchone()["count"]
    print(f"  📦 Orders: {order_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM payments")
    payment_count = cursor.fetchone()["count"]
    print(f"  💳 Payments: {payment_count}")
    
    cursor.execute("SELECT SUM(amount) as total FROM orders")
    total_revenue = cursor.fetchone()["total"]
    print(f"  💰 Total Revenue: ${total_revenue:,.2f}")
    
    conn.close()


def main():
    """Main seeding function."""
    print("🌱 Starting database seeding...\n")
    
    # Initialize database schema first
    print("🔧 Initializing database schema...")
    initialize_db()
    
    # Seed data
    seed_customers()
    seed_orders()
    seed_payments()
    
    # Show statistics
    show_stats()
    
    print("\n✅ Database seeding completed!")
    print("\n💡 Test queries:")
    print("  - Fetch customer: CUST001")
    print("  - Fetch order: ORD0001")
    print("  - Search orders by customer: CUST001")


if __name__ == "__main__":
    main()
