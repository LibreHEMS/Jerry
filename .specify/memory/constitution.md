<!--
Sync Impact Report:
Version change: initial → 1.0.0
Modified principles: N/A (initial creation)
Added sections: Core Principles (7 principles), Technical Standards, Development Practices, Governance
Removed sections: N/A
Templates requiring updates:
✅ .specify/templates/plan-template.md - Updated constitution check gates
✅ .specify/templates/spec-template.md - Aligned with persona and mission requirements
✅ .specify/templates/tasks-template.md - Aligned with technical principles and tooling
Follow-up TODOs: None
-->

# Jerry Self-Hosted AI Constitution

## Core Principles

### I. Persona Preservation (NON-NEGOTIABLE)
Jerry MUST remain "Jerry Hems," the seasoned, grandfatherly AI advisor specializing in Australian renewable energy and home automation. His persona—knowledgeable, patient, practical, and warm—is paramount and must be preserved in all interactions. No feature or change may compromise this core identity.

**Rationale**: The persona is the foundational value proposition and user experience differentiator.

### II. Self-Hosted & Sovereign
The entire platform MUST be designed to be fully self-hosted, giving the operator complete control over data and infrastructure. No essential functionality may depend on external proprietary services.

**Rationale**: Ensures user data sovereignty, operational independence, and alignment with open-source values.

### III. Open-Source First
All components, from the language model to the vector database and supporting libraries, MUST be open-source and community-supported. When functionality is equivalent, open-source solutions take precedence over proprietary alternatives.

**Rationale**: Promotes transparency, community contribution, long-term sustainability, and avoids vendor lock-in.

### IV. Container-Native Architecture
The application MUST be architected as a set of collaborating services running in containers, orchestrated by Podman. Each service must be independently deployable, scalable, and maintainable.

**Rationale**: Ensures portability, scalability, ease of deployment, and modern DevOps practices.

### V. Security by Design
Security MUST be a foundational requirement, not an afterthought. This includes secure communication between services, proper credential management, and adherence to container security best practices. All external-facing endpoints MUST be protected.

**Rationale**: Protects user data, maintains system integrity, and ensures compliance with privacy expectations.

### VI. Test-Driven Development (NON-NEGOTIABLE)
All code MUST be fully tested to ensure reliability and prevent regressions. Tests must be written before implementation, following the Red-Green-Refactor cycle strictly.

**Rationale**: Ensures system reliability, maintainability, and confidence in deployments.

### VII. Simplicity & Readability
The codebase MUST be simple, well-documented, and easy for new contributors to understand. Complexity must be avoided unless absolutely necessary and thoroughly justified.

**Rationale**: Promotes maintainability, community contribution, and reduces technical debt.

## Technical Standards

**Modern Tooling**: The project MUST leverage modern, high-performance tools including `uv` for Python package management and `ruff` for code linting and formatting to ensure clean, maintainable, and efficient development.

**Agentic Architecture**: Jerry MUST evolve from a simple chatbot into an agentic system using LangChain to manage complex conversational flows and securely use tools for web research, enhancing advice depth and accuracy.

**Efficient Context Management**: The system MUST implement multi-tiered memory architecture including progressive summarization, vector-based memory retrieval, fixed-window recent memory, and query condensation to handle long conversations efficiently.

**Semantic Caching**: Conversation-level caching MUST be implemented to improve response times and reduce computational overhead through near-identical query recognition, semantic similarity detection, and intelligent cache invalidation.

**Ethical Tool Use**: All external tools, especially web searching capabilities, MUST be used ethically and securely, respecting user privacy and data ownership.

## Development Practices

**Knowledge Organization**: Jerry's knowledge base MUST be structured hierarchically with core competencies in Australian energy systems, home automation, and renewable technologies. All resources must be ethically sourced from open documentation, prioritizing quality over quantity.

**Data Privacy**: User conversations MUST be treated with strict confidentiality, stored securely, and only used for system improvement with explicit consent.

**Australian Context**: All advice, examples, and recommendations MUST be meticulously tailored to the Australian context including standards, climate, market conditions, and typical home setups.

**Mission Alignment**: Every feature MUST serve the core mission to empower Australian homeowners to make informed decisions about renewable energy and smart home technology through practical, personalized advice.

## Governance

This constitution supersedes all other development practices and standards. All code reviews, feature implementations, and architectural decisions MUST verify compliance with these principles. 

Amendments require:
1. Documentation of the proposed change and rationale
2. Impact assessment on existing features and architecture
3. Community discussion and approval process
4. Migration plan for any breaking changes

Complexity must be justified against the Simplicity & Readability principle with clear documentation of necessity and alternative approaches considered.

**Version**: 1.0.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-06