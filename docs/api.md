# Jerry AI - API Documentation

This document provides comprehensive API documentation for all Jerry AI services.

## Overview

Jerry AI consists of multiple microservices that work together to provide an intelligent assistant platform:

- **Agent Service**: Main AI agent orchestration
- **Model Service**: Local LLM inference
- **RAG Service**: Knowledge base search and retrieval
- **Bot Service**: Discord bot interface

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord Bot   │    │  Agent Service  │    │  Model Service  │
│     (Python)    │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   RAG Service   │
                       │   (FastAPI)     │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Vector Store  │
                       │   (Chroma DB)   │
                       └─────────────────┘
```

## Authentication

All inter-service communication uses JWT tokens with HMAC signatures:

```
Authorization: Bearer <jwt_token>
```

Or API keys for external access:

```
X-API-Key: <api_key>
```

## Agent Service API

### Base URL
```
http://localhost:8003
```

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <jwt_token>
```

### Chat Endpoint

#### POST /v1/chat
Start or continue a conversation with Jerry.

**Request:**
```json
{
  "message": "What are the benefits of solar panels in Australia?",
  "user_id": "user123",
  "conversation_id": "conv456",
  "stream": false
}
```

**Response:**
```json
{
  "response": "G'day! Solar panels in Australia offer excellent benefits...",
  "conversation_id": "conv456",
  "message_id": "msg789",
  "model_used": "mistral-7b-instruct",
  "tokens_used": 150,
  "processing_time_ms": 1250,
  "rag_sources": [
    {
      "title": "Australian Solar Guide",
      "relevance_score": 0.92,
      "chunk_id": "chunk123"
    }
  ]
}
```

#### POST /v1/chat/stream
Stream conversation responses for real-time chat.

**Request:** Same as `/v1/chat` with `"stream": true`

**Response:** Server-Sent Events (SSE) stream:
```
data: {"type": "token", "content": "G'day!"}
data: {"type": "token", "content": " Solar"}
data: {"type": "done", "conversation_id": "conv456"}
```

### Memory Management

#### GET /v1/conversations/{conversation_id}
Retrieve conversation history.

**Response:**
```json
{
  "conversation_id": "conv456",
  "user_id": "user123",
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "Hello Jerry",
      "timestamp": "2025-10-06T10:00:00Z"
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "G'day! How can I help you today?",
      "timestamp": "2025-10-06T10:00:01Z"
    }
  ],
  "created_at": "2025-10-06T10:00:00Z",
  "updated_at": "2025-10-06T10:00:01Z"
}
```

#### DELETE /v1/conversations/{conversation_id}
Delete a conversation and its history.

**Response:**
```json
{
  "message": "Conversation deleted successfully",
  "conversation_id": "conv456"
}
```

### Health Endpoints

#### GET /health
Basic health check.

**Response:**
```json
{
  "service": "agent",
  "status": "healthy",
  "timestamp": "2025-10-06T10:00:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "checks": [
    {
      "name": "model_service",
      "status": "healthy",
      "duration_ms": 45.2
    },
    {
      "name": "rag_service", 
      "status": "healthy",
      "duration_ms": 12.8
    }
  ]
}
```

#### GET /metrics
Prometheus metrics endpoint.

### Base URL
```
http://localhost:8001/v1
```

### Endpoints

#### Process Message
Process a user message through the Jerry agent.

```http
POST /v1/agent/process
```

**Request Body:**
```json
{
  "user_id": "string",
  "conversation_id": "string", 
  "message": "string",
  "context": {
    "channel_id": "string",
    "guild_id": "string"
  }
}
```

**Response:**
```json
{
  "response": "string",
  "conversation_id": "string",
  "metadata": {
    "tools_used": ["string"],
    "processing_time": 1.23,
    "model_used": "string"
  }
}
```

#### Get Conversation
Retrieve conversation history.

```http
GET /v1/conversations/{conversation_id}
```

