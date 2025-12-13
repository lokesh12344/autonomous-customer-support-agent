"""Email notification service for customer communications."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Optional
from ..utils.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending email notifications to customers."""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.sender_email = settings.sender_email
        self.enabled = settings.email_enabled
        
    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email to the specified recipient.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service is disabled. Skipping email send.")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Attach plain text
            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            
            # Attach HTML if provided
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_refund_notification(
        self, 
        to_email: str, 
        order_id: str, 
        refund_amount: float,
        currency: str = "USD",
        customer_name: str = "Customer"
    ) -> bool:
        """
        Send refund processing notification email.
        
        Args:
            to_email: Customer email address
            order_id: Order ID being refunded
            refund_amount: Amount being refunded
            currency: Currency code (USD, INR, etc.)
            customer_name: Customer's name
            
        Returns:
            bool: True if email sent successfully
        """
        subject = f"Refund Processing for Order {order_id}"
        
        # Plain text body
        body = f"""Dear {customer_name},

We are processing your refund request for order {order_id}.

Refund Details:
- Order ID: {order_id}
- Refund Amount: {currency} {refund_amount:.2f}
- Processing Date: {datetime.now().strftime('%B %d, %Y')}

The refund has been initiated and will be credited to your original payment method within 5-7 business days, though it may appear sooner depending on your bank's processing time.

If you have any questions or concerns, please don't hesitate to reach out to our support team.

Thank you for your patience and understanding.

Best regards,
Customer Support Team
Autonomous Customer Support Agent
"""
        
        # HTML body
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
              .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
              .details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50; }}
              .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>Refund Processing Confirmation</h2>
              </div>
              <div class="content">
                <p>Dear {customer_name},</p>
                <p>We are processing your refund request for order <strong>{order_id}</strong>.</p>
                
                <div class="details">
                  <h3>Refund Details:</h3>
                  <ul>
                    <li><strong>Order ID:</strong> {order_id}</li>
                    <li><strong>Refund Amount:</strong> {currency} {refund_amount:.2f}</li>
                    <li><strong>Processing Date:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                  </ul>
                </div>
                
                <p>The refund has been initiated and will be credited to your original payment method within <strong>5-7 business days</strong>, though it may appear sooner depending on your bank's processing time.</p>
                
                <p>If you have any questions or concerns, please don't hesitate to reach out to our support team.</p>
                
                <p>Thank you for your patience and understanding.</p>
                
                <p>Best regards,<br>
                <strong>Customer Support Team</strong><br>
                Autonomous Customer Support Agent</p>
              </div>
              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_ticket_created_notification(
        self,
        to_email: str,
        ticket_id: str,
        order_id: str,
        customer_name: str = "Customer"
    ) -> bool:
        """
        Send notification when support ticket is created.
        
        Args:
            to_email: Customer email address
            ticket_id: Support ticket ID
            order_id: Related order ID
            customer_name: Customer's name
            
        Returns:
            bool: True if email sent successfully
        """
        subject = f"Support Ticket Created - {ticket_id}"
        
        body = f"""Dear {customer_name},

Your support request has been received and a ticket has been created.

Ticket Details:
- Ticket ID: {ticket_id}
- Order ID: {order_id}
- Created: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

A human support representative will review your request and contact you within 4 hours.

You can reference ticket ID {ticket_id} for any follow-up inquiries.

Thank you for your patience.

Best regards,
Customer Support Team
"""
        
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
              .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
              .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
              .ticket-box {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #2196F3; }}
              .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h2>Support Ticket Created</h2>
              </div>
              <div class="content">
                <p>Dear {customer_name},</p>
                <p>Your support request has been received and a ticket has been created.</p>
                
                <div class="ticket-box">
                  <h3>Ticket Details:</h3>
                  <ul>
                    <li><strong>Ticket ID:</strong> {ticket_id}</li>
                    <li><strong>Order ID:</strong> {order_id}</li>
                    <li><strong>Created:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</li>
                  </ul>
                </div>
                
                <p>A human support representative will review your request and contact you within <strong>4 hours</strong>.</p>
                
                <p>You can reference ticket ID <strong>{ticket_id}</strong> for any follow-up inquiries.</p>
                
                <p>Thank you for your patience.</p>
                
                <p>Best regards,<br>
                <strong>Customer Support Team</strong></p>
              </div>
              <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)

# Global email service instance
email_service = EmailService()
