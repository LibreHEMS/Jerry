# Jerry Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.11+ + LangChain, FastAPI, llama.cpp, Chroma DB, uv, ruff (001-jerry-self-hosted)

## Project Structure
```
src/
├── bot/                      # Discord bot integration
├── data/                     # Data models and schemas  
├── prompts/                  # AI system prompts and personality
├── rag/                      # RAG pipeline components
├── services/                 # Microservice implementations
│   ├── agent_service.py      # LangChain agent
│   ├── model_service.py      # LLM inference
│   ├── rag_service.py        # Vector search
│   └── web_chat_server.py    # Web interface
└── utils/                    # Shared utilities
tests/
├── unit/                     # Unit tests
├── integration/              # Integration tests
└── contract/                 # API contract tests
configs/                      # Container configurations
k8s/                         # Kubernetes manifests
data/                        # Persistent data (created on first run)
Resources/                   # Knowledge base source documents
```

## Commands
```bash
# Development
uv sync --dev                 # Install dependencies
uv run pytest tests/ -v      # Run tests
uv run ruff check src/ tests/ --fix  # Lint and fix
uv run ruff format src/ tests/       # Format code
uv run mypy src/ --ignore-missing-imports  # Type check

# Deployment
./deploy-podman.sh deploy     # Full deployment (test, build, deploy)
./deploy-podman.sh start      # Start services
./deploy-podman.sh status     # Check status
./deploy-podman.sh debug      # Debug issues
```

## Code Style
- Python 3.11+ with type hints
- FastAPI for web services
- Pydantic for data validation
- LangChain for AI agents
- ChromaDB for vector storage
- Podman for containerization

## Architecture Principles
- **Microservices**: Each service has a single responsibility
- **Containerized**: All services run in containers
- **Self-hosted**: No external AI service dependencies
- **Secure**: Authentication, encryption, zero-trust networking
- **Agentic**: LangChain tools for dynamic capabilities
- **RAG-enabled**: Vector search for knowledge retrieval

## Jerry Personality
Jerry is a grandfatherly Australian energy advisor with:
- Warm, patient, and knowledgeable personality
- Deep expertise in Australian energy standards and regulations
- Ability to explain complex technical topics clearly
- Focus on renewable energy and smart home automation
- Practical, actionable advice for homeowners and businesses

## Service Architecture
- **Web Chat (8004)**: User interface with WebSocket support
- **Agent Service (8003)**: LangChain agent with conversation management
- **RAG Service (8002)**: Vector database integration
- **Model Service (8001)**: Local LLM inference with llama.cpp
- **Vector DB (8000)**: ChromaDB for document embeddings

## Recent Changes
- 001-jerry-self-hosted: Complete migration to Python-based containerized platform with local AI models

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->