**Response:**
```json
{
  "id": "string",
  "user_id": "string", 
  "messages": [
    {
      "id": "string",
      "role": "user|assistant|system",
      "content": "string",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Health Check
Check agent service health.

```http
GET /health
```

**Response:**
```json
{
  "service": "agent",
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime_seconds": 123.45,
  "version": "1.0.0",
  "checks": [
    {
      "name": "model_service",
      "status": "healthy",
      "duration_ms": 10.5
    }
  ]
}
```

## Model Service API

### Base URL
```
http://localhost:8002/v1
```

### Endpoints

#### Chat Completion
Generate chat completion using local LLM.

```http
POST /v1/chat/completions
```

**Request Body:**
```json
{
  "model": "jerry-7b",
  "messages": [
    {
      "role": "system|user|assistant",
      "content": "string"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 512,
  "top_p": 0.9,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chat-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "jerry-7b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "string"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  }
}
```

#### Streaming Chat Completion
Stream chat completion responses.

```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "jerry-7b",
  "messages": [...],
  "stream": true
}
```

**Response (Server-Sent Events):**
```
data: {"id":"chat-abc123","object":"chat.completion.chunk","created":1234567890,"model":"jerry-7b","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chat-abc123","object":"chat.completion.chunk","created":1234567890,"model":"jerry-7b","choices":[{"index":0,"delta":{"content":" there!"},"finish_reason":"stop"}]}

data: [DONE]
```

#### List Models
Get available models.

```http
GET /v1/models
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "jerry-7b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "jerry",
      "context_length": 4096,
      "quantization": "Q4_K_M"
    }
  ]
}
```

#### Model Info
Get specific model information.

```http
GET /v1/models/{model_id}
```

**Response:**
```json
{
  "id": "jerry-7b",
  "object": "model", 
  "created": 1234567890,
  "owned_by": "jerry",
  "context_length": 4096,
  "quantization": "Q4_K_M",
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40
  }
}
```

## RAG Service API

### Base URL
```
http://localhost:8003/v1
```

### Endpoints

#### Search Knowledge Base
Search the knowledge base for relevant information.

```http
POST /v1/search
```

**Request Body:**
```json
{
  "query": "string",
  "top_k": 5,
  "metadata_filter": {
    "document_type": "documentation",
    "category": "API"
  },
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "query": "string",
  "results": [
    {
      "id": "string",
      "document_id": "string", 
      "title": "string",
      "content": "string",
      "metadata": {
        "document_type": "string",
        "source": "string"
      },
      "chunk_index": 0,
      "relevance_score": 0.95
    }
  ],
  "total_results": 5,
  "processing_time": 0.123
}
```

#### Get Context
Get formatted context for a query.

```http
POST /v1/context
```

**Request Body:**
```json
{
  "query": "string",
  "max_chunks": 3,
  "include_metadata": true
}
```

**Response:**
```json
{
  "query": "string",
  "context": "string",
  "chunks_used": 3,
  "sources": [
    {
      "document_id": "string",
      "title": "string",
      "relevance_score": 0.95
    }
  ]
}
```

#### Collection Stats
Get knowledge base statistics.

```http
GET /v1/collections/stats
```

**Response:**
```json
{
  "total_documents": 100,
  "total_chunks": 1500,
  "collection_size": "256MB",
  "last_updated": "2024-01-01T00:00:00Z",
  "embeddings_model": "all-MiniLM-L6-v2"
}
```

## Error Responses

All APIs use standard HTTP status codes and return errors in this format:

```json
{
  "error": {
    "code": "string",
    "message": "string", 
    "details": {}
  },
  "request_id": "string"
}
```

### Common Error Codes

- `400` - Bad Request: Invalid request parameters
- `401` - Unauthorized: Missing or invalid authentication
- `403` - Forbidden: Insufficient permissions
- `404` - Not Found: Resource not found
- `429` - Too Many Requests: Rate limit exceeded
- `500` - Internal Server Error: Server error
- `503` - Service Unavailable: Service temporarily unavailable

## Rate Limiting

All APIs implement rate limiting:

- **Agent Service**: 60 requests/minute per user
- **Model Service**: 30 requests/minute per API key
- **RAG Service**: 100 requests/minute per API key

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
```

## Performance Optimizations

### Caching

Jerry implements multiple caching layers:

1. **Semantic Cache**: Caches similar queries and responses
2. **Memory Cache**: Fast in-memory caching for frequent data
3. **HTTP Cache**: Standard HTTP caching headers

### Connection Pooling

All services use connection pooling for:
- Database connections
- Inter-service HTTP requests
- External API calls

### Monitoring

Comprehensive monitoring with Prometheus metrics:

```
# Request metrics
http_requests_total{service="agent", endpoint="/v1/agent/process", method="POST", status="200"}
http_request_duration_seconds{service="agent", endpoint="/v1/agent/process"}

# Business metrics  
messages_processed_total{service="agent"}
model_inference_duration_seconds{model="jerry-7b"}
rag_search_duration_seconds{collection="knowledge_base"}

# System metrics
process_cpu_usage{service="agent"}
process_memory_bytes{service="agent"}
```

## SDK Examples

### Python

```python
import aiohttp
import asyncio

class JerryClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def process_message(self, message: str, user_id: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/agent/process",
                json={
                    "user_id": user_id,
                    "message": message
                },
                headers=self.headers
            ) as resp:
                return await resp.json()

# Usage
client = JerryClient("http://localhost:8001", "your-api-key")
response = await client.process_message("Hello Jerry!", "user123")
```

### JavaScript

```javascript
class JerryClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = { 'X-API-Key': apiKey };
    }
    
    async processMessage(message, userId) {
        const response = await fetch(`${this.baseUrl}/v1/agent/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...this.headers
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });
        
        return await response.json();
    }
}

// Usage
const client = new JerryClient('http://localhost:8001', 'your-api-key');
const response = await client.processMessage('Hello Jerry!', 'user123');
```

### cURL

```bash
# Process message
curl -X POST "http://localhost:8001/v1/agent/process" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_id": "user123",
    "message": "Hello Jerry!"
  }'

# Search knowledge base
curl -X POST "http://localhost:8003/v1/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "How do I install Jerry?",
    "top_k": 5
  }'

# Chat completion
curl -X POST "http://localhost:8002/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "model": "jerry-7b",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  agent:
    image: jerry/agent:latest
    ports:
      - "8001:8001"
    environment:
      - MODEL_SERVICE_URL=http://model:8002
      - RAG_SERVICE_URL=http://rag:8003
    depends_on:
      - model
      - rag

  model:
    image: jerry/model:latest
    ports:
      - "8002:8002"
    volumes:
      - ./models:/models
    
  rag:
    image: jerry/rag:latest
    ports:
      - "8003:8003"
    volumes:
      - ./data:/data
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jerry-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jerry-agent
  template:
    metadata:
      labels:
        app: jerry-agent
    spec:
      containers:
      - name: agent
        image: jerry/agent:latest
        ports:
        - containerPort: 8001
        env:
        - name: MODEL_SERVICE_URL
          value: "http://jerry-model:8002"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8001
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
```

## Contributing

For API changes and additions:

1. Update OpenAPI specs in `/docs/api/`
2. Update this documentation
3. Add integration tests
4. Update SDK examples

## Support

- **Documentation**: [https://jerry.docs](https://jerry.docs)
- **Issues**: [https://github.com/jerry-ai/jerry/issues](https://github.com/jerry-ai/jerry/issues)
- **Discord**: [https://discord.gg/jerry](https://discord.gg/jerry)