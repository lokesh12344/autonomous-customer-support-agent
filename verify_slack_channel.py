#!/usr/bin/env python3
"""Verify Slack bot channel access"""

import sys
sys.path.insert(0, '/home/lokesh/autonomous-customer-support-agent')

from app.services.slack_service import slack_service
from app.utils.config import settings

print("=" * 60)
print("Slack Channel Verification")
print("=" * 60)

if not slack_service.enabled:
    print("❌ Slack service is not enabled")
    sys.exit(1)

channel_id = settings.slack_channel
print(f"\nConfigured Channel: {channel_id}")
print(f"Bot User: tpm")

try:
    # Test if we can post to the channel
    print(f"\n📤 Attempting to send test message to channel {channel_id}...")
    
    result = slack_service.client.chat_postMessage(
        channel=channel_id,
        text="🤖 *Test Message from Customer Support Agent*\n\nIf you can see this, Slack integration is working! ✅"
    )
    
    print(f"\n✅ SUCCESS! Message sent to Slack!")
    print(f"   Channel: {channel_id}")
    print(f"   Message TS: {result['ts']}")
    print(f"\n💡 Check your Slack workspace to see the message!")
    
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ FAILED: {error_msg}")
    
    if "channel_not_found" in error_msg:
        print(f"\n🔧 Fix: The bot hasn't been invited to this channel yet!")
        print(f"\n📋 Steps to fix:")
        print(f"   1. Open Slack workspace: https://tpm.slack.com")
        print(f"   2. Go to the channel (or create it)")
        print(f"   3. In the channel, type: /invite @tpm")
        print(f"   4. Press Enter")
        print(f"   5. Run this test again")
    elif "not_in_channel" in error_msg:
        print(f"\n🔧 Fix: Bot needs to be added to the channel")
        print(f"   Type in Slack channel: /invite @tpm")
    elif "invalid_auth" in error_msg:
        print(f"\n🔧 Fix: Check your SLACK_TOKEN in .env")
    else:
        print(f"\n🔧 Check Slack app permissions and try again")

print("\n" + "=" * 60)
