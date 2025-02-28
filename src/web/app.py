"""
Web interface for the DeepSeek chatbot.
"""

import json
import signal
import sys
from flask import Flask, render_template, request, jsonify
from ..chat.client import DeepSeekClient
from ..config.settings import chat_settings, api_settings
from ..utils.helpers import create_chat_messages
from ..utils.search import search_and_scrape

app = Flask(__name__)
client = DeepSeekClient(api_key=api_settings.api_key, model=chat_settings.model)

# Store chat history in memory (you might want to use a database in production)
chat_history = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down the server...")
    sys.exit(0)

@app.route('/')
def home():
    """Render the chat interface."""
    return render_template('chat.html')

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the server."""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Empty message'})
    
    # Handle search command
    if user_message.lower().startswith('/search '):
        search_query = user_message[8:].strip()
        if search_query:
            search_results = search_and_scrape(search_query)
            chat_history.extend([
                {"role": "user", "content": f"Please search for information about: {search_query}"},
                {"role": "assistant", "content": f"Here are the search results:\n\n{search_results}"}
            ])
            return jsonify({
                'response': search_results,
                'history': chat_history
            })
    
    # Regular chat message
    messages = create_chat_messages(
        user_message=user_message,
        system_message=chat_settings.system_message,
        chat_history=chat_history
    )
    
    # Get response
    response_iterator = client.chat(
        messages=messages,
        stream=True,
        temperature=chat_settings.temperature,
        max_tokens=chat_settings.max_tokens
    )
    
    # Collect response
    response_text = ""
    for chunk in response_iterator:
        response_text += chunk
    
    # Update history
    chat_history.extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response_text}
    ])
    
    return jsonify({
        'response': response_text,
        'history': chat_history
    })

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear chat history."""
    global chat_history
    chat_history = []
    return jsonify({'status': 'success'})

def main():
    """Run the web application."""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nBunnyChat web interface running at http://localhost:5000")
    print("Press Ctrl+C to quit")
    
    try:
        app.run(debug=False, port=5000)  # Set debug=False for cleaner shutdown
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        sys.exit(0)

if __name__ == '__main__':
    main() 