"""
DeepSeek Chat Client implementation.
Provides a simple interface to interact with DeepSeek's API.
"""

import os
import logging
from typing import List, Dict, Optional, Union, Iterator
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from dotenv import load_dotenv
import requests.exceptions

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class DeepSeekClient:
    """Client for interacting with DeepSeek's chat API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-reasoner"):
        """Initialize the DeepSeek client.
        
        Args:
            api_key: DeepSeek API key. If not provided, will look for DEEPSEEK_API_KEY in environment.
            model: Model to use for chat. Defaults to "deepseek-reasoner".
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Please provide it or set DEEPSEEK_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com",
            timeout=60.0  # Set a longer timeout
        )
        logger.debug(f"Initialized with model: {model}")
        
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Send a chat request to DeepSeek API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            stream: Whether to stream the response.
            temperature: Controls randomness in responses.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream=False, returns the complete response as a string.
            If stream=True, returns an iterator of response chunks.
            
        Raises:
            ConnectionError: If there are network connectivity issues
            TimeoutError: If the request times out
            Exception: For other API errors
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_complete_response(response)
                
        except requests.exceptions.ConnectionError as e:
            logger.error("Network connection error")
            raise ConnectionError("Failed to connect to the DeepSeek API. Please check your internet connection.")
        except requests.exceptions.Timeout as e:
            logger.error("Request timeout")
            raise TimeoutError("Request to DeepSeek API timed out. Please try again.")
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            raise Exception(f"Error calling DeepSeek API: {str(e)}")
    
    def chat_stream(
        self,
        message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """Send a chat request and stream the response.
        
        This is a convenience method that formats a single message and streams the response.
        
        Args:
            message: The message to send.
            temperature: Controls randomness in responses.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            An iterator of response chunks.
        """
        messages = [{"role": "user", "content": message}]
        return self.chat(
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    def _handle_complete_response(self, response: ChatCompletion) -> str:
        """Handle a complete (non-streamed) response."""
        return response.choices[0].message.content
    
    def _handle_stream_response(self, response: Iterator[ChatCompletionChunk]) -> Iterator[Dict[str, str]]:
        """Handle a streamed response.
        
        Returns:
            Iterator of dictionaries containing 'type' ('thinking' or 'response') and 'content'.
        """
        try:
            for chunk in response:
                delta = chunk.choices[0].delta
                
                # Check for reasoning content (thinking process)
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    yield {
                        'type': 'thinking',
                        'content': delta.reasoning_content
                    }
                
                # Check for regular content (actual response)
                if hasattr(delta, 'content') and delta.content:
                    yield {
                        'type': 'response',
                        'content': delta.content
                    }
                
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            raise
