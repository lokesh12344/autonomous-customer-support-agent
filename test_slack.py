#!/usr/bin/env python3
"""Test Slack integration"""

import sys
sys.path.insert(0, '/home/lokesh/autonomous-customer-support-agent')

from app.services.slack_service import slack_service

print("=" * 60)
print("Testing Slack Integration")
print("=" * 60)

print(f"\nSlack Enabled: {slack_service.enabled}")

if slack_service.enabled:
    print("\n1. Testing refund notification...")
    result = slack_service.send_refund_notification(
        order_id="ORD0041",
        customer_email="test@example.com",
        refund_amount=69.00,
        currency="USD",
        refund_id="re_test123456",
        channel="#refunds"
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    
    print("\n2. Testing high-value refund alert...")
    result = slack_service.send_high_value_refund_alert(
        order_id="ORD9999",
        customer_email="vip@example.com",
        refund_amount=250.00,
        currency="USD",
        ticket_id="TKT-123",
        channel="#high-value-refunds"
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    
    print("\n3. Testing support ticket notification...")
    result = slack_service.send_support_ticket_notification(
        ticket_id="TKT-456",
        issue="Customer needs help with account",
        customer_email="support@example.com",
        order_id="ORD0042",
        priority="high",
        channel="#support-tickets"
    )
    print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
else:
    print("\n⚠️  Slack service is not enabled. Check your SLACK_TOKEN in .env")

print("\n" + "=" * 60)
