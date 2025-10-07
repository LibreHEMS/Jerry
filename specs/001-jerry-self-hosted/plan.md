
# Implementation Plan: Jerry Self-Hosted AI Migration

**Branch**: `001-jerry-self-hosted` | **Date**: 2025-10-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-jerry-self-hosted/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Migration of Jerry AI advisor from a Deno-based application to a fully self-hosted Python platform featuring a containerized architecture, local LLM, agentic capabilities via LangChain, a RAG knowledge base, and a secure web-based chat interface. Technical approach emphasizes container-native design with Podman orchestration, open-source toolchain, and comprehensive testing.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: LangChain, FastAPI, llama.cpp, Chroma DB, uv, ruff  
**Storage**: Vector database (Chroma), conversation history, knowledge base documents  
**Testing**: pytest with TDD approach, contract tests, integration tests  
**Target Platform**: Linux server with container orchestration (Podman)
**Project Type**: Container-native microservices architecture  
**Performance Goals**: <200ms response time for cached queries, <2s for complex RAG lookups  
**Constraints**: Self-hosted only, open-source components, secure inter-service communication  
**Scale/Scope**: Single-server deployment, 100-1000 concurrent users, Australian energy domain knowledge

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Persona Preservation**: ✅ This feature explicitly preserves Jerry's grandfatherly, knowledgeable, patient persona as a NON-NEGOTIABLE requirement (FR-001). The migration maintains his Australian energy/automation advisor identity.

**Self-Hosted & Sovereign**: ✅ This feature enforces full self-hosting capability with no dependencies on external proprietary services (FR-002). All components run locally in containers.

**Open-Source First**: ✅ All dependencies specified are open-source and community-supported (Python, LangChain, Chroma DB, llama.cpp). No proprietary alternatives used.

**Container-Native**: ✅ The feature is designed as independently deployable container services using Podman orchestration with explicit containerized architecture.

**Security by Design**: ✅ Security requirements are addressed from the start with secure networking, inter-service communication, and container security practices planned.

**Test-Driven Development**: ✅ Tests are planned before implementation with comprehensive coverage including contract tests, integration tests, and TDD approach specified.

**Simplicity & Readability**: ✅ The approach follows modular design with clear service separation and leverages proven patterns (web application, model service abstraction, LangChain agents).

**Technical Standards Alignment**: ✅ This feature uses required tooling (uv, ruff) and follows agentic architecture patterns with LangChain as specified in technical standards.

**Mission Alignment**: ✅ This feature serves Jerry's core mission of empowering Australian homeowners with renewable energy and smart home advice through enhanced capabilities and knowledge base integration.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
```
### Source Code (repository root)
```
# Container-native microservices architecture
src/
├── web/                 # Web frontend service (chat interface)
│   ├── static/
│   └── templates/
├── api/                 # FastAPI backend service
│   ├── __init__.py
│   ├── main.py
│   └── routers/
├── services/            # Core business logic
│   ├── __init__.py
│   ├── model_service.py      # Abstract model interface
│   ├── local_model_service.py # Local LLM implementation
│   └── agent_service.py      # LangChain agent wrapper
├── rag/                 # Knowledge base and retrieval
│   ├── __init__.py
│   ├── vector_store.py
│   ├── retriever.py
│   └── embeddings.py
├── data/                # Data models and schemas
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── utils/               # Shared utilities
│   ├── __init__.py
│   ├── config.py
│   ├── logging.py
│   └── cache.py
└── prompts/             # LangChain prompt templates
    ├── __init__.py
    ├── system_prompts.py
    └── guild_prompts.py

tests/
├── contract/            # API contract tests
├── integration/         # Integration tests
└── unit/               # Unit tests

data_ingestion/          # Knowledge base population scripts
├── __init__.py
├── pdf_processor.py
└── vector_populate.py

configs/                 # Configuration files
├── ruff.toml
├── podman-compose.yml
└── model_configs/

docs/                   # Documentation
├── deployment.md
├── api.md
└── troubleshooting.md
```

**Structure Decision**: Container-native microservices architecture selected to support independent service deployment, scalability, and clear separation of concerns. Each major component (Discord bot, model service, RAG pipeline) can be developed, tested, and deployed independently while maintaining secure inter-service communication.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Break down into 7 implementation phases matching jerry_spek.md structure:
  1. Foundation & Scaffolling (Python environment, containerization)
  2. Core Functionality Porting (Discord bot, model service abstraction)
  3. Self-Hosted AI Integration (local LLM deployment and integration)
  4. Agentic Brain Implementation (LangChain agent with tools)
  5. Knowledge Base & RAG (vector database and retrieval pipeline)
  6. Platform Security (networking, authentication, secrets management)
  7. Monitoring & Performance (metrics, logging, optimization)

**Ordering Strategy**:
- TDD order: Contract tests before implementation for each service
- Dependency order: Core services → Model integration → Agent layer → RAG → Security
- Infrastructure tasks first: Environment setup, containerization, basic health checks
- Progressive integration: Each service validates independently before inter-service communication
- Mark [P] for parallel execution (independent services: model, RAG, agent APIs)

**Estimated Output**: 35-40 numbered, ordered tasks across 7 phases in tasks.md
- Phase 1: 8 tasks (environment, containers, basic bot structure)
- Phase 2: 6 tasks (Discord integration, model service interface)
- Phase 3: 5 tasks (LLM deployment, integration testing)
- Phase 4: 6 tasks (LangChain setup, agent tools, conversation management)
- Phase 5: 6 tasks (vector DB, RAG pipeline, knowledge ingestion)
- Phase 6: 4 tasks (networking, security, authentication)
- Phase 7: 4 tasks (monitoring, performance optimization, documentation)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
