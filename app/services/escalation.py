"""Human escalation system for handling complex queries."""

import uuid
from typing import Optional, Dict, List
from datetime import datetime

from app.services.database import get_db_connection
from app.services.email_service import email_service
from langchain.tools import tool


class EscalationManager:
    """Manages ticket creation and escalation logic."""
    
    @staticmethod
    def create_ticket(
        session_id: str,
        customer_id: Optional[str],
        issue_type: str,
        description: str,
        priority: str = "medium",
        confidence_score: Optional[float] = None
    ) -> str:
        """
        Create a support ticket for human escalation.
        
        Args:
            session_id: Conversation session ID
            customer_id: Customer ID if known
            issue_type: Type of issue (technical, refund, complex_query, etc.)
            description: Detailed description of the issue
            priority: low, medium, high, urgent
            confidence_score: Agent's confidence score (0-1)
            
        Returns:
            Ticket ID
        """
        ticket_id = f"TKT{uuid.uuid4().hex[:8].upper()}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO support_tickets 
            (ticket_id, session_id, customer_id, issue_type, description, priority, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticket_id, session_id, customer_id, issue_type, description, priority, confidence_score))
        
        conn.commit()
        conn.close()
        
        return ticket_id
    
    @staticmethod
    def should_escalate(
        query: str,
        tool_results: Optional[List[str]] = None,
        confidence_threshold: float = 0.3
    ) -> tuple[bool, str]:
        """
        Determine if a query should be escalated to human agent.
        
        Args:
            query: User's query
            tool_results: Results from tool executions
            confidence_threshold: Minimum confidence to continue (default 0.3)
            
        Returns:
            Tuple of (should_escalate: bool, reason: str)
        """
        # Escalation triggers
        escalation_keywords = [
            "speak to human", "talk to person", "real person", "human agent",
            "not satisfied", "complaint", "legal", "lawsuit", "fraud",
            "emergency", "urgent", "critical", "manager", "supervisor"
        ]
        
        query_lower = query.lower()
        
        # Check for explicit human request
        for keyword in escalation_keywords:
            if keyword in query_lower:
                return True, f"Customer explicitly requested: {keyword}"
        
        # Check if tools failed
        if tool_results:
            error_count = sum(1 for result in tool_results if "error" in result.lower() or "❌" in result)
            if error_count >= 2:
                return True, "Multiple tool failures detected"
        
        # Check for complex legal/financial queries
        complex_keywords = ["legal", "lawsuit", "attorney", "contract", "terms violation"]
        if any(keyword in query_lower for keyword in complex_keywords):
            return True, "Complex legal/contractual query detected"
        
        return False, ""
    
    @staticmethod
    def get_ticket(ticket_id: str) -> Optional[Dict]:
        """Get ticket details by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM support_tickets
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        conn.close()
        
        if ticket:
            return dict(ticket)
        return None
    
    @staticmethod
    def get_open_tickets() -> List[Dict]:
        """Get all open tickets."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM support_tickets
            WHERE status = 'open'
            ORDER BY priority DESC, created_at DESC
        """)
        
        tickets = cursor.fetchall()
        conn.close()
        
        return [dict(ticket) for ticket in tickets]
    
    @staticmethod
    def resolve_ticket(ticket_id: str, resolution_notes: Optional[str] = None) -> bool:
        """Mark ticket as resolved."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE support_tickets
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success


@tool
def create_support_ticket(issue_description: str, order_id: str = "", customer_email: str = "", priority: str = "medium") -> str:
    """
    Create a support ticket for complex issues that need human attention.
    
    Use this when:
    - Customer explicitly asks for human agent
    - Issue is too complex to handle automatically
    - Legal or sensitive matters are involved
    - Refund amount exceeds automated limit
    - Customer declines to proceed with refund
    
    Args:
        issue_description: Detailed description of the issue
        order_id: Related order ID (if applicable)
        customer_email: Customer's email for ticket notification
        priority: Ticket priority (low, medium, high, urgent)
        
    Returns:
        Ticket ID and confirmation message
    """
    try:
        # Generate a session ID (in real system, would come from context)
        session_id = f"SESSION_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        ticket_id = EscalationManager.create_ticket(
            session_id=session_id,
            customer_id=None,
            issue_type="complex_query",
            description=issue_description,
            priority=priority
        )
        
        # Send email notification if email provided
        email_confirmation = ""
        if customer_email:
            email_sent = email_service.send_ticket_created_notification(
                to_email=customer_email,
                ticket_id=ticket_id,
                order_id=order_id if order_id else "N/A",
                customer_name="Customer"
            )
            if email_sent:
                email_confirmation = f"\n\n📧 A confirmation email has been sent to {customer_email} with your ticket details."
        
        return f"""
✅ **Support Ticket Created**

**Ticket ID:** {ticket_id}
**Priority:** {priority}
**Status:** Open

A human support representative will review your case and contact you shortly. You can reference this ticket ID for any follow-ups.

**Expected Response Time:**
- Urgent: Within 1 hour
- High: Within 4 hours
- Medium: Within 24 hours
- Low: Within 48 hours{email_confirmation}

Is there anything else I can help you with in the meantime?
"""
    
    except Exception as e:
        return f"❌ Error creating support ticket: {str(e)}"


@tool
def check_ticket_status(ticket_id: str) -> str:
    """
    Check the status of a support ticket.
    
    Args:
        ticket_id: The ticket ID to check
        
    Returns:
        Ticket status and details
    """
    try:
        ticket = EscalationManager.get_ticket(ticket_id)
        
        if not ticket:
            return f"❌ Ticket {ticket_id} not found in the system."
        
        result = f"""
🎫 **Ticket Status for {ticket_id}**

**Status:** {ticket['status']}
**Priority:** {ticket['priority']}
**Issue Type:** {ticket['issue_type']}
**Created:** {ticket['created_at']}
"""
        
        if ticket['assigned_to']:
            result += f"**Assigned To:** {ticket['assigned_to']}\n"
        
        if ticket['resolved_at']:
            result += f"**Resolved:** {ticket['resolved_at']}\n"
        
        if ticket['status'] == 'open':
            result += "\n⏳ Your ticket is being processed. A support agent will contact you soon."
        else:
            result += "\n✅ This ticket has been resolved."
        
        return result
    
    except Exception as e:
        return f"❌ Error checking ticket status: {str(e)}"


# Export tools
escalation_tools = [create_support_ticket, check_ticket_status]
