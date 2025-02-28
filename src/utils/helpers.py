"""
Utility functions for the chatbot.
"""

from typing import List, Dict, Optional
import json

def format_message(role: str, content: str) -> Dict[str, str]:
    """Format a message for the chat API.
    
    Args:
        role: The role of the message sender ('system', 'user', or 'assistant')
        content: The message content
        
    Returns:
        A dictionary with 'role' and 'content' keys
    """
    return {"role": role, "content": content}

def create_chat_messages(
    user_message: str,
    system_message: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """Create a list of messages for the chat API.
    
    Args:
        user_message: The user's message
        system_message: Optional system message to set context
        chat_history: Optional list of previous messages
        
    Returns:
        List of message dictionaries
    """
    messages = []
    
    if system_message:
        messages.append(format_message("system", system_message))
        
    if chat_history:
        messages.extend(chat_history)
        
    messages.append(format_message("user", user_message))
    return messages

def is_json_response(text: str) -> bool:
    """Check if a string is valid JSON.
    
    Args:
        text: String to check
        
    Returns:
        True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(text)
        return True
    except ValueError:
        return False
