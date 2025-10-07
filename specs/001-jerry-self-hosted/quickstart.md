# Quickstart: Jerry Self-Hosted AI Migration

**Date**: 2025-10-06  
**Feature**: Jerry Self-Hosted AI Migration  
**Purpose**: Validate end-to-end functionality after implementation

## Prerequisites

### System Requirements
- Linux server with Docker/Podman support
- Minimum 16GB RAM, 8 CPU cores, 100GB storage
- Python 3.11+ installed
- Git and build tools available

### Required Accounts/Tokens
- Discord Bot Token (from Discord Developer Portal)
- Discord Guild/Server for testing
- GitHub account for repository access

### Network Requirements
- Internet access for initial model downloads
- Port availability: 8000-8005 for internal services
- Tailscale account (optional, for secure networking)

## Installation Steps

### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/LibreHEMS/Jerry.git
cd Jerry

# Switch to feature branch
git checkout 001-jerry-self-hosted

# Initialize Python environment
uv init
uv pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration file
vim .env
```

**Required Environment Variables:**
```
# Discord Configuration
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_test_guild_id

# Model Service Configuration
MODEL_SERVICE_URL=http://localhost:8001
MODEL_NAME=llama-3.1-8b-instruct
MODEL_QUANTIZATION=Q4_K_M

# RAG Service Configuration  
RAG_SERVICE_URL=http://localhost:8002
VECTOR_DB_PATH=./data/vector_db

# Agent Service Configuration
AGENT_SERVICE_URL=http://localhost:8003
LANGCHAIN_API_KEY=optional_for_langsmith

# Security
JWT_SECRET=generate_random_secret_here
ENCRYPTION_KEY=generate_32_byte_key_here
```

### 3. Model Download
```bash
# Download recommended model
./scripts/download-model.sh llama-3.1-8b-instruct Q4_K_M

# Verify model download
ls -la models/
```

### 4. Knowledge Base Setup
```bash
# Create knowledge base directory
mkdir -p data/knowledge_base

# Copy sample Australian energy documents
cp -r Resources/ data/knowledge_base/

# Process documents into vector database
python scripts/populate_knowledge_base.py
```

### 5. Service Deployment
```bash
# Start all services with podman-compose
podman-compose up -d

# Wait for services to be ready (2-3 minutes for model loading)
./scripts/wait-for-services.sh

# Check service health
podman-compose ps
curl http://localhost:8001/v1/health
curl http://localhost:8002/v1/health
curl http://localhost:8003/v1/health
```

## Validation Tests

### 1. Basic Service Health
**Test**: Verify all services are running and responding
```bash
# Run health check script
./scripts/health_check.py

# Expected output:
# ✅ Model Service: HEALTHY (response: 45ms)
# ✅ RAG Service: HEALTHY (response: 12ms) 
# ✅ Agent Service: HEALTHY (response: 8ms)
# ✅ Discord Bot: CONNECTED (latency: 23ms)
```

### 2. Discord Bot Connection
**Test**: Verify Discord bot is online and responsive
```bash
# Check bot status in Discord
# Bot should appear online with "Jerry Hems" status

# Test basic command
# In Discord: /jerry ping
# Expected response: "G'day! I'm here and ready to help with your energy questions."
```

### 3. Model Service Integration
**Test**: Verify local LLM is responding appropriately
```bash
# Test model API directly
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are Jerry Hems, an Australian energy advisor."},
      {"role": "user", "content": "What is solar panel efficiency?"}
    ]
  }'

# Expected: JSON response with Jerry-style answer about solar efficiency
```

### 4. RAG Knowledge Retrieval  
**Test**: Verify knowledge base search functionality
```bash
# Test RAG service
curl -X POST http://localhost:8002/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Australian solar installation standards", "limit": 3}'

# Expected: JSON with relevant knowledge chunks about Australian standards
```

### 5. Agent Integration Test
**Test**: Full conversation flow through LangChain agent
```bash
# Test agent service
curl -X POST http://localhost:8003/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "I need advice on solar panel sizing for a 200sqm home in Melbourne",
    "conversation_id": "01234567-89ab-cdef-0123-456789abcdef",
    "use_rag": true
  }'

# Expected: Detailed response with RAG sources and tool usage information
```

### 6. End-to-End Discord Test
**Test**: Complete user interaction via Discord interface

**Setup:**
1. Invite bot to test Discord server
2. Ensure bot has appropriate permissions
3. Test in DM and server channels

**Test Scenarios:**

**Scenario A: Basic Energy Question**
```
User: /jerry "What size solar system do I need for a 4-bedroom house?"
Expected: Jerry responds with questions about location, energy usage, 
          and provides personalized sizing recommendations
```

**Scenario B: Technical Knowledge Query**
```
User: /jerry "What are the Australian standards for solar installation?"
Expected: Jerry responds with specific Australian standards (AS/NZS),
          citing knowledge base sources
```

**Scenario C: Complex Advisory Request**
```
User: /jerry "I want to add battery storage to my existing solar system"
Expected: Jerry asks qualifying questions, provides options comparison,
          and includes recent market information via web search
```

### 7. Performance Validation
**Test**: Verify system meets performance requirements
```bash
# Run performance benchmark
python scripts/performance_benchmark.py

# Expected metrics:
# Average response time: < 2000ms
# Cache hit rate: > 60% after warmup
# Memory usage: < 75% of allocated
# CPU usage: < 50% under normal load
```

### 8. Monitoring Validation
**Test**: Verify monitoring and metrics collection
```bash
# Check Prometheus metrics
curl http://localhost:9090/metrics | grep jerry_

# Access Grafana dashboard
# URL: http://localhost:3000
# Default login: admin/admin
# Verify dashboards show real-time metrics
```

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
podman-compose logs [service_name]

# Common causes:
# - Insufficient memory for model loading
# - Port conflicts
# - Missing environment variables
```

**Model loading failures:**
```bash
# Verify model file integrity
sha256sum models/llama-3.1-8b-instruct-q4_k_m.gguf

# Check available memory
free -h

# Restart model service with debug logging
podman-compose restart model-service
```

**Discord bot offline:**
```bash
# Verify bot token
python scripts/verify_discord_token.py

# Check Discord API status
curl https://discordstatus.com/api/v2/status.json
```

**RAG retrieval errors:**
```bash
# Rebuild vector database
rm -rf data/vector_db
python scripts/populate_knowledge_base.py

# Verify document processing
ls -la data/knowledge_base/processed/
```

## Success Criteria

✅ **All services healthy and responsive**  
✅ **Discord bot online and processing commands**  
✅ **Local LLM generating appropriate responses**  
✅ **Knowledge base returning relevant results**  
✅ **Agent orchestrating tools and conversation flow**  
✅ **Performance metrics within acceptable ranges**  
✅ **Monitoring dashboards displaying real-time data**  
✅ **End-to-end user conversations working smoothly**

## Next Steps

After successful validation:

1. **Production Deployment**: Follow production deployment guide
2. **Security Hardening**: Implement Tailscale networking and additional security measures
3. **Knowledge Base Expansion**: Add more Australian energy resources
4. **Performance Tuning**: Optimize based on usage patterns
5. **User Onboarding**: Migrate existing Discord community to new platform

## Support

For issues during quickstart:
- Check troubleshooting section above
- Review service logs: `podman-compose logs`
- Consult documentation in `/docs` directory
- Open GitHub issue with detailed logs and system information