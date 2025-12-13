# Email Notification Setup Guide

This guide explains how to configure email notifications for refund processing and support ticket creation.

## Features

The email notification system provides:

1. **Refund Processing Notifications** - Sent when a refund is successfully processed
2. **Support Ticket Confirmations** - Sent when a support ticket is created

## Configuration

### 1. Gmail Setup (Recommended)

If you're using Gmail, you need to create an **App Password** (not your regular Gmail password):

1. Go to your [Google Account Settings](https://myaccount.google.com/)
2. Select **Security** from the left menu
3. Enable **2-Step Verification** if not already enabled
4. Under "2-Step Verification", scroll to **App passwords**
5. Click **App passwords** and sign in again
6. Select **Mail** for the app and **Other** for the device
7. Name it "Customer Support Agent" and click **Generate**
8. Copy the 16-character password (shown in yellow box)

### 2. Environment Variables

Add these variables to your `.env` file:

```bash
# Email Configuration (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here  # 16-character app password from step 1
SENDER_EMAIL=your_email@gmail.com
EMAIL_ENABLED=true  # Set to true to enable email notifications
```

**Note:** For security, never commit your `.env` file to version control!

### 3. Other Email Providers

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_password
SENDER_EMAIL=your_email@outlook.com
```

#### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your_email@yahoo.com
SMTP_PASSWORD=your_app_password  # Requires app password
SENDER_EMAIL=your_email@yahoo.com
```

#### Custom SMTP Server
```bash
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USERNAME=support@yourdomain.com
SMTP_PASSWORD=your_password
SENDER_EMAIL=support@yourdomain.com
```

## Email Templates

### Refund Notification Email

Sent when a refund is processed successfully. Includes:
- Order ID and product name
- Refund amount and currency
- Refund ID from Stripe
- Timeline (5-7 business days)
- Formatted HTML email with company branding

### Support Ticket Email

Sent when a support ticket is created. Includes:
- Ticket ID for reference
- Related order ID (if applicable)
- Priority level
- Expected response time
- Human representative will contact within specified timeframe

## How the Email Flow Works

### Refund Process with Email

1. **Customer Request:** "I want a refund for order ORD0001"
2. **Agent Checks:** Verifies refund eligibility using `check_refund_eligibility`
3. **Agent Informs:** "Your refund amount is $45.00. Our automated limit is $120."
4. **Agent Asks:** "Would you like me to go ahead and process this refund?"
5. **Customer Confirms:** "Yes, please proceed"
6. **Agent Requests:** "Great! I'll need your email address to send you a confirmation."
7. **Customer Provides:** "john@example.com"
8. **Agent Processes:** Calls `process_refund_for_order(order_id, customer_email)`
9. **Email Sent:** Confirmation email delivered to john@example.com
10. **Agent Confirms:** "Perfect! I've processed the refund and sent a confirmation email."

### Ticket Creation with Email

1. **Customer Request:** "I want a refund but amount is over $120" OR "No, I don't want to proceed"
2. **Agent Creates Ticket:** Calls `create_support_ticket(description, order_id, customer_email)`
3. **Email Sent:** Ticket confirmation email delivered
4. **Agent Informs:** "I've created a support ticket. A human representative will be assigned within 4 hours."

## Testing Email Configuration

To test if your email configuration is working:

```python
from app.services.email_service import email_service

# Test refund notification
email_service.send_refund_notification(
    to_email="test@example.com",
    order_id="ORD0001",
    refund_amount=45.00,
    currency="USD",
    customer_name="John Doe"
)

# Test ticket notification
email_service.send_ticket_created_notification(
    to_email="test@example.com",
    ticket_id="TKT12345678",
    order_id="ORD0001",
    customer_name="John Doe"
)
```

## Troubleshooting

### Email Not Sending

1. **Check EMAIL_ENABLED**: Make sure it's set to `true` in `.env`
2. **Verify Credentials**: Test your SMTP username and password
3. **Check Logs**: Look in `logs/agent_*.log` for error messages
4. **Gmail Blocks**: If using Gmail, ensure you've created an App Password
5. **Firewall**: Ensure port 587 (or 465) is not blocked

### Common Errors

**"Authentication failed"**
- Wrong username/password
- Gmail: Need to use App Password, not regular password
- Yahoo: Need to enable "Less secure app access"

**"Connection timeout"**
- SMTP server or port incorrect
- Firewall blocking outbound SMTP connections
- Check if your ISP blocks port 25/587

**"Email not received"**
- Check spam/junk folder
- Verify sender email is correct
- Some email providers have rate limits

### Disabling Emails

If you want to disable email notifications temporarily:

```bash
EMAIL_ENABLED=false
```

Emails will be skipped but the agent will still function normally.

## Security Best Practices

1. **Never commit** your `.env` file to version control
2. **Use App Passwords** for Gmail (not your actual password)
3. **Rotate passwords** regularly
4. **Use environment variables** for sensitive data
5. **Enable 2FA** on your email account
6. **Monitor logs** for failed authentication attempts

## Production Considerations

For production deployment:

1. **Use a dedicated email service** like SendGrid, Mailgun, or AWS SES
2. **Set up SPF/DKIM** records for better deliverability
3. **Implement rate limiting** to prevent email abuse
4. **Add email queue** for handling failures and retries
5. **Monitor bounce rates** and email delivery metrics
6. **Use templates** stored in database for easy updates

## Next Steps

After configuring emails:

1. Restart your services: `./run_full_stack.sh`
2. Test the refund flow with a mock order
3. Verify emails are received
4. Check email formatting in different clients (Gmail, Outlook, etc.)
5. Configure email templates to match your brand

---

For issues or questions, check the logs in `logs/agent_*.log` or create a GitHub issue.
