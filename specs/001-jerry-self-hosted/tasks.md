# Tasks: Jerry Self-Hosted AI Migration

**Input**: Design documents from `/specs/001-jerry-self-hosted/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, discord.py, LangChain, FastAPI, llama.cpp, Chroma DB, uv, ruff
   → Structure: Container-native microservices architecture
2. Load design documents:
   → data-model.md: 7 core entities (User, Conversation, Message, KnowledgeChunk, ModelService, CacheEntry, AgentTool)
   → contracts/: 3 API contracts (agent-service, model-service, rag-service)
   → research.md: Technical decisions for LLM, vector DB, containers, tooling
3. Generate tasks by 7 implementation phases:
   → Phase 1: Foundation & Scaffolding (Python environment, containerization)
   → Phase 2: Core Functionality Porting (Discord bot, model service abstraction)
   → Phase 3: Self-Hosted AI Integration (local LLM deployment and integration)
   → Phase 4: Agentic Brain Implementation (LangChain agent with tools)
   → Phase 5: Knowledge Base & RAG (vector database and retrieval pipeline)
   → Phase 6: Platform Security (networking, authentication, secrets management)
   → Phase 7: Monitoring & Performance (metrics, logging, optimization)
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
   → Infrastructure before application code
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 1: Foundation & Scaffolding
- [x] T001 Create project structure per implementation plan (src/, tests/, data_ingestion/, configs/, docs/)
- [x] T002 Initialize Python environment with uv and configure pyproject.toml
- [x] T003 [P] Configure ruff linting and formatting in ruff.toml
- [x] T004 [P] Create .gitignore for Python projects with model and data exclusions
- [x] T005 [P] Create Dockerfile for discord-bot service in configs/Dockerfile.bot
- [x] T006 [P] Create Dockerfile for model-service in configs/Dockerfile.model
- [x] T007 [P] Create Dockerfile for rag-service in configs/Dockerfile.rag
- [x] T008 Create podman-compose.yml defining all services (discord-bot, model-server, rag-service, vector-db)

## Phase 2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE Phase 3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T009 [P] Contract test POST /v1/chat in tests/contract/test_agent_service.py
- [x] T010 [P] Contract test POST /v1/inference in tests/contract/test_model_service.py  
- [x] T011 [P] Contract test POST /v1/search in tests/contract/test_rag_service.py
- [x] T012 [P] Integration test Discord /jerry command in tests/integration/test_discord_commands.py
- [x] T013 [P] Integration test DM conversation flow in tests/integration/test_dm_flow.py
- [x] T014 [P] Integration test agent with RAG retrieval in tests/integration/test_agent_rag.py

## Phase 3: Core Implementation (ONLY after tests are failing)
- [x] T015 [P] User data model in src/data/models.py
- [x] T016 [P] Conversation data model in src/data/models.py  
- [x] T017 [P] Message data model in src/data/models.py
- [x] T018 [P] Abstract ModelService interface in src/services/model_service.py
- [x] T019 [P] Discord bot client setup in src/bot/bot.py
- [x] T020 [P] Discord command handlers in src/bot/commands.py
- [x] T021 [P] Discord DM handlers in src/bot/handlers.py
- [x] T022 [P] Configuration management in src/utils/config.py
- [x] T023 [P] Logging setup in src/utils/logging.py

## Phase 4: Self-Hosted AI Integration  
- [x] T024 FastAPI model service server in src/services/model_server.py
- [x] T025 LocalModelService implementation for llama.cpp integration in src/services/local_model_service.py
- [x] T026 Model health checks and fallback handling in src/services/model_service.py
- [x] T027 Model configuration loader for different quantizations in src/utils/model_config.py
- [x] T028 Update Discord bot to use LocalModelService in src/bot/bot.py

## Phase 5: Agentic Brain Implementation
- [x] T029 [P] LangChain prompt templates in src/prompts/system_prompts.py
- [x] T030 [P] LangChain agent configuration in src/services/agent_service.py
- [x] T031 [P] Web search tool for LangChain in src/services/tools/web_search.py
- [x] T032 [P] Conversation memory management in src/services/memory.py
- [x] T033 FastAPI agent service server in src/services/agent_server.py
- [x] T034 Agent conversation summarization in src/services/agent_service.py
- [x] T035 Update Discord bot to use agent service in src/bot/handlers.py

## Phase 6: Knowledge Base & RAG
- [x] T036 [P] KnowledgeChunk data model in src/data/models.py
- [x] T037 [P] Chroma vector store setup in src/rag/vector_store.py
- [x] T038 [P] Document embeddings service in src/rag/embeddings.py
- [x] T039 [P] RAG retriever implementation in src/rag/retriever.py
- [x] T040 [P] PDF document processor in data_ingestion/pdf_processor.py
- [x] T041 FastAPI RAG service server in src/services/rag_server.py
- [x] T042 Knowledge base population script in data_ingestion/vector_populate.py
- [x] T043 RAG tool for LangChain agent in src/services/tools/rag_search.py

## Phase 7: Platform Security
- [x] T044 [P] Environment secrets management in src/utils/config.py
- [x] T045 [P] Inter-service authentication in src/utils/auth.py
- [x] T046 Container security configuration in configs/ Dockerfiles
- [x] T047 Tailscale network setup documentation in docs/deployment.md

## Phase 8: Monitoring & Performance
- [x] T048 [P] Semantic cache implementation in src/utils/cache.py
- [x] T049 [P] Prometheus metrics collection in src/utils/metrics.py
- [x] T050 [P] Performance optimization and caching in src/services/
- [x] T051 Health check endpoints for all services
- [x] T052 [P] API documentation generation in docs/api.md

## Dependencies
- Foundation (T001-T008) before all other phases
- Tests (T009-T014) before implementation (T015-T052)
- Data models (T015-T017) before services that use them
- Model service (T018, T024-T028) before agent service (T029-T035)
- Vector store (T037-T038) before RAG service (T039-T043)
- Core services before monitoring (T048-T052)

## Parallel Execution Examples
```bash
# Phase 1 Foundation (can run in parallel):
Task: "Configure ruff linting and formatting in ruff.toml"
Task: "Create .gitignore for Python projects with model and data exclusions"  
Task: "Create Dockerfile for discord-bot service in configs/Dockerfile.bot"
Task: "Create Dockerfile for model-service in configs/Dockerfile.model"

# Phase 2 Contract Tests (can run in parallel):
Task: "Contract test POST /v1/chat in tests/contract/test_agent_service.py"
Task: "Contract test POST /v1/inference in tests/contract/test_model_service.py"
Task: "Contract test POST /v1/search in tests/contract/test_rag_service.py"

# Phase 3 Core Models (can run in parallel):
Task: "User data model in src/data/models.py"
Task: "Abstract ModelService interface in src/services/model_service.py"
Task: "Discord bot client setup in src/bot/bot.py"
Task: "Configuration management in src/utils/config.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Each service can be developed independently after core models
- Container services start after basic implementation is complete
- Knowledge base population happens after RAG infrastructure is ready

## Task Generation Rules
- Each contract file → contract test task marked [P]
- Each data model entity → model creation task
- Each service → interface + implementation tasks
- Different files = can be parallel [P]
- Same file = sequential (no [P])
- Tests before implementation (TDD)
- Infrastructure before application code