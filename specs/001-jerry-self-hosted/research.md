# Research: Jerry Self-Hosted AI Migration

**Date**: 2025-10-06  
**Feature**: Jerry Self-Hosted AI Migration  
**Status**: Complete

## Research Tasks Completed

### Local LLM Selection and Integration
**Decision**: llama.cpp with GGUF format models, served via FastAPI  
**Rationale**: 
- llama.cpp provides excellent performance for local inference
- GGUF format offers optimized quantization for resource efficiency
- FastAPI enables clean REST API interface for model service abstraction
- Strong community support and regular updates
- Hardware flexibility from CPU-only to GPU acceleration

**Alternatives considered**: 
- Ollama: Easier setup but less flexible configuration
- vLLM: Better for high-throughput but overkill for single-server deployment
- Transformers library: More resource intensive, slower inference

### Vector Database for RAG Pipeline
**Decision**: Chroma DB (embedded mode)  
**Rationale**:
- Embedded deployment aligns with self-hosted requirements
- Python-native integration simplifies development
- Built-in embedding model support
- Lightweight resource footprint
- Excellent documentation and community

**Alternatives considered**:
- Milvus: More scalable but complex for single-server deployment
- Weaviate: Feature-rich but heavier resource requirements
- Pinecone: Proprietary service conflicts with self-hosted requirement

### Container Orchestration
**Decision**: Podman with podman-compose  
**Rationale**:
- Rootless containers improve security posture
- Docker-compatible API ensures ecosystem compatibility
- No daemon requirement reduces attack surface
- Built-in support for pod concepts
- Aligns with open-source first principle

**Alternatives considered**:
- Docker Compose: Requires daemon, root privileges by default
- Kubernetes: Overkill complexity for single-server deployment
- Systemd containers: Less ecosystem support

### Python Package Management
**Decision**: uv for package management  
**Rationale**:
- Significantly faster than pip/poetry for dependency resolution
- Built-in virtual environment management
- Excellent caching and reproducibility
- Modern lockfile format
- Growing adoption in Python community

**Alternatives considered**:
- Poetry: Mature but slower dependency resolution
- pip-tools: Simpler but lacks advanced features
- conda: Heavyweight and not pure Python focused

### Code Quality Tools
**Decision**: ruff for linting and formatting  
**Rationale**:
- 100x faster than traditional tools (flake8, black, isort combined)
- Single tool replaces multiple linters/formatters
- Excellent VS Code integration
- Growing ecosystem adoption
- Rust-based performance advantages

**Alternatives considered**:
- Black + flake8 + isort: Traditional but slower
- pylint: Comprehensive but very slow
- autopep8: Limited scope compared to ruff

### LangChain Agent Architecture
**Decision**: LangChain with custom tool integration  
**Rationale**:
- Mature conversation management and memory handling
- Extensive tool ecosystem for web search and document retrieval
- Strong prompt template system for persona preservation
- Built-in support for conversation summarization
- Active development and community

**Alternatives considered**:
- Custom agent implementation: More control but significant development overhead
- LlamaIndex: Focused on RAG but less conversational agent support
- Haystack: Good for search but less Discord-specific patterns

### Secure Networking Solution
**Decision**: Tailscale for private network overlay  
**Rationale**:
- Zero-trust networking model
- Easy setup and management
- Wireguard-based performance
- Cross-platform support
- Free tier suitable for small deployments

**Alternatives considered**:
- Headscale (self-hosted Tailscale): More complex setup
- CloudFlare Tunnels: Introduces external dependency
- VPN solutions: More complex configuration and management

### Monitoring and Observability
**Decision**: Prometheus + Grafana with OpenTelemetry  
**Rationale**:
- Industry standard for metrics collection
- Excellent container ecosystem integration
- Rich visualization capabilities with Grafana
- OpenTelemetry provides future-proof instrumentation
- Self-hosted without external dependencies

**Alternatives considered**:
- ELK stack: Heavier resource requirements
- Cloud monitoring: Conflicts with self-hosted requirement
- Simple logging: Insufficient for production monitoring

## Technical Specifications

### Hardware Requirements
**Minimum Configuration**:
- CPU: 8 cores (x86_64 or ARM64)
- RAM: 16GB
- Storage: 100GB SSD
- Network: 1Gbps

**Recommended Configuration**:
- CPU: 16+ cores with AVX2 support
- RAM: 32GB+ 
- GPU: CUDA-compatible with 8GB+ VRAM (optional but recommended)
- Storage: 200GB+ NVMe SSD
- Network: 10Gbps for high-concurrency scenarios

### Model Selection
**Primary Model**: Llama 3.1 8B Instruct (GGUF Q4_K_M quantization)  
**Rationale**: Optimal balance of capability, resource usage, and instruction following for conversational AI

**Fallback Models**:
- Llama 3.1 7B for lower resource environments
- Mistral 7B Instruct as alternative architecture

### Performance Targets
- **Response Time**: <200ms for cached queries, <2s for RAG lookups
- **Throughput**: 100-1000 concurrent conversations
- **Availability**: 99.9% uptime target
- **Resource Efficiency**: <50% CPU utilization under normal load

## Integration Patterns

### Discord Bot Migration Strategy
1. Maintain existing command interface (`/jerry`, `/donate`)
2. Preserve conversation flow and user experience
3. Abstract model service for seamless backend swapping
4. Implement graceful degradation for service failures

### RAG Pipeline Design
1. Document ingestion pipeline for Australian energy standards
2. Embedding generation with sentence-transformers
3. Semantic search with relevance scoring
4. Context injection for LLM prompts

### Security Architecture
1. Inter-service communication via private network overlay
2. API key authentication for service endpoints
3. Container security with non-root users
4. Secrets management via environment variables

## Research Validation Complete
All technical uncertainties resolved. No NEEDS CLARIFICATION markers remain.