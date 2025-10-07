# Jerry AI Assistant

**Self-hosted AI advisor for Australian renewable energy and smart home automation**

Jerry is a containerized, self-hosted AI assistant that provides expert advice on renewable energy systems, solar installations, battery storage, and smart home automation specifically tailored for Australian homeowners and businesses.

## 🌟 Features

- **🏠 Australian Energy Expertise**: Specialized knowledge of Australian energy standards, regulations, and best practices
- **🤖 Grandfatherly Persona**: Warm, patient, and knowledgeable personality that explains complex topics clearly
- **🚢 Fully Containerized**: Runs entirely in containers using Podman with no external dependencies
- **🧠 Local AI Models**: Uses llama.cpp for private, offline AI inference
- **📚 Knowledge Base**: RAG (Retrieval Augmented Generation) with ChromaDB vector store
- **🔐 Security Focused**: Zero-trust networking, encrypted communications, and secure authentication
- **📱 Web Interface**: Modern web-based chat interface with real-time messaging
- **🎯 Agentic Capabilities**: LangChain-powered tools for web research and dynamic responses
- **📊 Monitoring**: Built-in health checks, metrics, and performance monitoring

## 🏗️ Architecture

Jerry uses a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Chat      │    │  Agent Service  │    │  Model Service  │
│   (Port 8004)   │◄──►│   (Port 8003)   │◄──►│   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
┌─────────────────┐    ┌─────────────────┐               │
│   RAG Service   │    │   Vector DB     │               │
│   (Port 8002)   │◄──►│ ChromaDB (8000) │               │
└─────────────────┘    └─────────────────┘               │
                                                         │
┌──────────────────────────────────────────────────────────┐
│                    Podman Pod Network                    │
└──────────────────────────────────────────────────────────┘
```

### Service Components

- **Web Chat Service**: FastAPI-based web interface with WebSocket support
- **Agent Service**: LangChain agent with conversation management and tool integration
- **Model Service**: llama.cpp-based local LLM inference with GGUF model support
- **RAG Service**: Vector database integration for knowledge retrieval
- **Vector DB**: ChromaDB for storing and searching document embeddings

## 🚀 Quick Start

### Prerequisites

- **Podman**: Container runtime (version 4.0+)
- **Python**: 3.11+ (for development only)
- **uv**: Fast Python package manager
- **Git**: For cloning the repository

#### Install Prerequisites (Ubuntu/Debian)

```bash
# Install Podman
sudo apt update && sudo apt install -y podman

# Verify installations
podman --version
```

### 1. Clone and Setup

```bash
git clone https://github.com/LibreHEMS/Jerry.git
cd Jerry
```

### 2. Deploy Jerry

```bash
# Full deployment (tests, build, deploy)
./deploy-podman.sh deploy

# Or for quick start without tests
./deploy-podman.sh start
```

### 3. Access Jerry

Once deployed, access Jerry through:

- **Web Interface**: http://localhost:8004
- **API Documentation**: http://localhost:8003/docs (Agent Service)
- **Vector DB**: http://localhost:8000 (ChromaDB)

### 4. First Conversation

Open http://localhost:8004 in your browser and start chatting with Jerry about:

- Solar panel sizing and installation
- Battery storage recommendations
- Energy efficiency improvements
- Australian energy regulations and rebates
- Smart home automation integration

## 🛠️ Development

### Local Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Code quality checks
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/

# Type checking
uv run mypy src/ --ignore-missing-imports
```

### Project Structure

```
Jerry/
├── src/                          # Main application code
│   ├── bot/                      # Discord bot integration (optional)
│   ├── data/                     # Data models and schemas
│   ├── prompts/                  # AI system prompts and personality
│   ├── rag/                      # RAG pipeline components
│   ├── services/                 # Microservice implementations
│   │   ├── agent_service.py      # LangChain agent
│   │   ├── model_service.py      # LLM inference
│   │   ├── rag_service.py        # Vector search
│   │   └── web_chat_server.py    # Web interface
│   └── utils/                    # Shared utilities
├── configs/                      # Container configurations
│   ├── Dockerfile.agent         # Agent service container
│   ├── Dockerfile.model         # Model service container
│   ├── Dockerfile.rag           # RAG service container
│   └── Dockerfile.webchat       # Web chat container
├── k8s/                         # Kubernetes manifests (for cluster deployment)
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── contract/                # API contract tests
├── data/                        # Persistent data (created on first run)
│   ├── chroma/                  # Vector database storage
│   ├── documents/               # Knowledge base documents
│   └── models/                  # AI model files
└── Resources/                   # Knowledge base source documents
```

## 📚 Knowledge Base

Jerry's knowledge base includes:

- **Australian Energy Standards**: AS/NZS standards for solar and electrical installations
- **Regulatory Information**: Clean Energy Council guidelines and state regulations
- **Product Specifications**: Solar panels, inverters, and battery systems
- **Technical Guides**: Installation procedures and maintenance best practices
- **Smart Home Integration**: Home Assistant, OpenHAB, and IoT device guides

### Adding New Documents

