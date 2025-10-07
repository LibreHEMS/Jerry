# Data Model: Jerry Self-Hosted AI Migration

**Date**: 2025-10-06  
**Feature**: Jerry Self-Hosted AI Migration  
**Status**: Complete

## Core Entities

### User
**Purpose**: Represents a Discord user interacting with Jerry
```python
@dataclass
class User:
    discord_id: str          # Primary identifier
    username: str            # Discord username
    display_name: str        # Discord display name
    first_interaction: datetime
    last_interaction: datetime
    preferences: Dict[str, Any]  # User-specific settings
    conversation_count: int
```

**Relationships**: 
- Has many Conversations
- Has many Interactions

**Validation Rules**:
- discord_id must be unique and non-empty
- username must match Discord username format
- timestamps must be valid UTC datetime

### Conversation
**Purpose**: Represents a conversation session between user and Jerry
```python
@dataclass
class Conversation:
    id: UUID                    # Primary identifier
    user_discord_id: str        # Foreign key to User
    channel_id: str             # Discord channel/DM identifier
    started_at: datetime
    last_message_at: datetime
    status: ConversationStatus  # ACTIVE, PAUSED, ARCHIVED
    context_summary: str        # Progressive summarization
    message_count: int
    total_tokens_used: int
```

**Relationships**:
- Belongs to User
- Has many Messages
- Has many ContextChunks (for vector storage)

**State Transitions**:
- NEW → ACTIVE (first message)
- ACTIVE → PAUSED (inactivity timeout)
- PAUSED → ACTIVE (new message)
- ACTIVE/PAUSED → ARCHIVED (manual or retention policy)

### Message
**Purpose**: Individual messages within a conversation
```python
@dataclass
class Message:
    id: UUID                    # Primary identifier
    conversation_id: UUID       # Foreign key to Conversation
    role: MessageRole           # USER, ASSISTANT, SYSTEM
    content: str               # Message content
    timestamp: datetime
    tokens_used: int           # For usage tracking
    response_time_ms: int      # Performance metrics
    model_used: str            # Model identifier
    tools_used: List[str]      # Tools invoked for this response
    rag_sources: List[str]     # Documents retrieved for context
```

**Relationships**:
- Belongs to Conversation
- May reference KnowledgeChunks via rag_sources

**Validation Rules**:
- content must be non-empty for USER and ASSISTANT roles
- timestamps must be sequential within conversation
- tokens_used must be positive integer

### KnowledgeChunk
**Purpose**: Represents chunks of knowledge base documents for RAG
```python
@dataclass
class KnowledgeChunk:
    id: UUID                   # Primary identifier
    document_id: str           # Source document identifier
    title: str                 # Document title
    content: str               # Chunk content
    embedding: List[float]     # Vector embedding
    metadata: Dict[str, Any]   # Source, page, section, etc.
    created_at: datetime
    updated_at: datetime
    chunk_index: int           # Position within document
    relevance_score: float     # Current query relevance
```

**Relationships**:
- Belongs to Document (metadata reference)
- Referenced by Messages via rag_sources

**Validation Rules**:
- content must be non-empty
- embedding must match model dimensions
- chunk_index must be sequential within document

### ModelService
**Purpose**: Represents available AI models and their configurations
```python
@dataclass
class ModelService:
    id: str                    # Model identifier
    name: str                  # Human-readable name
    type: ModelType            # LOCAL_LLM, EXTERNAL_API
    endpoint_url: str          # Service endpoint
    max_tokens: int            # Context window limit
    status: ServiceStatus      # HEALTHY, DEGRADED, UNAVAILABLE
    average_response_time: float
    last_health_check: datetime
    config: Dict[str, Any]     # Model-specific parameters
```

**Relationships**:
- Referenced by Messages via model_used

**State Transitions**:
- HEALTHY → DEGRADED (high latency or errors)
- DEGRADED → HEALTHY (recovered performance)
- Any → UNAVAILABLE (service failure)
- UNAVAILABLE → HEALTHY (service restored)

### CacheEntry
**Purpose**: Semantic cache for conversation responses
```python
@dataclass
class CacheEntry:
    id: UUID                   # Primary identifier
    query_hash: str            # Semantic hash of query
    query_embedding: List[float] # Vector for similarity search
    response: str              # Cached response
    model_used: str            # Model identifier
    context_hash: str          # Hash of conversation context
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int           # Time to live
```

**Relationships**:
- Independent entity with semantic relationships via embeddings

**Validation Rules**:
- query_hash must be unique
- embedding must match model dimensions
- ttl_seconds must be positive

### AgentTool
**Purpose**: Represents tools available to the LangChain agent
```python
@dataclass
class AgentTool:
    id: str                    # Tool identifier
    name: str                  # Human-readable name
    description: str           # Tool capability description
    enabled: bool              # Tool availability
    rate_limit: int            # Calls per minute
    current_usage: int         # Current period usage
    last_reset: datetime       # Rate limit reset time
    config: Dict[str, Any]     # Tool-specific parameters
```

**Relationships**:
- Referenced by Messages via tools_used

## Database Schema Considerations

### Storage Strategy
- **Conversation Data**: SQLite for structured data (users, conversations, messages)
- **Vector Data**: Chroma DB for embeddings and semantic search
- **Cache Data**: Redis-compatible in-memory store
- **Configuration**: File-based (YAML/JSON)

### Indexing Strategy
- Primary keys: UUID v4 for distributed compatibility
- Foreign keys: Indexed for query performance
- Timestamps: Indexed for time-range queries
- Discord IDs: Unique indexes for user lookup

### Data Retention Policy
- **Active Conversations**: Retained indefinitely
- **Archived Conversations**: Retained for 2 years
- **Cache Entries**: TTL-based expiration (1-24 hours)
- **Metrics Data**: Aggregated and retained for 1 year

### Privacy Considerations
- User data encrypted at rest
- Conversation data anonymizable on request
- No PII stored in vector embeddings
- Audit log for data access and modifications

## API Data Transfer Objects

### ConversationRequest
```python
@dataclass
class ConversationRequest:
    user_id: str
    message: str
    channel_id: str
    use_rag: bool = True
    use_cache: bool = True
    max_tokens: Optional[int] = None
```

### ConversationResponse
```python
@dataclass
class ConversationResponse:
    message: str
    conversation_id: UUID
    response_time_ms: int
    tokens_used: int
    sources_used: List[str]
    tools_used: List[str]
    cached: bool
```

### HealthCheckResponse
```python
@dataclass
class HealthCheckResponse:
    service: str
    status: ServiceStatus
    response_time_ms: float
    last_check: datetime
    details: Dict[str, Any]
```

## Migration Mapping

### From TypeScript bot.js
- `guild_id` → Conversation.channel_id
- `user_id` → User.discord_id  
- `System_Prompt` → Agent prompt templates
- `Guild_System_Prompt` → Guild-specific prompt templates
- Message handling → Message entity with role mapping

### Data Migration Strategy
1. Export existing conversation data (if any)
2. Transform to new schema format
3. Import with conversation reconstruction
4. Validate data integrity
5. Update Discord bot configuration

## Validation Complete
All entities defined with clear relationships, validation rules, and state transitions. Ready for contract generation.