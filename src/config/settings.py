"""
Configuration settings for the chatbot.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ChatSettings:
    """Settings for chat functionality."""
    model: str = "deepseek-reasoner"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = True
    system_message: str = "You are a helpful AI assistant with reasoning capabilities. When appropriate, you can search the internet to provide up-to-date information."

@dataclass
class APISettings:
    """API-related settings."""
    api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com"
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError("DeepSeek API key not found. Please set DEEPSEEK_API_KEY environment variable.")

@dataclass
class SearchSettings:
    """Settings for web search functionality."""
    max_results: int = 3
    max_concurrent: int = 3
    search_timeout: int = 10

@dataclass
class WebSettings:
    """Web server settings."""
    port: int = 5000
    debug: bool = False
    host: str = "localhost"

# Default settings instances
chat_settings = ChatSettings()
api_settings = APISettings()
search_settings = SearchSettings()
web_settings = WebSettings()
