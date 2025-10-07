# Jerry AI Assistant - Deployment Guide

This guide covers the secure deployment of Jerry AI assistant using containerized microservices with Tailscale networking.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Security Overview](#security-overview)
- [Tailscale Network Setup](#tailscale-network-setup)
- [Container Deployment](#container-deployment)
- [Service Configuration](#service-configuration)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Linux server (Ubuntu 20.04+ or RHEL 8+ recommended)
- Minimum 8GB RAM, 16GB recommended
- 50GB+ available disk space
- Docker or Podman installed
- Python 3.11+

### Required Accounts and Tokens
- Discord bot token
- Tailscale account (free tier sufficient)
- Optional: LangSmith account for agent monitoring

## Security Overview

Jerry implements defense-in-depth security:

### Container Security
- Non-root user execution (UID 1000)
- Minimal base images with security updates
- Read-only filesystems where possible
- Capability dropping and privilege restrictions
- Resource limits and health checks

### Network Security
- Tailscale VPN for secure remote access
- Internal container network isolation
- Services bound to localhost by default
- No direct internet exposure of internal APIs

### Application Security
- JWT-based inter-service authentication
- HMAC signatures for API requests
- Encrypted secrets management
- Rate limiting and request validation

## Tailscale Network Setup

### 1. Install Tailscale

```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# RHEL/CentOS
sudo yum install yum-utils
sudo yum-config-manager --add-repo https://pkgs.tailscale.com/stable/rhel/tailscale.repo
sudo yum install tailscale

# Start and enable Tailscale
sudo systemctl enable --now tailscaled
```

### 2. Authenticate with Tailscale

```bash
# Join your Tailscale network
sudo tailscale up

# Follow the authentication URL provided
# This connects your server to your Tailscale network
```

### 3. Configure Tailscale Settings

#### Enable Subnet Routes (Optional)
If you want to access the entire server subnet through Tailscale:

```bash
# Advertise subnet routes
sudo tailscale up --advertise-routes=192.168.1.0/24

# Approve routes in Tailscale admin console
# Go to https://login.tailscale.com/admin/machines
# Find your machine and approve the subnet routes
```

#### Configure Exit Node (Optional)
To use the server as an exit node:

```bash
# Advertise as exit node
sudo tailscale up --advertise-exit-node

# Approve in admin console
```

### 4. Set Machine Name and Tags

```bash
# Set a descriptive name
sudo tailscale up --hostname=jerry-ai-server

# Add tags for organization (configure tags in admin console first)
sudo tailscale up --advertise-tags=tag:jerry,tag:ai-server
```

### 5. Configure ACLs (Access Control Lists)

In your Tailscale admin console, configure ACLs to restrict access:

```json
{
  "tagOwners": {
    "tag:jerry": ["user@example.com"],
    "tag:ai-server": ["user@example.com"]
  },
  
  "acls": [
    // Allow tagged devices to communicate with Jerry services
    {
      "action": "accept",
      "src": ["tag:jerry"],
      "dst": ["tag:ai-server:8001-8003", "tag:ai-server:22"]
    },
    
    // Allow admin access from specific users
    {
      "action": "accept", 
      "src": ["user@example.com"],
      "dst": ["tag:ai-server:*"]
    }
  ]
}
```

## Container Deployment

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/LibreHEMS/Jerry.git
cd Jerry

# Create required directories
mkdir -p data/{models,documents,vector_db,chroma,bot}
mkdir -p logs
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (IMPORTANT: Set secure values!)
nano .env
```

#### Critical Environment Variables

```bash
# Discord Bot (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Security (Generate strong secrets!)
JWT_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Production Security Settings
ENVIRONMENT=production
REQUIRE_HTTPS=true
SECURE_COOKIES=true
ALLOWED_ORIGINS=https://yourdomain.com

# Tailscale Network
TAILSCALE_HOSTNAME=jerry-ai-server
```

### 3. Generate Production Secrets

```bash
# Use Jerry's secret generation utility
python -c "
from src.utils.config import generate_production_secrets
secrets = generate_production_secrets()
for key, value in secrets.items():
    print(f'{key}={value}')
"
```

### 4. Build and Deploy

```bash
# Build all services
podman-compose build

# Deploy services
podman-compose up -d

# Check service status
podman-compose ps
podman-compose logs
```

## Service Configuration

### Model Service Configuration

#### Download Models

```bash
# Create models directory
mkdir -p data/models

# Download recommended model (example)
cd data/models
wget https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/pytorch_model.bin

# Or use a GGUF model for llama.cpp
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

#### Model Configuration

```yaml
# configs/model_configs/default.yaml
model:
  name: "mistral-7b-instruct-v0.1.Q4_K_M.gguf"
  type: "llama_cpp"
  params:
    n_ctx: 4096
    n_threads: 4
    temperature: 0.7
    top_p: 0.9
    max_tokens: 512
```

### Knowledge Base Population

```bash
# Populate from Resources directory
podman exec jerry-rag-service python -m data_ingestion.vector_populate add-resources

# Add custom documents
podman exec jerry-rag-service python -m data_ingestion.vector_populate add-directory /app/data/documents

# Check knowledge base stats
podman exec jerry-rag-service python -m data_ingestion.vector_populate stats
```

### Discord Bot Setup

1. Create Discord application at https://discord.com/developers/applications
2. Create bot and copy token to `.env`
3. Invite bot to server with appropriate permissions
4. Configure guild ID in `.env`

## Service Access Through Tailscale

### Direct Service Access

```bash
# Get your server's Tailscale IP
tailscale ip -4

# Access services (replace with your Tailscale IP)
curl http://100.x.x.x:8001/health  # Model service
curl http://100.x.x.x:8002/health  # RAG service  
curl http://100.x.x.x:8003/health  # Agent service
```

### SSH Access

```bash
# SSH through Tailscale (more secure than exposing SSH to internet)
ssh user@jerry-ai-server

# Or using Tailscale IP
ssh user@100.x.x.x
```

### Secure Web Interface (Future)

```bash
# When web interface is added, access via:
https://jerry-ai-server/
# or
https://100.x.x.x/
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
podman-compose ps

# Check individual service health
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health

# View logs
podman-compose logs -f discord-bot
podman-compose logs -f model-service
```

### System Monitoring

```bash
# Monitor resource usage
podman stats

# Check Tailscale status
sudo tailscale status

# Monitor disk usage
df -h data/
```

### Updates and Maintenance

```bash
# Update containers
git pull
podman-compose build
podman-compose up -d

# Backup data
tar -czf jerry-backup-$(date +%Y%m%d).tar.gz data/ logs/

# Update Tailscale
sudo tailscale update
```

### Log Management

```bash
# View aggregated logs
podman-compose logs --tail=100 -f

# Service-specific logs
podman logs jerry-discord-bot
podman logs jerry-model-service
podman logs jerry-rag-service
podman logs jerry-agent-service

# Log rotation (automatic via container config)
# Logs are limited to 10MB per service with 5 backup files
```

## Troubleshooting

### Common Issues

#### Container Startup Issues

```bash
# Check container status
podman-compose ps

# View detailed logs
podman-compose logs service-name

# Restart specific service
podman-compose restart service-name
```

#### Model Loading Issues

```bash
# Check model file permissions
ls -la data/models/

# Verify model configuration
podman exec jerry-model-service cat /app/configs/model_configs/default.yaml

# Check model service logs
podman logs jerry-model-service
```

#### Discord Connection Issues

```bash
# Verify bot token
echo $DISCORD_BOT_TOKEN

# Check Discord API connectivity
curl -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  https://discord.com/api/v10/users/@me

# View bot logs
podman logs jerry-discord-bot
```

#### Tailscale Connectivity Issues

```bash
# Check Tailscale status
sudo tailscale status

# Restart Tailscale
sudo systemctl restart tailscaled

# Re-authenticate if needed
sudo tailscale up

# Check firewall rules
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # RHEL/CentOS
```

### Performance Tuning

#### Memory Optimization

```bash
# Adjust memory limits in podman-compose.yml
# Monitor memory usage
free -h
podman stats --no-stream
```

#### CPU Optimization

```bash
# Adjust CPU limits and model threads
# Edit configs/model_configs/default.yaml
# Set n_threads based on available cores
```

### Security Considerations

#### Regular Security Updates

```bash
# Update base images
podman-compose pull
podman-compose build --no-cache
podman-compose up -d

# Update system packages
sudo apt update && sudo apt upgrade  # Ubuntu
sudo yum update  # RHEL/CentOS
```

#### Secret Rotation

```bash
# Generate new secrets periodically
python -c "
from src.utils.config import generate_production_secrets
secrets = generate_production_secrets()
print('Update these in your .env file:')
for key, value in secrets.items():
    print(f'{key}={value}')
"

# After updating .env, restart services
podman-compose restart
```

#### Network Security

```bash
# Verify internal network isolation
podman network ls
podman network inspect jerry-internal

# Check port bindings (should be localhost only)
netstat -tlnp | grep -E ':(8001|8002|8003)'
```

## Production Deployment Checklist

- [ ] Tailscale configured with proper ACLs
- [ ] Strong secrets generated and configured
- [ ] Discord bot token configured
- [ ] SSL/TLS certificates configured (if web interface)
- [ ] Firewall configured (minimal open ports)
- [ ] Regular backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Log rotation configured
- [ ] Security updates scheduled
- [ ] Access control reviewed
- [ ] Network isolation verified
- [ ] Resource limits appropriate
- [ ] Health checks functioning
- [ ] Documentation updated

## Support and Resources

- Jerry Repository: https://github.com/LibreHEMS/Jerry
- Tailscale Documentation: https://tailscale.com/kb/
- Discord Developer Portal: https://discord.com/developers/docs/
- Podman Documentation: https://docs.podman.io/

For additional support, create an issue in the Jerry repository with:
- System information (`uname -a`, `podman version`)
- Tailscale status (`tailscale status`)
- Service logs (`podman-compose logs`)
- Configuration (redacted sensitive information)