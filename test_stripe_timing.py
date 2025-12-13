#!/usr/bin/env python3
"""Test Stripe API response time"""

import sys
import time
sys.path.insert(0, '/home/lokesh/autonomous-customer-support-agent')

import stripe
from dotenv import load_dotenv
import os

load_dotenv()
stripe.api_key = os.getenv('STRIPE_API_KEY')

payment_id = 'pi_3SdyHp6Vp84LvD1J069BuzLO'  # ORD0043

print("=" * 60)
print("Testing Stripe API Response Times")
print("=" * 60)

# Test 1: Retrieve PaymentIntent
print("\n1. Retrieving PaymentIntent...")
start = time.time()
pi = stripe.PaymentIntent.retrieve(payment_id)
elapsed = time.time() - start
print(f"   ✅ Retrieved in {elapsed:.2f} seconds")
print(f"   Amount: ${pi.amount / 100:.2f}, Status: {pi.status}")

# Test 2: Create Refund
print("\n2. Creating Refund...")
start = time.time()
refund = stripe.Refund.create(
    payment_intent=payment_id,
    reason="requested_by_customer"
)
elapsed = time.time() - start
print(f"   ✅ Refund created in {elapsed:.2f} seconds")
print(f"   Refund ID: {refund.id}")
print(f"   Amount: ${refund.amount / 100:.2f}, Status: {refund.status}")

print("\n" + "=" * 60)
print(f"Total Stripe operations time: {elapsed + (time.time() - start):.2f}s")
print("=" * 60)
