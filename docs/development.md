# Jerry AI - Development Environment Configuration

## Development Setup

### Prerequisites
- Python 3.11+
- uv package manager
- Podman or Docker
- Git

### Quick Start
```bash
# Clone repository
git clone https://github.com/LibreHEMS/Jerry.git
cd Jerry

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Start development services
./deploy-podman.sh start
```

### Development Workflow

#### Code Quality
```bash
# Run linting
uv run ruff check src/ tests/

# Fix formatting
uv run ruff format src/ tests/

# Type checking
uv run mypy src/

# Run tests
uv run pytest tests/ -v
```

#### Container Development
```bash
# Build containers
./deploy-podman.sh build

# Start services
./deploy-podman.sh start

# Check status
./deploy-podman.sh status

# View logs
./deploy-podman.sh logs
```

#### Debugging
```bash
# Debug specific service
podman logs jerry-pod-agent-service

# Connect to container
podman exec -it jerry-pod-agent-service bash

# Check health
curl http://localhost:8003/health
```

### IDE Configuration

#### VS Code
Recommended extensions:
- Python (Microsoft)
- Ruff (Astral Software)
- Docker (Microsoft)
- GitLens

#### PyCharm
- Enable type checking
- Configure ruff integration
- Set up Docker integration

### Environment Variables

#### Development
```bash
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=DEBUG
```

#### Testing
```bash
export ENVIRONMENT=testing
export MODEL_SERVICE_URL=http://localhost:8001
export RAG_SERVICE_URL=http://localhost:8002
```

### Git Hooks

Install pre-commit hooks:
```bash
uv run pre-commit install
```

### Troubleshooting

#### Common Issues

1. **Container startup fails**
   - Check port availability
   - Verify container permissions
   - Review logs for errors

2. **Tests fail**
   - Ensure dependencies are installed
   - Check test database setup
   - Verify environment variables

3. **Linting errors**
   - Run `uv run ruff format`
   - Check for import issues
   - Verify type annotations

#### Getting Help

- Check documentation in `docs/`
- Review GitHub issues
- Ask in development discussions
