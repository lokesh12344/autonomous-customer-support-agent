"""ReAct Agent for autonomous customer support."""

import re
import json
import time
from typing import List, Any, Optional, Dict

from app.services.llm_engine import get_llm
from app.tools.db_tools import db_tools
from app.tools.rag_tools import rag_tools
from app.tools.stripe_tools import stripe_tools
from app.tools.order_management_tools import order_management_tools
from app.tools.refund_workflow_tools import refund_workflow_tools
from app.services.escalation import escalation_tools, EscalationManager
from app.services.memory import ConversationMemory
from app.utils.logging_config import logger, log_tool_execution, log_agent_request, log_escalation


# Agent system prompt
AGENT_SYSTEM_PROMPT = """You are a professional customer support agent working for a company. Your goal is to help customers with genuine care and attention.

**YOUR PERSONALITY:**
- Professional but friendly - like talking to a helpful store employee
- Empathetic and patient - understand customer frustrations
- Guide customers step-by-step through processes
- Explain what you're doing and why it helps them
- Use natural transitions: "Let me look into that for you", "Give me just a moment", "I can definitely help with that"
- NEVER mention internal systems, tools, databases, or technical processes

{conversation_context}

**CONVERSATION STYLE:**
1. **Acknowledge & Empathize** - Show you understand their concern
2. **Explain Your Actions** - "Let me check on that order for you", "I'll look into your refund options"
3. **Present Information Naturally** - Share findings conversationally, not as a data dump
4. **Offer Next Steps** - Guide them on what happens next
5. **Check Understanding** - "Does this help?" "Is there anything else?"

**CRITICAL RULES:**
1. **NEVER reveal tools** - Don't mention "semantic search", "database", "fetch_order", or show JSON
2. **BE CONVERSATIONAL** - Talk like a human support agent, not a robot
3. **MINIMIZE QUESTIONS** - Only ask for what you absolutely need
4. **USE TOOL RESULTS NATURALLY** - Weave data into conversation, don't list it
5. **NO PLACEHOLDERS** - Never say "[insert status here]" - always use real data

{tool_descriptions}

**WHEN TO USE TOOLS (Silently - customer never sees this):**
Reply with ONLY JSON when you need data:
{{"action": "fetch_order", "action_input": "ORD0001"}}
{{"action": "initiate_refund", "action_input": "pi_xxxxx"}}

**RESPONSE EXAMPLES:**

❌ **BAD (Too Robotic)**:
"I've processed your refund of $45.00. Refund ID: re_yyy. You'll see it in 5-7 business days."

✅ **GOOD (Natural & Caring)**:
"I completely understand you'd like a refund. Let me take care of that for you right away.

I've processed the refund for your order. The amount of $45.00 will be credited back to your original payment method. You should see it reflected in your account within 5-7 business days, though it can sometimes appear sooner depending on your bank.

Is there anything else I can help you with today?"

**RESPONSE STRATEGY:**

For "Where is my order?":
1. Acknowledge: "Let me check on that for you"
2. Call fetch_order silently
3. Natural response: "I can see your order for [product] is currently [status]. It was placed on [date] and should arrive by [estimated date]."

For "I want a refund":
1. Empathize: "I understand, I'm happy to help with that"
2. Ask for order ID: "Could you provide your order number?"
3. Call process_refund_for_order silently
4. Explain with care: "I've processed that refund for you. The [amount] will be returned to your original payment method within 5-7 business days..."

NEVER ask for payment ID or bank details - system handles this!

**AFTER TOOL RESULTS - Start with "FINAL ANSWER:"**
Present information naturally in flowing conversation:

✅ GOOD: "I can see your order for the Premium Subscription is currently being shipped. It left our facility on November 15th and should arrive at your address by November 20th. You'll receive a tracking number via email shortly."

❌ BAD: "Order ORD0001 - Status: shipped - Date: 2024-11-15"

**ESCALATION:**
High-value refunds >₹10k/$120: "This refund requires manager approval. I've created a ticket, and our finance team will review it within 4 hours..."

Remember: Be HUMAN, CARING, and CONVERSATIONAL - like a real customer service rep!"""


