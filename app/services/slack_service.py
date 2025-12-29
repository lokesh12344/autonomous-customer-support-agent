"""Slack notification service for customer support alerts."""

import os
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.utils.config import settings


class SlackService:
    """Service for sending notifications to Slack channels."""
    
    def __init__(self):
        """Initialize Slack client with bot token."""
        self.enabled = bool(settings.slack_token)
        self.client = None
        
        if self.enabled:
            try:
                self.client = WebClient(token=settings.slack_token)
                # Test the connection
                self.client.auth_test()
                print("✅ Slack service initialized successfully")
            except SlackApiError as e:
                print(f"⚠️  Slack initialization failed: {e.response['error']}")
                self.enabled = False
            except Exception as e:
                print(f"⚠️  Slack service disabled: {e}")
                self.enabled = False
        else:
            print("ℹ️  Slack service is disabled (no token provided)")
    
    def send_refund_notification(
        self,
        order_id: str,
        customer_email: str,
        refund_amount: float,
        currency: str,
        refund_id: str,
        channel: str = None
    ) -> bool:
        """
        Send refund notification to Slack channel.
        
        Args:
            order_id: The order ID
            customer_email: Customer's email address
            refund_amount: Amount refunded
            currency: Currency code (USD, INR, etc.)
            refund_id: Stripe refund ID
            channel: Slack channel to post to (default: #refunds)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("Slack service is disabled. Skipping notification.")
            return False
        
        # Use default channel if none provided
        if not channel:
            channel = settings.slack_channel
        
        try:
            symbol = "₹" if currency == "INR" else "$"
            
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "💰 Refund Processed",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Order ID:*\n{order_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Amount:*\n{symbol}{refund_amount:.2f} {currency}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Customer:*\n{customer_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Refund ID:*\n`{refund_id}`"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"✅ Automated refund processed by AI Agent"
                        }
                    ]
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=message_blocks,
                text=f"Refund processed: {order_id} - {symbol}{refund_amount:.2f} {currency}"
            )
            
            print(f"✅ Slack notification sent to {channel}")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Failed to send Slack notification: {str(e)}")
            return False
    
    def send_high_value_refund_alert(
        self,
        order_id: str,
        customer_email: str,
        refund_amount: float,
        currency: str,
        ticket_id: str,
        channel: str = None
    ) -> bool:
        """
        Send alert for high-value refunds that require manual approval.
        
        Args:
            order_id: The order ID
            customer_email: Customer's email address
            refund_amount: Amount to be refunded
            currency: Currency code
            ticket_id: Support ticket ID
            channel: Slack channel to post to
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("Slack service is disabled. Skipping alert.")
            return False
        
        # Use default channel if none provided
        if not channel:
            channel = settings.slack_channel
        
        try:
            symbol = "₹" if currency == "INR" else "$"
            
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 High-Value Refund Request",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Order ID:*\n{order_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Amount:*\n{symbol}{refund_amount:.2f} {currency}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Customer:*\n{customer_email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:*\n{ticket_id}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Action Required:* This refund exceeds the automated limit and requires manual approval.\n\n👉 Review ticket: `{ticket_id}`"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "⏰ Expected response time: Within 4 hours"
                        }
                    ]
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=message_blocks,
                text=f"High-value refund request: {order_id} - {symbol}{refund_amount:.2f} {currency}"
            )
            
            print(f"✅ High-value refund alert sent to {channel}")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {str(e)}")
            return False
    
    def send_support_ticket_notification(
        self,
        ticket_id: str,
        issue: str,
        customer_email: str,
        order_id: Optional[str] = None,
        priority: str = "medium",
        channel: str = None
    ) -> bool:
        """
        Send notification for new support tickets.
        
        Args:
            ticket_id: Support ticket ID
            issue: Issue description
            customer_email: Customer's email
            order_id: Associated order ID (if any)
            priority: Ticket priority (low, medium, high)
            channel: Slack channel to post to
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("Slack service is disabled. Skipping notification.")
            return False
        
        # Use default channel if none provided
        if not channel:
            channel = settings.slack_channel
        
        try:
            # Determine emoji and color based on priority
            priority_config = {
                "low": {"emoji": "🔵", "color": "#36a64f"},
                "medium": {"emoji": "🟡", "color": "#ff9900"},
                "high": {"emoji": "🔴", "color": "#ff0000"}
            }
            
            config = priority_config.get(priority.lower(), priority_config["medium"])
            
            fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Ticket ID:*\n{ticket_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Priority:*\n{config['emoji']} {priority.upper()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Customer:*\n{customer_email}"
                }
            ]
            
            if order_id:
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*Order ID:*\n{order_id}"
                })
            
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎫 New Support Ticket",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": fields
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Issue:*\n{issue[:500]}"  # Limit to 500 chars
                    }
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=message_blocks,
                text=f"New support ticket: {ticket_id} - {priority.upper()} priority"
            )
            
            print(f"✅ Support ticket notification sent to {channel}")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Failed to send Slack notification: {str(e)}")
            return False
    
    def send_replacement_request_notification(
        self,
        ticket_id: str,
        order_id: str,
        product_name: str,
        reason: str,
        customer_email: str,
        amount: float,
        channel: str = None
    ) -> bool:
        """
        Send notification for product replacement requests.
        
        Args:
            ticket_id: Support ticket ID
            order_id: The order ID
            product_name: Name of the product to be replaced
            reason: Reason for replacement
            customer_email: Customer's email
            amount: Order amount
            channel: Slack channel to post to
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("Slack service is disabled. Skipping notification.")
            return False
        
        # Use default channel if none provided
        if not channel:
            channel = settings.slack_channel
        
        try:
            message_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Product Replacement Request",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Ticket ID:*\n{ticket_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Order ID:*\n{order_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Product:*\n{product_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Amount:*\n${amount:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{reason}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Customer:*\n{customer_email}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "⚠️ *Action Required:* Please review and arrange replacement:\n• Verify defect/issue\n• Arrange pickup (if needed)\n• Ship replacement product\n• Update customer with tracking"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🚨 HIGH PRIORITY | ⏰ Response expected within 4 hours"
                        }
                    ]
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=message_blocks,
                text=f"Replacement request: {order_id} - {product_name} ({reason})"
            )
            
            print(f"✅ Replacement request notification sent to {channel}")
            return True
            
        except SlackApiError as e:
            print(f"❌ Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ Failed to send Slack notification: {str(e)}")
            return False


# Global Slack service instance
slack_service = SlackService()
