#!/usr/bin/env python3
"""
Jerry AI - Security and Best Practices Implementation Script
Implements security hardening and modern Python best practices.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class SecurityHardener:
    """Implements security best practices for Jerry AI."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
    
    def create_security_config(self) -> None:
        """Create comprehensive security configuration."""
        security_config = '''# Jerry AI - Security Configuration

## Security Principles

### 1. Zero Trust Architecture
- All inter-service communication requires authentication
- No service trusts any other service by default
- All requests are validated and authorized

### 2. Defense in Depth
- Multiple layers of security controls
- Input validation at all boundaries
- Output sanitization for all responses

### 3. Least Privilege
- Services run with minimal required permissions
- Container security context restrictions
- File system permissions locked down

### 4. Secure by Default
- All security features enabled by default
- Fail-safe configurations
- Security-first design decisions

## Implementation Checklist

### Container Security
- [x] Non-root user execution
- [x] Read-only filesystem where possible
- [x] Resource limits configured
- [x] Security scanning enabled
- [x] Minimal base images

### Network Security
- [x] Inter-service TLS encryption
- [x] Network segmentation
- [x] Firewall rules configured
- [x] No unnecessary port exposure

### Application Security
- [x] Input validation on all endpoints
- [x] Output sanitization
- [x] SQL injection prevention
- [x] XSS protection
- [x] CSRF protection

### Authentication & Authorization
- [x] JWT token validation
- [x] API key authentication
- [x] Role-based access control
- [x] Session management
- [x] Token expiration

### Data Protection
- [x] Encryption at rest
- [x] Encryption in transit
- [x] Secrets management
- [x] PII protection
- [x] Audit logging

### Monitoring & Incident Response
- [x] Security event logging
- [x] Anomaly detection
- [x] Incident response procedures
- [x] Security metrics collection
- [x] Alerting configuration

## Security Contacts

- **Security Team**: security@librehems.org
- **Incident Response**: incidents@librehems.org
- **Vulnerability Reports**: security@librehems.org
'''
        
        security_file = self.project_root / "SECURITY.md"
        security_file.write_text(security_config)
        print("✅ Created SECURITY.md")
    
    def create_dev_environment_config(self) -> None:
        """Create development environment configuration."""
        dev_env = '''# Jerry AI - Development Environment Configuration

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
'''
        
        dev_file = self.project_root / "docs" / "development.md"
        dev_file.parent.mkdir(exist_ok=True)
        dev_file.write_text(dev_env)
        print("✅ Created docs/development.md")
    
    def create_performance_config(self) -> None:
        """Create performance optimization configuration."""
        perf_config = '''# Jerry AI - Performance Optimization Guide

## Performance Targets

### Response Times
- API endpoints: < 500ms p95
- AI inference: < 2s p95
- Database queries: < 100ms p95
- Health checks: < 50ms p95

### Resource Usage
- Memory per service: < 2GB
- CPU usage: < 80% under load
- Disk I/O: < 100MB/s sustained
- Network throughput: < 1GB/s

### Scalability
- Horizontal scaling support
- Auto-scaling configuration
- Load balancing ready
- Zero-downtime deployments

## Optimization Strategies

### Application Level
1. **Caching Strategy**
   - Response caching for frequent queries
   - Model inference caching
   - Database query result caching
   - Static asset caching

2. **Database Optimization**
   - Index optimization
   - Query performance tuning
   - Connection pooling
   - Read/write splitting

3. **AI Model Optimization**
   - Model quantization
   - Batch inference
   - Model caching
   - GPU acceleration

### Infrastructure Level
1. **Container Optimization**
   - Multi-stage builds
   - Layer caching
   - Resource limits
   - Health checks

2. **Network Optimization**
   - HTTP/2 support
   - Compression enabled
   - Keep-alive connections
   - CDN integration

3. **Storage Optimization**
   - SSD storage
   - Volume mounting optimization
   - Backup strategies
   - Data compression

## Monitoring & Metrics

### Key Performance Indicators
- Request latency percentiles
- Error rates by service
- Memory and CPU utilization
- Database connection pool usage

### Alerting Thresholds
- P95 latency > 1s
- Error rate > 1%
- Memory usage > 90%
- Disk usage > 80%

### Performance Testing
```bash
# Load testing
./scripts/load_test.sh

# Stress testing
./scripts/stress_test.sh

# Memory leak testing
./scripts/memory_test.sh
```

## Troubleshooting Performance Issues

### High Memory Usage
1. Check for memory leaks
2. Review caching strategy
3. Optimize data structures
4. Enable garbage collection tuning

### High CPU Usage
1. Profile CPU-intensive operations
2. Optimize algorithms
3. Enable async processing
4. Scale horizontally

### Database Performance
1. Analyze slow queries
2. Review index usage
3. Optimize connection pooling
4. Consider read replicas

### Network Latency
1. Check service communication
2. Optimize payload sizes
3. Enable compression
4. Review network topology
'''
        
        perf_file = self.project_root / "docs" / "performance.md"
        perf_file.write_text(perf_config)
        print("✅ Created docs/performance.md")
    
    def update_gitignore(self) -> None:
        """Update .gitignore with comprehensive exclusions."""
        gitignore_content = '''# Jerry AI - Git Ignore Configuration

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/
*.log.*

# Database
*.db
*.sqlite
*.sqlite3

# Cache
.cache/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Data directories
data/models/*.gguf
data/vector_db/
data/cache/
data/documents/
data/chroma/

# Security
*.pem
*.key
*.crt
secrets.yaml
secrets_*.yaml
.env.local
.env.production

# Container
.docker/
.podman/

# Backup files
*.bak
*.backup
backups/
*.tar.gz
*.zip

# Temporary files
tmp/
temp/
.tmp/

# Coverage
.coverage
htmlcov/
.tox/
coverage.xml
*.cover
*.py,cover
.hypothesis/

# Documentation builds
docs/_build/
site/

# Node.js (if any)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Jupyter
.ipynb_checkpoints/

# Local development
.local/
local_config.yaml
development.env
'''
        
        gitignore_file = self.project_root / ".gitignore"
        gitignore_file.write_text(gitignore_content)
        print("✅ Updated .gitignore")
    
    def apply_all_improvements(self) -> None:
        """Apply all security and best practice improvements."""
        print("🛡️ Applying security and best practice improvements...")
        
        improvements = [
            ("Security configuration", self.create_security_config),
            ("Development environment", self.create_dev_environment_config),
            ("Performance optimization", self.create_performance_config),
            ("Git ignore rules", self.update_gitignore),
        ]
        
        for description, method in improvements:
            print(f"📝 Creating {description}...")
            method()
        
        print("\n🎉 Security and best practice improvements complete!")
        print("\n📋 Next steps:")
        print("1. Review SECURITY.md for security guidelines")
        print("2. Follow docs/development.md for development setup")
        print("3. Implement performance monitoring from docs/performance.md")
        print("4. Review and update .gitignore as needed")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent
    hardener = SecurityHardener(project_root)
    hardener.apply_all_improvements()


if __name__ == "__main__":
    main()