class CustomerSupportAgent:
    """
    Simple autonomous customer support agent.
    
    This agent uses LangChain tools to reason about customer queries
    and take actions using available tools (database, RAG, Stripe, etc.)
    
    Note: This is a simplified implementation. For full ReAct agent,
    install compatible langchain versions or use initialize_agent.
    """
    
    def __init__(self, model_name: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize the customer support agent.
        
        Args:
            model_name: Optional LLM model name override
            session_id: Optional session ID for conversation memory
        """
        self.llm = get_llm(model_name=model_name)
        self.tools = self._register_tools()
        self.session_id = session_id or f"session_{int(time.time())}"
        self.memory = ConversationMemory(self.session_id)
        self.tool_results = []  # Track tool results for escalation detection
        
        # Create a simple tool mapper
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        logger.info(f"Agent initialized for session {self.session_id}")
    
    def _register_tools(self) -> List:
        """
        Register all available tools for the agent.
        
        Includes:
        - Database operations (fetch_customer, fetch_order, search_orders)
        - Order management (cancel_order, modify_address, track_shipment)
        - RAG/semantic search (FAQ search, documentation)
        - Stripe operations (refunds with limits, payment status)
        - Escalation tools (create_ticket, check_ticket_status)
        
        Returns:
            List: All registered tools
        """
        # Combine all tool lists
        all_tools = []
        
        # Add database tools
        all_tools.extend(db_tools)
        
        # Add order management tools
        all_tools.extend(order_management_tools)
        
        # Add RAG tools
        all_tools.extend(rag_tools)
        
        # Add Stripe tools (legacy - for checking payment status)
        all_tools.extend(stripe_tools)
        
        # Add refund workflow tools (complete refund handling)
        all_tools.extend(refund_workflow_tools)
        
        # Add escalation tools
        all_tools.extend(escalation_tools)
        
        logger.info(f"Registered {len(all_tools)} tools for the agent")
        print(f"🛠️  Registered {len(all_tools)} tools for the agent")
        return all_tools
    
    def _parse_action(self, text: str) -> Optional[Dict[str, str]]:
        """Parse action JSON from LLM response."""
        try:
            # Try to find JSON object in the text
            json_match = re.search(r'\{[^}]*"action"[^}]*\}', text)
            if json_match:
                action_dict = json.loads(json_match.group())
                return action_dict
            return None
        except Exception:
            return None
    
    def _clean_response(self, response: str) -> str:
        """
        Clean technical jargon from LLM response to make it human-like.
        Remove any mentions of tools, actions, or internal processes.
        """
        # Remove technical phrases
        technical_phrases = [
            r"I'll use the \w+ tool",
            r"using the \w+ tool",
            r"I will use the \w+ tool",
            r"Let me use the \w+ tool",
            r"I'll search the \w+ database",
            r"I'll query the \w+",
            r"Here's my next step:",
            r"Here's my request:",
            r"Here is my action:",
            r"Here's the JSON object:",
            r"\{\"action\":[^}]+\}",
            r"semantic_search_faq",
            r"fetch_order",
            r"fetch_customer",
            r"tool to retrieve",
            r"database operations",
            r"Please let me know if this is acceptable",
            r"if you'd like me to proceed",
        ]
        
        cleaned = response
        for phrase in technical_phrases:
            cleaned = re.sub(phrase, "", cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and newlines
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        # If response is too short or empty after cleaning, return original
        if len(cleaned) < 20:
            return response
        
        return cleaned
    
    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool and return the result with logging."""
        start_time = time.time()
        try:
            if tool_name not in self.tool_map:
                error_msg = f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(self.tool_map.keys())}"
                logger.error(f"Tool not found: {tool_name}")
                return error_msg
            
            tool = self.tool_map[tool_name]
            print(f"🔧 Executing tool: {tool_name} with input: {tool_input}")
            logger.info(f"Executing tool: {tool_name}", extra={"tool_name": tool_name, "session_id": self.session_id})
            
            # Call the tool function directly
            result = tool.func(tool_input)
            result_str = str(result)
            
            # Track tool results for escalation detection
            self.tool_results.append(result_str)
            
            # Log execution
            execution_time = time.time() - start_time
            log_tool_execution(tool_name, tool_input, result_str, execution_time, self.session_id)
            
            return result_str
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            logger.error(error_msg, extra={"tool_name": tool_name, "session_id": self.session_id, "execution_time": execution_time})
            self.tool_results.append(error_msg)
            return error_msg
    
    def run(self, user_input: str, max_iterations: int = 5) -> str:
        """
        Run the agent with ReAct-style reasoning and tool calling.
        
        The agent will:
        1. Check conversation history for context
        2. Check if query should be escalated to human
        3. Perform initial FAQ/documentation search
        4. Decide which tools to call based on query
        5. Execute tools and gather results
        6. Combine tool results with LLM knowledge
        7. Provide comprehensive final answer or escalate
        
        Args:
            user_input: The customer's question or request
            max_iterations: Maximum number of reasoning iterations
            
        Returns:
            str: The agent's response
        """
        start_time = time.time()
        self.tool_results = []  # Reset for this request
        
        try:
            # Save user message to memory
            self.memory.add_message("user", user_input)
            logger.info(f"User query: {user_input}", extra={"session_id": self.session_id, "user_input": user_input})
            
            # Check if query should be escalated immediately
            should_escalate, escalation_reason = EscalationManager.should_escalate(user_input)
            if should_escalate:
                ticket_id = EscalationManager.create_ticket(
                    session_id=self.session_id,
                    customer_id=None,
                    issue_type="explicit_request",
                    description=f"User query: {user_input}\nReason: {escalation_reason}",
                    priority="high"
                )
                log_escalation(ticket_id, self.session_id, escalation_reason)
                
                escalation_message = f"""
I understand you'd like to speak with a human agent. I've created a support ticket for you.

**Ticket ID:** {ticket_id}
**Priority:** High
**Status:** Open

A human support agent will contact you shortly. Expected response time: Within 1 hour.

Is there anything I can help you with in the meantime?
"""
                self.memory.add_message("assistant", escalation_message)
                log_agent_request(self.session_id, user_input, escalation_message, time.time() - start_time)
                return escalation_message
            
            # Build tool descriptions
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tools
            ])
            
            # Get conversation context
            conversation_context = self.memory.get_context_string(limit=3)
            
            # Start with system prompt
            system_prompt = AGENT_SYSTEM_PROMPT.format(
                tool_descriptions=tool_descriptions,
                conversation_context=f"\n{conversation_context}\n" if conversation_context != "No previous conversation." else ""
            )
            
            conversation_history = []
            
            # Detect query type and call appropriate tools immediately
            query_lower = user_input.lower()
            
            # Check for order-related queries
            if any(keyword in query_lower for keyword in ["order", "ord", "where is my", "track"]):
                # Extract order ID if present
                import re
                order_match = re.search(r'ord\d{4}', user_input, re.IGNORECASE)
                if order_match:
                    order_id = order_match.group().upper()
                    print(f"🔍 Detected order query, fetching order {order_id}")
                    order_result = self._execute_tool("fetch_order", order_id)
                    conversation_history.append(f"Order Data:\n{order_result}\n")
            
            # Check for refund queries
            if any(keyword in query_lower for keyword in ["refund", "return", "money back"]):
                print(f"🔍 Detected refund query, searching FAQ")
                faq_result = self._execute_tool("semantic_search_faq", "refund policy")
                conversation_history.append(f"Refund Policy:\n{faq_result}\n")
            
            # For general queries, do FAQ search
            if not conversation_history:
                print(f"🔍 Performing FAQ search for: {user_input}")
                try:
                    faq_result = self._execute_tool("semantic_search_faq", user_input)
                    conversation_history.append(f"FAQ Search Result:\n{faq_result}\n")
                except Exception as e:
                    print(f"⚠️  FAQ search failed: {e}")
            
            # Add user query
            conversation_history.append(f"Customer Question: {user_input}\n")
            
            # Reasoning loop
            for iteration in range(max_iterations):
                print(f"🤔 Reasoning iteration {iteration + 1}/{max_iterations}")
                
                # Build prompt with history
                full_prompt = f"""{system_prompt}

{' '.join(conversation_history)}

**Instructions:**
- If you have tool results above, you MUST use the actual data in your response
- If you need more data, call a tool with JSON: {{"action": "tool_name", "action_input": "value"}}
- If you have enough data, respond with "FINAL ANSWER:" followed by your complete response using the ACTUAL data from tool results
- NEVER use placeholders like "[insert X here]" or generic responses - always use the specific data provided"""
                
                # Get LLM response
                response = self.llm.invoke(full_prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                print(f"💭 LLM Response: {response_text[:200]}...")
                
                # Check if this is a final answer
                if "FINAL ANSWER:" in response_text.upper():
                    # Extract final answer
                    final_answer = response_text.split("FINAL ANSWER:")[-1].strip()
                    if not final_answer or final_answer.startswith("{"):
                        # LLM didn't provide answer after "FINAL ANSWER:", continue
                        continue
                    
                    # Clean technical jargon from response
                    final_answer = self._clean_response(final_answer)
                    
                    print(f"✅ Final answer generated")
                    
                    # Save to memory
                    self.memory.add_message("assistant", final_answer)
                    
                    # Log the request
                    processing_time = time.time() - start_time
                    log_agent_request(self.session_id, user_input, final_answer, processing_time)
                    
                    return final_answer
                
                # Try to parse action
                action = self._parse_action(response_text)
                
                if action and "action" in action:
                    tool_name = action["action"]
                    tool_input = action.get("action_input", "")
                    
                    # Execute tool
                    tool_result = self._execute_tool(tool_name, tool_input)
                    
                    # Add to conversation history
                    conversation_history.append(f"Tool Used: {tool_name}\nTool Input: {tool_input}\nTool Result: {tool_result}\n")
                else:
                    # No action found, treat as final answer
                    print(f"✅ No more actions needed, using response as final answer")
                    
                    # Clean technical jargon from response
                    cleaned_response = self._clean_response(response_text)
                    
                    # Save to memory
                    self.memory.add_message("assistant", cleaned_response)
                    
                    # Log the request
                    processing_time = time.time() - start_time
                    log_agent_request(self.session_id, user_input, cleaned_response, processing_time)
                    
                    return cleaned_response
            
            # If we exhausted iterations, check if we should escalate
            should_escalate_after, escalation_reason = EscalationManager.should_escalate(
                user_input, 
                tool_results=self.tool_results
            )
            
            if should_escalate_after:
                ticket_id = EscalationManager.create_ticket(
                    session_id=self.session_id,
                    customer_id=None,
                    issue_type="complex_query",
                    description=f"User query: {user_input}\nReason: {escalation_reason}\nTool results: {self.tool_results[:3]}",
                    priority="medium",
                    confidence_score=0.2
                )
                log_escalation(ticket_id, self.session_id, f"Max iterations reached - {escalation_reason}")
                
                escalation_message = f"""
I apologize, but I'm having difficulty resolving your issue automatically. I've created a support ticket for human assistance.

**Ticket ID:** {ticket_id}
**Status:** Open

A support agent will review your case and contact you within 24 hours.
"""
                self.memory.add_message("assistant", escalation_message)
                log_agent_request(self.session_id, user_input, escalation_message, time.time() - start_time)
                return escalation_message
            
            # If we exhausted iterations, ask LLM for final answer
            print("⚠️  Max iterations reached, generating final answer")
            final_prompt = f"""{system_prompt}

{' '.join(conversation_history)}

Based on all the information above, provide your FINAL ANSWER to the customer's question in a natural, human-like way: {user_input}
Remember: Be warm, friendly, and never mention technical processes."""
            
            final_response = self.llm.invoke(final_prompt)
            final_text = final_response.content if hasattr(final_response, 'content') else str(final_response)
            
            # Clean the response
            final_text = self._clean_response(final_text)
            
            # Save to memory
            self.memory.add_message("assistant", final_text)
            
            # Log the request
            processing_time = time.time() - start_time
            log_agent_request(self.session_id, user_input, final_text, processing_time)
            
            return final_text
        
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error while processing your request. Please try again or rephrase your question."
            logger.error(f"Agent error: {e}", extra={"session_id": self.session_id}, exc_info=True)
            print(f"❌ Agent error: {e}")
            import traceback
            traceback.print_exc()
            
            # Save error to memory
            self.memory.add_message("assistant", error_msg)
            
            return error_msg


# Global agent instance
_agent = None


def get_agent(model_name: Optional[str] = None) -> CustomerSupportAgent:
    """
    Get or create the global customer support agent instance.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        CustomerSupportAgent: The agent instance
    """
    global _agent
    if _agent is None:
        _agent = CustomerSupportAgent(model_name=model_name)
    return _agent


if __name__ == "__main__":
    # Test the agent initialization
    print("🤖 Testing Customer Support Agent...")
    agent = get_agent()
    print(f"✅ Agent initialized with {len(agent.tools)} tools")
