"""
Web interface for the DeepSeek chatbot.
"""

import json
import signal
import sys
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
from src.chat.client import DeepSeekClient
from src.config.settings import chat_settings, api_settings, web_settings
from src.utils.helpers import create_chat_messages
from src.utils.search import search_and_scrape
from threading import Lock
import logging
import argparse

app = Flask(__name__)
# Set Flask's logger to INFO level
app.logger.setLevel(logging.INFO)
# Set Werkzeug's logger to WARNING level to suppress request logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Enable more detailed logging
app.debug = True

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'js', 'html', 'css', 'json', 'md'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Store chat histories and client instances in memory
chat_histories = {}
chat_clients = {}  # Store separate client instances for each chat
chat_locks = {}

def get_or_create_client(chat_id):
    """Get or create a client for the specific chat."""
    if chat_id not in chat_clients:
        app.logger.debug(f"Creating new client for chat {chat_id}")
        chat_clients[chat_id] = DeepSeekClient()
        chat_locks[chat_id] = Lock()
    return chat_clients[chat_id], chat_locks[chat_id]

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
    try:
        data = request.get_json()
        message = data.get('message')
        chat_id = data.get('chatId', 'default')
        
        if not message:
            return {'error': 'Message is required'}, 400
        
        app.logger.info(f"Processing chat request for chat {chat_id}")
        
        # Initialize chat history if it doesn't exist
        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
        
        # Get chat history
        chat_history = chat_histories[chat_id]
        
        # Create messages with history and system message
        messages = create_chat_messages(
            user_message=message,
            system_message=chat_settings.system_message,
            chat_history=chat_history
        )
        
        client, lock = get_or_create_client(chat_id)
        
        def generate():
            # Add user message to history immediately
            chat_history.append({"role": "user", "content": message})
            
            response_text = ""
            thinking_text = ""
            is_thinking = True  # Start in thinking mode
            assistant_message = {"role": "assistant", "content": ""}
            chat_history.append(assistant_message)
            
            try:
                with lock:
                    app.logger.debug(f"Starting response stream for chat {chat_id}")
                    
                    # Use chat directly with messages instead of chat_stream
                    for chunk_data in client.chat(messages=messages, stream=True):
                        if not chunk_data:
                            continue
                        
                        chunk_type = chunk_data['type']
                        chunk_content = chunk_data['content']
                        
                        if chunk_type == 'thinking':
                            # Stream thinking text immediately
                            thinking_text += chunk_content
                            thinking = {
                                'type': 'thinking',
                                'content': chunk_content,
                                'full_thinking': thinking_text,
                                'chatId': chat_id
                            }
                            yield json.dumps(thinking) + '\n'
                        else:
                            # If this is the first response chunk, mark end of thinking
                            if is_thinking:
                                thinking_end = {
                                    'type': 'thinking_end',
                                    'chatId': chat_id
                                }
                                yield json.dumps(thinking_end) + '\n'
                                is_thinking = False
                            
                            # Add to response text and stream
                            response_text += chunk_content
                            # Update the assistant's message in history
                            assistant_message["content"] = response_text
                            
                            response_data = {
                                'type': 'response',
                                'chunk': chunk_content,
                                'response': response_text,
                                'chatId': chat_id
                            }
                            yield json.dumps(response_data) + '\n'
                    
                    # If we only got thinking text, mark its end
                    if is_thinking:
                        thinking_end = {
                            'type': 'thinking_end',
                            'chatId': chat_id
                        }
                        yield json.dumps(thinking_end) + '\n'
                    
                    app.logger.debug(f"Stream completed for chat {chat_id}")
                    
            except Exception as e:
                app.logger.error(f"Error in stream for chat {chat_id}: {str(e)}")
                # Remove the incomplete assistant message on error
                if chat_history and chat_history[-1]["role"] == "assistant":
                    chat_history.pop()
                error_data = {
                    'error': str(e),
                    'chatId': chat_id
                }
                yield json.dumps(error_data) + '\n'
            finally:
                app.logger.debug(f"Stream cleanup for chat {chat_id}")
        
        return Response(
            stream_with_context(generate()),
            mimetype='application/json'
        )
        
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear chat history and remove client instance."""
    data = request.json
    chat_id = data.get('chatId', 'chat-1')
    
    if chat_id in chat_histories:
        chat_histories[chat_id] = []
    
    # Clean up client instance
    if chat_id in chat_clients:
        print(f"[DEBUG] Removing client for {chat_id} on clear", file=sys.stderr)
        del chat_clients[chat_id]
    
    return jsonify({'status': 'success'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    chat_id = request.form.get('chatId', 'chat-1')  # Get chat ID from form data
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Initialize chat history for this chat if it doesn't exist
        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
        
        chat_history = chat_histories[chat_id]
        
        # Read file content
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add file content to chat history
            chat_history.extend([
                {"role": "user", "content": f"I've uploaded a file named {filename}. Here's its content:\n\n```\n{content}\n```"},
                {"role": "assistant", "content": f"I've received the file '{filename}'. I can help you analyze or work with its content. What would you like to know about it?"}
            ])
            
            return jsonify({
                'success': True,
                'filename': filename,
                'history': chat_history
            })
            
        except UnicodeDecodeError:
            # For binary files, just acknowledge receipt
            chat_history.extend([
                {"role": "user", "content": f"I've uploaded a file named {filename}."},
                {"role": "assistant", "content": f"I've received the binary file '{filename}'. What would you like me to do with it?"}
            ])
            
            return jsonify({
                'success': True,
                'filename': filename,
                'history': chat_history
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def main():
    """Run the web application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='BunnyChat web interface')
    parser.add_argument('--port', type=int, default=web_settings.port,
                      help=f'Port to run the server on (default: {web_settings.port})')
    parser.add_argument('--host', type=str, default=web_settings.host,
                      help=f'Host to run the server on (default: {web_settings.host})')
    parser.add_argument('--debug', action='store_true', default=web_settings.debug,
                      help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Update web settings with command line arguments
    web_settings.port = args.port
    web_settings.host = args.host
    web_settings.debug = args.debug
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"\nBunnyChat web interface running at http://{web_settings.host}:{web_settings.port}")
    print("Press Ctrl+C to quit")
    
    try:
        app.run(
            host=web_settings.host,
            port=web_settings.port,
            debug=web_settings.debug
        )
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        sys.exit(0)

if __name__ == '__main__':
    main() 