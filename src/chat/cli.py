"""
Command-line interface for the DeepSeek chatbot.
"""

import os
import json
import sys
from typing import List, Dict
import readline  # For better input handling (command history)

from src.config.settings import chat_settings, api_settings
from src.utils.helpers import create_chat_messages
from src.utils.search import search_and_scrape
from src.chat.client import DeepSeekClient

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
                print(f"Error loading chat history: {e}", file=sys.stderr)
                return []
        return []
    
    def save_history(self):
        """Save chat history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving chat history: {e}", file=sys.stderr)
    
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
        print("\nSearching the web...", flush=True)
        return search_and_scrape(query)
    
    def run(self):
        """Run the chat interface."""
        print(f"Welcome to DeepSeek Chat! Using model: {chat_settings.model}")
        print("Commands:")
        print("  /search <query> - Search the internet")
        print("  /clear - Clear chat history")
        print("  /quit or /exit - End chat")
        print("Streaming responses enabled - you'll see the response as it's generated.")
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Handle commands
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("Goodbye!")
                    self.save_history()
                    break
                elif user_input.lower() in ['/clear', 'clear']:
                    self.chat_history = []
                    self.save_history()
                    print("Chat history cleared.")
                    continue
                elif not user_input:
                    continue
                elif user_input.lower().startswith('/search '):
                    search_query = user_input[8:].strip()
                    if search_query:
                        search_results = self.handle_search(search_query)
                        print(search_results)
                        
                        # Add search results to chat history
                        self.chat_history.append({
                            "role": "user",
                            "content": f"Please search for information about: {search_query}"
                        })
                        self.chat_history.append({
                            "role": "assistant",
                            "content": f"Here are the search results:\n\n{search_results}"
                        })
                        self.save_history()
                    continue
                
                # Create messages with history
                messages = create_chat_messages(
                    user_message=user_input,
                    system_message=chat_settings.system_message,
                    chat_history=self.chat_history
                )
                
                # Get streaming response
                response_iterator = self.client.chat(
                    messages=messages,
                    stream=True,  # Always use streaming
                    temperature=chat_settings.temperature,
                    max_tokens=chat_settings.max_tokens
                )
                
                # Print response and get complete text
                response_text = self.print_streaming_response(response_iterator)
                
                # Update history
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": response_text})
                self.save_history()
                
            except KeyboardInterrupt:
                print("\nInterrupted. Type '/quit' or '/exit' to end the chat.")
            except Exception as e:
                print(f"\nError: {str(e)}", file=sys.stderr)

def main():
    """Main entry point for the CLI."""
    cli = ChatCLI()
    cli.run()

if __name__ == "__main__":
    main() 