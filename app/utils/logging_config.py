"""Structured logging configuration for the application."""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path

from app.utils.config import settings


# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'tool_name'):
            log_data['tool_name'] = record.tool_name
        if hasattr(record, 'execution_time'):
            log_data['execution_time'] = record.execution_time
        if hasattr(record, 'user_input'):
            log_data['user_input'] = record.user_input[:100]  # Truncate for safety
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("customer_support_agent")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with pretty formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(
        LOGS_DIR / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(
        LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    logger.addHandler(error_handler)
    
    return logger


# Global logger instance
logger = setup_logging(log_level=settings.log_level if hasattr(settings, 'log_level') else "INFO")


def log_tool_execution(tool_name: str, input_data: str, result: str, execution_time: float, session_id: Optional[str] = None):
    """
    Log tool execution with structured data.
    
    Args:
        tool_name: Name of the tool executed
        input_data: Input provided to the tool
        result: Tool execution result
        execution_time: Time taken in seconds
        session_id: Optional session identifier
    """
    logger.info(
        f"Tool executed: {tool_name}",
        extra={
            "tool_name": tool_name,
            "execution_time": execution_time,
            "session_id": session_id,
            "input_length": len(input_data),
            "result_length": len(result)
        }
    )


def log_agent_request(session_id: str, user_input: str, response: str, processing_time: float):
    """
    Log agent request and response.
    
    Args:
        session_id: Session identifier
        user_input: User's question
        response: Agent's response
        processing_time: Total processing time in seconds
    """
    logger.info(
        f"Agent request processed",
        extra={
            "session_id": session_id,
            "user_input": user_input,
            "processing_time": processing_time,
            "response_length": len(response)
        }
    )


def log_escalation(ticket_id: str, session_id: str, reason: str, confidence_score: Optional[float] = None):
    """
    Log human escalation event.
    
    Args:
        ticket_id: Generated ticket ID
        session_id: Session identifier
        reason: Reason for escalation
        confidence_score: Optional confidence score
    """
    logger.warning(
        f"Escalated to human: {reason}",
        extra={
            "ticket_id": ticket_id,
            "session_id": session_id,
            "confidence_score": confidence_score
        }
    )


def log_error(error_type: str, error_message: str, session_id: Optional[str] = None, **kwargs):
    """
    Log error with context.
    
    Args:
        error_type: Type/category of error
        error_message: Error message
        session_id: Optional session identifier
        **kwargs: Additional context
    """
    extra = {"error_type": error_type, "session_id": session_id}
    extra.update(kwargs)
    
    logger.error(error_message, extra=extra)
