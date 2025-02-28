# BunnyChat

A command-line chatbot using DeepSeek's API, with support for web search and streaming responses.

## Features

- Uses DeepSeek-R1 (deepseek-reasoner) model for better reasoning capabilities
- Real-time streaming responses
- Web search integration
- Chat history persistence
- Command history support

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

Run the chatbot:
```bash
bunnychat
```

Available commands:
- `/search <query>` - Search the internet
- `/clear` - Clear chat history
- `/quit` or `/exit` - End chat

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
│   └── utils/
│       ├── helpers.py   # Helper functions
│       └── search.py    # Web search utilities
├── tools/               # External tools
└── requirements.txt     # Project dependencies
```

## License

MIT