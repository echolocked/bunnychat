# BunnyChat

A chatbot using DeepSeek's API, with support for web search and streaming responses. Features both command-line and web interfaces.

## Features

- Uses DeepSeek-R1 (deepseek-reasoner) model for better reasoning capabilities
- Real-time streaming responses
- Web search integration
- Chat history persistence
- Command history support
- Web interface with:
  * LaTeX math rendering
  * Markdown formatting
  * Code syntax highlighting
  * Modern, responsive design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/echolocked/bunnychat.git
cd bunnychat
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a `.env` file in the project root and add your DeepSeek API key:
```
DEEPSEEK_API_KEY=your_api_key_here
```

## Usage

### Command-line Interface

Run the chatbot in terminal:
```bash
bunnychat
```

Available commands:
- `/search <query>` - Search the internet
- `/clear` - Clear chat history
- `/quit` or `/exit` - End chat

### Web Interface

Run the web interface:
```bash
bunnychat-web
```

Then open http://localhost:5000 in your browser. The web interface provides:
- Beautiful formatting for mathematical expressions using LaTeX
- Markdown rendering for rich text formatting
- Syntax highlighting for code blocks
- Modern, responsive design

Available commands:
- `/help` - Show available commands
- `/search <query>` - Search the internet
- `/clear` - Clear chat history
- `/backup` - Create a backup of current chat
- `/quit` - Shutdown the server

## Development

The project structure:
```
bunnychat/
├── src/
│   ├── chat/
│   │   ├── client.py    # DeepSeek API client
│   │   └── cli.py       # Command-line interface
│   ├── config/
│   │   └── settings.py  # Configuration settings
│   ├── utils/
│   │   ├── helpers.py   # Helper functions
│   │   └── search.py    # Web search utilities
│   └── web/            # Web interface
│       ├── app.py      # Flask application
│       └── templates/  # HTML templates
├── tools/              # External tools
└── requirements.txt    # Project dependencies
```

## License

MIT