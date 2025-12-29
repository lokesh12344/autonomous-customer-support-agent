#!/usr/bin/env python3
"""Find Slack bot user and send test message"""

import sys
sys.path.insert(0, '/home/lokesh/autonomous-customer-support-agent')

from app.services.slack_service import slack_service

print("=" * 60)
print("Slack Bot Information")
print("=" * 60)

if not slack_service.enabled:
    print("❌ Slack service is not enabled")
    sys.exit(1)

try:
    # Get bot info
    auth_test = slack_service.client.auth_test()
    print(f"\n✅ Bot Connected!")
    print(f"   Bot User ID: {auth_test['user_id']}")
    print(f"   Bot Name: {auth_test['user']}")
    print(f"   Team: {auth_test['team']}")
    
    bot_user_id = auth_test['user_id']
    
    # Try to send a DM to the bot user (itself)
    print(f"\n📬 Sending test message to bot's DM channel...")
    
    # Open a DM channel with the bot
    im_response = slack_service.client.conversations_open(users=[bot_user_id])
    channel_id = im_response['channel']['id']
    
    print(f"   DM Channel ID: {channel_id}")
    
    # Send test message
    result = slack_service.client.chat_postMessage(
        channel=channel_id,
        text="🤖 Test message from Customer Support Agent!"
    )
    
    print(f"   ✅ Test message sent successfully!")
    print(f"   Message timestamp: {result['ts']}")
    
    print(f"\n💡 To receive notifications in a workspace channel:")
    print(f"   1. Create a channel (e.g., #refunds)")
    print(f"   2. In Slack, type: /invite @{auth_test['user']}")
    print(f"   3. Update .env: SLACK_CHANNEL=refunds")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
