# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lynxe is a Java implementation of Manus (multi-agent collaboration system) built with Spring AI Alibaba and Spring Boot 3.5.6. It provides an AI Agent Management System with Func-Agent mode for precise execution control, MCP (Model Context Protocol) integration, and HTTP service invocation capabilities.

**Version**: 4.10.7 | **Port**: 18080

## Development Commands

### Backend (Java/Maven)
```bash
# Start the application (default: H2 database)
mvn spring-boot:run

# Build JAR
mvn clean package

# Run tests (currently skipped in config, use mvn test -DskipTests=false)
mvn test

# Apply code formatting (Spotless + Spring Java Format)
mvn spotless:apply
```

### Frontend (Vue.js + Vite)
```bash
cd ui-vue3

# Development server
pnpm dev

# Build for production
pnpm build

# Type checking
pnpm type-check

# Linting and formatting
pnpm lint          # ESLint with auto-fix
pnpm format        # Prettier formatting
pnpm refactor:fix  # Run both lint and format

# Testing
pnpm test:unit     # Vitest unit tests
pnpm test:e2e      # Cypress E2E tests
```

### Database Profiles
- **Default**: `h2` (file-based in `./h2-data/`)
- **MySQL**: Activate with `-Dspring.profiles.active=mysql`
- **PostgreSQL**: Activate with `-Dspring.profiles.active=postgres`

Configuration files in `src/main/resources/`: `application-mysql.yml`, `application-postgres.yml`

## Architecture Overview

### Backend Structure (`src/main/java/com/alibaba/cloud/ai/lynxe/`)

| Directory | Purpose |
|-----------|---------|
| `config/` | Spring Boot configuration and startup |
| `controller/` | REST API endpoints (`LynxeController`, `PlanTemplateController`, `ConfigController`) |
| `service/` | Business logic layer |
| `entity/` | JPA entities and data models |
| `llm/` | LLM integration (OpenAI, Spring AI) |
| `agent/` | Agent management and execution |
| `planning/` | Plan template generation and execution |
| `tool/` | Tool definitions and registry |
| `mcp/` | Model Context Protocol implementation |
| `runtime/` | Runtime controllers for execution tracking |
| `workspace/` | Workspace and conversation management |
| `recorder/` | Execution recording (`PlanExecutionRecord`, `AgentExecutionRecord`) |

### Frontend Structure (`ui-vue3/src/`)

| Directory | Purpose |
|-----------|---------|
| `api/` | API client interfaces |
| `components/` | Vue components (chat, sidebar, modals) |
| `views/` | Page-level components |
| `router/` | Vue Router configuration |
| `stores/` | Pinia state management |
| `composables/` | Vue composables for reusable logic |
| `types/` | TypeScript type definitions |
| `base/` | Base configurations (i18n) |

### Data Flow Architecture

```
User Action → Component → Store (Pinia) → API Layer → Backend Controller → Service → Agent/LLM
```

**Key Data Entities:**
- `PlanExecutionRecord`: Core execution tracking with `agentExecutionSequence`
- `AgentExecutionRecord`: Individual agent execution details
- `Dialog` + `Message`: Conversational data structure
- `PlanTemplate`: Reusable agent plans

**Important**: Frontend data design follows domain ownership pattern (see `design.md`). Stores own data; composables orchestrate.

## Key API Endpoints

### Execution APIs (`LynxeController`)

**Async Execution** (recommended):
```
POST /api/executor/executeByToolNameAsync
```
Request: `{ toolName, serviceGroup, replacementParams?, uploadedFiles?, uploadKey?, conversationId? }`
Response: `{ planId, status, conversationId, toolName, planTemplateId }`

**Sync Execution**:
```
POST /api/executor/executeByToolNameSync
```

**Get Execution Details**:
```
GET /api/executor/details/{planId}
```
Returns: `PlanExecutionRecord` with nested execution tree

**Get Step Details**:
```
GET /api/executor/agent-execution/{stepId}
```
Returns: `AgentExecutionRecord` with think-act records

### Plan Template APIs (`PlanTemplateController`)
- `POST /api/plan-template/generate` - Generate new plan
- `POST /api/plan-template/executePlanByTemplateId` - Execute by template
- `GET /api/plan-template/list` - List all templates
- `POST /api/plan-template/save` - Save plan version
- `POST /api/plan-template/update` - Update template

### Config APIs (`ConfigController`)
- `GET /api/config/group/{groupName}` - Get config by group
- `POST /api/config/batch-update` - Batch update configs

### File Upload
```
POST /api/file-upload/upload
```
FormData with `files` field → Returns `{ uploadKey, uploadedFiles[] }`

## Important Workflows

### Func-Agent Creation and Execution
1. Create Func-Agent (plan template) via UI or API
2. Publish as tool (Internal Method Call or HTTP Service)
3. Execute via `executeByToolNameAsync` or `executeByToolNameSync`
4. Track progress via `/api/executor/details/{planId}` polling

See `ui-vue3/src/components/sidebar/ExecutionController.vue` and `ui-vue3/src/composables/usePlanExecution.ts` for reference.

### File Upload with Execution
1. Upload files via `/api/file-upload/upload` → get `uploadKey` + `uploadedFiles[]`
2. Call execute endpoint with both `uploadKey` and `uploadedFiles` parameters
3. Backend syncs files to plan directory via `syncUploadedFilesToPlan()`
4. Agents can access files; LLM sees filenames in `stepRequirement`

### Polling Execution Status
Frontend polls `/api/executor/details/{planId}` every 1 second (default). Response includes:
- `status`: pending/running/completed/failed
- `agentExecutionSequence[]`: Step-by-step execution
- `userInputWaitState`: If waiting for user input
- `subPlanExecutionRecords[]`: Nested sub-plans

## Key Dependencies

**Backend:**
- Spring Boot 3.5.6, Spring AI 1.1.2
- Spring WebFlux (for MCP reactive streams)
- Playwright 1.55.0 (browser automation)
- Apache POI 5.4.1, EasyExcel 3.1.5 (document processing)
- MCP SDK 0.16.0

**Frontend:**
- Vue 3, TypeScript, Vite
- Ant Design Vue 4
- Pinia (state management)
- Monaco Editor (code editing)

## Code Quality

**Java:**
- Spring Java Format Maven Plugin (line length: 120)
- Spotless (removes unused imports)
- Maven Compiler Plugin with `-parameters` flag

**Frontend:**
- ESLint + Prettier
- `pnpm refactor:check` validates both types and linting
- Vue I18n for internationalization

## Testing

- **Backend**: JUnit 5 + Mockito (tests currently skipped in config)
- **Frontend**: Vitest (unit), Cypress (E2E)

## Configuration

Application properties in `src/main/resources/application.yml`. Key configs:
- `spring.profiles.active`: Database profile (h2/mysql/postgres)
- Server runs on port 18080
- H2 console available at `/h2-console`

For production database setup, configure `application-mysql.yml` or `application-postgres.yml` and activate the profile.
