# AGENTS.md

## Project intent
This repository is the MVP foundation for an AI comic-drama production pipeline.
This version is Coze-first, not n8n-first.
The goal is to create a lightweight internal production system for early-stage workflow validation.

## Priorities
1. Simplicity over completeness
2. Coze integration over complex orchestration
3. Reliability over fancy architecture
4. Mockable provider interfaces over hard-coded vendor logic
5. Documentation over premature optimization

## MVP scope
This phase only covers:
- project setup
- character setup
- storyboard/shot management
- asset task generation
- publishing records
- Coze integration endpoints

This phase does NOT require:
- retrospective module
- full frontend
- multi-tenant SaaS
- real paid provider dependency

## Architecture rules
- Keep provider integrations abstracted behind interfaces.
- Keep business logic in services, not in API routes.
- Keep state transitions explicit and validated.
- Prefer simple REST APIs.
- Default local development must work without paid external services.

## Review guidelines
- Flag missing tests for stateful logic.
- Flag hidden state transitions.
- Flag hard-coded secrets or API keys.
- Flag unnecessary complexity for MVP.

## Documentation requirements
Any feature that changes behavior must update:
- README.md
- docs/API.md
- docs/DATA_MODEL.md
- docs/STATUS_MACHINE.md

## Testing requirements
At minimum, test:
- project creation
- shot creation
- asset task creation
- Coze integration endpoints
- retry limit behavior
- dashboard summary

## Non-goals
- No retrospective module in phase 1
- No n8n-specific workflow in phase 1
- No complex admin frontend
