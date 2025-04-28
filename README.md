# Chatbot

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

## Description

The Python RAG Chatbot is a sophisticated retrieval-augmented generation (RAG) system that combines vector search, document reranking, and language generation to provide highly relevant and context-aware responses. This project leverages Django for database management, FastAPI for the API layer, and OpenAI for language modeling.

## Features

- **Vector Search**: Efficient similarity search using vector embeddings stored in a PostgreSQL database with pgvector.
- **Document Reranking**: Enhanced response quality through cross-encoder reranking based on query relevance.
- **Scalability**: Designed to handle large-scale document sets and provide quick responses.
- **API Integration**: Exposes an easy-to-use API for querying the chatbot.
- **Environment Config**: Uses environment variables for sensitive configurations, ensuring security.

## Installation

### Prerequisites

- Python 3.x
- PostgreSQL with `pgvector` extension installed
- Django
- FastAPI
- OpenAI API key

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/python-rag-chatbot.git
   cd python-rag-chatbot
   ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
Create a .env file in the project root and add necessary environment variables. For example:

    ```bash 
    OPENAI_API_KEY=your_openai_api_key
    ```

5. Apply migrations and set up the database:

    ```bash
    python manage.py migrate

    ```

6. Run the Django development server:

    ```bash
    python manage.py runserver

    ```

## Configuration

- Environment Variables: The .env file should contain all necessary environment variables, such as API keys and database settings.
- Database: Ensure that PostgreSQL is set up with the pgvector extension for vector search capabilities.

## License

- This project is licensed under the MIT License. See the LICENSE file for more details. 

## Acknowledgments

- **Django** - For the web framework.
- **FastAPI** - For the high-performance API layer.
- **OpenAI** - For the language model API.
- **pgvector** - For the vector similarity search extension in PostgreSQL.