```bash
# Place documents in Resources/ directory
cp your-document.pdf Resources/

# Rebuild RAG service to process new documents
./deploy-podman.sh build
./deploy-podman.sh restart
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# GPU Support (cpu, nvidia, intel)
export GPU_TYPE=nvidia

# Development mode
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=DEBUG

# Model configuration
export DEFAULT_MODEL=llama-2-7b-chat.Q4_K_M.gguf
export MODEL_CONTEXT_LENGTH=4096

# Security (change for production)
export AUTH_SECRET_KEY=your-secret-key
export JWT_SECRET=your-jwt-secret
```

### Custom Models

Jerry supports any GGUF format model:

1. Download model files to `data/models/`
2. Update `DEFAULT_MODEL` environment variable
3. Restart the model service

Popular models:
- **Llama 2 7B**: Good balance of speed and quality
- **Mistral 7B**: Excellent instruction following
- **Code Llama**: For technical coding questions

## 🚢 Deployment Options

### Local Development (Podman)

```bash
./deploy-podman.sh deploy
```

### Kubernetes Cluster

```bash
# For full Kubernetes deployment
./deploy-k8s.sh deploy
```

### Production Considerations

1. **Security**: Update authentication secrets
2. **Models**: Use larger models for better quality
3. **Resources**: Allocate sufficient CPU/RAM/GPU
4. **Monitoring**: Set up log aggregation and metrics
5. **Backups**: Regular backup of vector database

## 🔍 Monitoring & Debugging

### Service Status

```bash
# Check all services
./deploy-podman.sh status

# Debug issues
./deploy-podman.sh debug

# View logs
podman logs jerry-pod-agent-service
```

### Health Checks

Each service provides health endpoints:

- **Agent Service**: http://localhost:8003/health
- **Model Service**: http://localhost:8001/health  
- **RAG Service**: http://localhost:8002/health
- **Vector DB**: http://localhost:8000/api/v1/heartbeat

### Performance Metrics

Access Prometheus metrics at `/metrics` endpoint on each service.

## 📚 Comprehensive Documentation

Jerry includes extensive documentation for Australian energy technologies and integrations:

### Energy Management Systems
- **[EMHASS Integration](Resources/emhass_integration.md)**: Complete guide to Energy Management for Home Assistant
- **[Home Assistant Integration](Resources/home_assistant_integration.md)**: Comprehensive HA setup for energy management
- **[Jinja2 Templates](Resources/jinja2_templates.md)**: Advanced templating for energy automations

### Australian Energy Markets
- **[Amber Electric Integration](Resources/amber_electric_integration.md)**: Real-time wholesale electricity pricing
- **[Feed-in Tariffs](Resources/feed_in_tariffs.md)**: Current Australian feed-in tariff information
- **[Household Solar Guide](Resources/guide_to_household_solar.md)**: Complete solar installation guide

### Advanced Technologies
- **[Vehicle-to-Grid (V2G)](Resources/vehicle_to_grid_v2g.md)**: V2G implementation and optimization
- **[Open Source EMS](Resources/open_source_ems.md)**: Open source energy management solutions

### Technical Documentation
- **[API Documentation](docs/api.md)**: Complete API reference
- **[Deployment Guide](docs/deployment.md)**: Production deployment instructions
- **[Architecture Guide](specs/001-jerry-self-hosted/)**: Detailed technical specifications

## 🏭 Production Deployment

### Quick Production Setup
```bash
# Validate environment and configuration
./deploy-production.sh validate

# Generate secure production secrets
./deploy-production.sh secrets

# Full production deployment with monitoring
./deploy-production.sh deploy
```

### Production Features
- ✅ **Security Hardening**: Secure secrets, HTTPS, rate limiting
- ✅ **Health Monitoring**: Comprehensive health checks and metrics  
- ✅ **Performance Optimization**: Caching, resource limits, tuning
- ✅ **Backup & Recovery**: Automated backups and disaster recovery
- ✅ **Monitoring**: Prometheus metrics, alerting, log aggregation
- ✅ **Documentation**: Auto-generated API docs and operational guides

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Test** your changes (`./deploy-podman.sh test`)
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Standards

- **Python 3.11+** with type hints
- **Ruff** for linting and formatting
- **Pytest** for testing
- **FastAPI** for web services
- **Pydantic** for data validation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests on [GitHub Issues](https://github.com/LibreHEMS/Jerry/issues)
- **Discussions**: Join the community on [GitHub Discussions](https://github.com/LibreHEMS/Jerry/discussions)
- **Documentation**: Full documentation at [docs/](docs/)

## 🏆 Acknowledgments

- **LangChain** for the agentic AI framework
- **ChromaDB** for vector storage
- **llama.cpp** for efficient model inference
- **FastAPI** for the web framework
- **Podman** for containerization
- **Australian Clean Energy Council** for standards and guidelines

---

**Built with ❤️ for the Australian renewable energy community**
   - Local: http://localhost:30004
   - Tunnel: Configure Cloudflare Tunnel for external access

## Services

- **Vector DB**: ChromaDB for document embeddings
- **Model Service**: llama.cpp with local models
- **RAG Service**: Retrieval-augmented generation
- **Agent Service**: Intelligent conversation management
- **Web Chat**: Secure web interface with authentication

## Security

- Container security hardening
- Authentication via Cloudflare Access or JWT
- Network isolation
- Resource limits and monitoring

## Configuration

Environment variables can be configured in `.env.staging` for staging deployment.

## License

MIT License - see LICENSE file for details.