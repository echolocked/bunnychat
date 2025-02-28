"""
DeepSeek Chat Client implementation.
Provides a simple interface to interact with DeepSeek's API.
"""

import os
from typing import List, Dict, Optional, Union, Iterator
from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DeepSeekClient:
    """Client for interacting with DeepSeek's chat API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        """Initialize the DeepSeek client.
        
        Args:
            api_key: DeepSeek API key. If not provided, will look for DEEPSEEK_API_KEY in environment.
            model: Model to use for chat. Defaults to "deepseek-chat" (DeepSeek-V3).
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Please provide it or set DEEPSEEK_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
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
            temperature: Controls randomness in responses. Higher values (e.g., 0.8) make output more random, 
                        while lower values (e.g., 0.2) make it more focused and deterministic.
            max_tokens: Maximum number of tokens to generate.
            **kwargs: Additional parameters to pass to the API.
            
        Returns:
            If stream=False, returns the complete response as a string.
            If stream=True, returns an iterator of response chunks.
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
                
        except Exception as e:
            raise Exception(f"Error calling DeepSeek API: {str(e)}")
    
    def _handle_complete_response(self, response: ChatCompletion) -> str:
        """Handle a complete (non-streamed) response."""
        return response.choices[0].message.content
    
    def _handle_stream_response(self, response: Iterator[ChatCompletionChunk]) -> Iterator[str]:
        """Handle a streamed response."""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
