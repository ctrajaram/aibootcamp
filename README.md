# TechMuse: AI Blog Generator

A specialized AI system that produces high-quality technical blog posts using autonomous agent teams.

## Live App

**[https://aibootcamp-techmuse-chan.streamlit.app/](https://aibootcamp-techmuse-chan.streamlit.app/)**

## Architecture

![Architecture Diagram](https://i.imgur.com/PlMRtJF.png)

TechMuse uses a layered architecture:

1. **User Interface**: Streamlit frontend for user interactions
2. **Application Logic**: Authentication and content generation workflows
3. **AI Core**: CrewAI engine orchestrating specialized agents (Research, Write, Edit)
4. **Data & External Services**: SQLite database and Resend email service

## Key Technologies

- **UI**: Streamlit
- **Agent Framework**: CrewAI
- **AI Model**: OpenAI GPT-4o
- **Search**: Google Search API
- **Auth**: Custom system with bcrypt + SQLite
- **Email**: Resend API

## Quick Start (Local Development)

```bash
# Install
git clone https://github.com/ctrajaram/aibootcamp.git
cd aibootcamp
pip install -r requirements.txt

# Configure
# Create .env from .env.example (Add API keys)

# Run
streamlit run frontend/streamlit_app.py
```

## Features

- Create blog posts on any technical topic
- Control technical depth (beginner to advanced)
- AI-powered research using Google Search
- Multi-agent system for comprehensive content
- User management with email verification
- Save and export blogs as Markdown

## Acknowledgements

- [CrewAI](https://github.com/joaomdmoura/crewAI) for agent orchestration
- [OpenAI](https://openai.com/) for GPT-4o model
- [Streamlit](https://streamlit.io/) for the web interface
- [Resend](https://resend.com/) for email services 