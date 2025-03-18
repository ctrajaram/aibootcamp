# Technical Blog Generator

A multi-agent AI system for generating comprehensive technical blog posts with AI assistance. This tool helps you create accurate, well-researched technical content with just a few clicks.

## Features

- **AI-Powered Research**: Automatically researches technical topics using web search
- **Multi-Agent System**: Uses specialized AI agents for research and writing
- **Customizable Content**: Adjust depth level (beginner/intermediate/advanced)
- **Modern UI**: Material Design-inspired interface
- **Export Options**: Download generated content as Markdown

## Architecture

The system consists of:

1. **Frontend**: Streamlit web application
2. **Backend**: FastAPI server
3. **Agent System**: CrewAI multi-agent framework
4. **Search Integration**: Google Search API for up-to-date information

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Google Search API key
- Google Custom Search Engine ID

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/technical-blog-generator.git
   cd technical-blog-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_cse_id
   
   # Email verification configuration
   RESEND_API_KEY=your_resend_api_key_here
   RESEND_FROM_EMAIL=your_from_email_here
   RESEND_FROM_NAME=TechMuse
   BASE_URL=http://localhost:8501
   EDUCATIONAL_MODE=false
   VERIFIED_EMAIL=your_verified_email_here
   ```

   You can copy the `.env.template` file to create your `.env` file:
   ```bash
   cp .env.template .env
   ```
   Then edit the `.env` file with your actual API keys and configuration.

4. For Streamlit Cloud deployment, add these same variables to your Streamlit secrets:
   - Go to your Streamlit Cloud dashboard
   - Select your app
   - Go to "Settings" > "Secrets"
   - Add the same variables as in your `.env` file

## Usage

1. Start the backend server:
   ```bash
   python run_backend.py
   ```

2. In a separate terminal, start the Streamlit frontend:
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

3. Open your browser and navigate to http://localhost:8501

4. Enter a technical topic, keywords, and select the depth level

5. Click "Generate Content" and wait for the AI to create your blog post

6. Edit the generated content as needed and download as Markdown

## Project Structure

```
technical-blog-generator/
├── app/
│   └── agents/
│       ├── researcher.py     # Single agent implementation
│       └── multi_agent.py    # Multi-agent implementation
├── backend/
│   ├── app.py               # FastAPI backend
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   └── streamlit_app.py     # Streamlit frontend
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
├── run_backend.py           # Script to run the backend
└── test_*.py                # Test scripts
```

## Development

### Testing

The project includes several test scripts:

- `test_search.py`: Test the web search functionality
- `test_researcher.py`: Test the researcher agent
- `test_multi_agent.py`: Test the multi-agent system

Run tests with:
```bash
python test_search.py
python test_researcher.py
python test_multi_agent.py
```

## License

MIT

## Acknowledgements

- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [LangChain](https://github.com/langchain-ai/langchain)
- [Streamlit](https://streamlit.io/)
- [FastAPI](https://fastapi.tiangolo.com/) 