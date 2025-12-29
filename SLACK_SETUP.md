# Slack Integration Setup

## Overview
The system sends real-time notifications to Slack for:
- ✅ **Refund Processing** - Automated refunds with order details
- 🚨 **High-Value Refund Alerts** - Manual approval requests for amounts > $120
- 🎫 **Support Tickets** - New ticket creations with priority levels

## Setup Instructions

### 1. Create a Slack App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name your app (e.g., "Customer Support Bot")
4. Select your workspace

### 2. Configure Bot Token Scopes
Go to **OAuth & Permissions** and add these scopes:
- `chat:write` - Send messages
- `chat:write.customize` - Customize message appearance
- `channels:history` - Read channel messages
- `groups:history` - Read private channel messages
- `im:history` - Read direct messages

### 3. Install App to Workspace
1. In **OAuth & Permissions**, click **"Install to Workspace"**
2. Authorize the app
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 4. Get Signing Secret
1. Go to **Basic Information**
2. Under **App Credentials**, find **Signing Secret**
3. Click **Show** and copy it

### 5. Update .env File
```bash
SLACK_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_CHANNEL=general  # Default channel name
```

### 6. Invite Bot to Channels
In Slack, invite your bot to any channel:
```
/invite @YourBotName
```

## Testing Slack Integration

Run the test script:
```bash
python3 test_slack.py
```

Expected output:
```
✅ Slack service initialized successfully
Testing Slack Integration
============================================================

Slack Enabled: True

1. Testing refund notification...
   Result: ✅ Success

2. Testing high-value refund alert...
   Result: ✅ Success

3. Testing support ticket notification...
   Result: ✅ Success
```

## Notification Examples

### Refund Notification
```
💰 Refund Processed

Order ID: ORD0041
Amount: $69.00 USD
Customer: alice@example.com
Refund ID: re_xxxxx

✅ Automated refund processed by AI Agent
```

### High-Value Refund Alert
```
🚨 High-Value Refund Request

Order ID: ORD9999
Amount: $250.00 USD
Customer: vip@example.com
Ticket ID: TKT-123

⚠️ Action Required: This refund exceeds the automated limit and requires manual approval.

[Approve Refund] [Review Ticket]
```

### Support Ticket
```
🎫 New Support Ticket

Ticket ID: TKT-456
Priority: 🔴 HIGH
Customer: support@example.com
Order ID: ORD0042

Issue: Customer needs help with account
```

## Customization

### Change Default Channel
Update `.env`:
```bash
SLACK_CHANNEL=refunds  # Use channel name
# or
SLACK_CHANNEL=C1234567890  # Use channel ID
```

### Override Channel Per Notification
In code:
```python
from app.services.slack_service import slack_service

slack_service.send_refund_notification(
    order_id="ORD0041",
    customer_email="test@example.com",
    refund_amount=69.00,
    currency="USD",
    refund_id="re_test",
    channel="#custom-channel"  # Override default
)
```

## Troubleshooting

### Error: `channel_not_found`
**Solution:** Invite the bot to the channel:
```
/invite @YourBotName
```

### Error: `missing_scope`
**Solution:** Add required scopes in OAuth & Permissions, then reinstall the app

### Error: `not_authed` or `invalid_auth`
**Solution:** Verify your SLACK_TOKEN is correct and starts with `xoxb-`

### Slack service is disabled
**Solution:** Check that SLACK_TOKEN is set in `.env` file

## Channel IDs vs Names
- **Names:** Use `#channel-name` or `general` (easier)
- **IDs:** Use `C1234567890` (more reliable)

To get channel ID:
1. Right-click channel in Slack
2. Select "Copy link"
3. ID is the last part: `https://workspace.slack.com/archives/C1234567890`

## Disable Slack Notifications
Set empty token in `.env`:
```bash
SLACK_TOKEN=
```

All Slack calls will gracefully skip without errors.
