"""
Command-line interface for the DeepSeek chatbot.
"""

import os
import json
import sys
import logging
from typing import List, Dict
import readline  # For better input handling (command history)

from src.config.settings import chat_settings, api_settings
from src.utils.helpers import create_chat_messages
from src.utils.search import search_and_scrape
from src.chat.client import DeepSeekClient

# Set up logging
logger = logging.getLogger(__name__)

class ChatCLI:
    def __init__(self, history_file: str = "chat_history.json"):
        """Initialize the chat CLI.
        
        Args:
            history_file: Path to file for storing chat history
        """
        self.history_file = history_file
        self.chat_history: List[Dict[str, str]] = self.load_history()
        self.client = DeepSeekClient(
            api_key=api_settings.api_key,
            model=chat_settings.model
        )
        
    def load_history(self) -> List[Dict[str, str]]:
        """Load chat history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load chat history: {e}")
                return []
        return []
    
    def save_history(self):
        """Save chat history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
    
    def print_streaming_response(self, response_iterator):
        """Print streaming response with proper formatting."""
        print("\nAssistant: ", end='', flush=True)
        response_text = ""
        for text_chunk in response_iterator:
            print(text_chunk, end='', flush=True)
            response_text += text_chunk
        print("\n")
        return response_text
    
    def handle_search(self, query: str) -> str:
        """Handle search command and return results."""
        try:
            results = search_and_scrape(query)
            if not results:
                return "No search results found."
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(f"URL: {result['url']}")
                formatted_results.append(f"Title: {result['title']}")
                formatted_results.append(f"Content: {result['content'][:200]}...")
                formatted_results.append("")
            
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Error performing search: {str(e)}"
    
    def run(self):
        """Run the chat CLI."""
        print("Welcome to DeepSeek Chat! Type '/help' for commands, '/quit' to exit.")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Handle commands
                if user_input.lower() in ['/quit', '/exit']:
                    print("Goodbye!")
                    break
                elif user_input.lower() == '/help':
                    print("\nCommands:")
                    print("  /help  - Show this help message")
                    print("  /clear - Clear chat history")
                    print("  /quit  - Exit the chat")
                    print("  /search <query> - Search the web")
                    continue
                elif user_input.lower() == '/clear':
                    self.chat_history = []
                    self.save_history()
                    print("Chat history cleared.")
                    continue
                elif user_input.lower().startswith('/search '):
                    query = user_input[8:].strip()
                    if query:
                        print("\nSearching...")
                        results = self.handle_search(query)
                        print(results)
                    continue
                elif not user_input:
                    continue
                
                # Create messages with history and system message
                messages = create_chat_messages(
                    user_message=user_input,
                    system_message=chat_settings.system_message,
                    chat_history=self.chat_history
                )
                
                # Get streaming response
                response_text = self.print_streaming_response(
                    self.client.chat(messages=messages, stream=True)
                )
                
                # Update history
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": response_text})
                self.save_history()
                
            except KeyboardInterrupt:
                print("\nInterrupted. Type '/quit' or '/exit' to end the chat.")
            except Exception as e:
                logger.error(f"Chat error: {e}")
                print("\nAn error occurred. Please try again.")

def main():
    """Main entry point for the CLI."""
    cli = ChatCLI()
    cli.run()

if __name__ == "__main__":
    main() 