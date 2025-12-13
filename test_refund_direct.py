#!/usr/bin/env python3
"""Direct test of refund functionality"""

import sys
sys.path.insert(0, '/home/lokesh/autonomous-customer-support-agent')

from app.tools.refund_workflow_tools import process_refund_for_order

# Test refund for ORD0044
print("=" * 60)
print("Testing Direct Refund Execution")
print("=" * 60)

result = process_refund_for_order.invoke({
    "order_id": "ORD0044",
    "customer_email": "john.doe@example.com",
    "reason": "requested_by_customer"
})

print("\n" + "=" * 60)
print("RESULT:")
print("=" * 60)
print(result)
