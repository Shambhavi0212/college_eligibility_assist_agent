# College Eligibility Assist Agent: Complete Technical Guide

## 1. Project Goal

This project is a full-stack college admissions assistant designed to:

- Ask students for missing profile details step-by-step
- Evaluate eligibility against structured admission criteria
- Provide deadline and document-aware guidance
- Return deterministic recommendation data from MySQL
- Present results in a user-friendly React chat interface

The architecture intentionally avoids one-file shortcuts and uses a clean split between frontend and backend.

## 2. Where Everything Is Created and Why

## Root Level

- [README.md](README.md)
Purpose: Quick start, setup, run, and testing instructions.

- [.env.example](.env.example)
Purpose: Standardized environment template for API key, DB config, and MCP options.

- [requirements.txt](requirements.txt)
Purpose: Python dependency manifest for backend runtime and testing.

- [PROJECT_DETAILED_GUIDE.md](PROJECT_DETAILED_GUIDE.md)
Purpose: This detailed architecture and design rationale document.

## Frontend

- [FRONTEND/package.json](FRONTEND/package.json)
Purpose: React/Vite dependency and script definitions.

- [FRONTEND/src/App.jsx](FRONTEND/src/App.jsx)
Purpose: Main chat UI logic (message state, send flow, theme toggle, new chat).

- [FRONTEND/src/styles.css](FRONTEND/src/styles.css)
Purpose: Single-card UI styling, theme variables, transitions, responsive behavior.

## Backend

- [backend/main.py](backend/main.py)
Purpose: FastAPI entrypoint and HTTP routes.

- [backend/core/config.py](backend/core/config.py)
Purpose: Centralized environment settings and validation.

- [backend/core/prompt.py](backend/core/prompt.py)
Purpose: System prompt and behavioral contract for the agent.

- [backend/core/agent.py](backend/core/agent.py)
Purpose: LLM + tools assembly with fallback strategy (LangChain direct tools or MCP tools).

- [backend/services/db_tools.py](backend/services/db_tools.py)
Purpose: DB safety layer, deterministic eligibility query logic, structured result shaping.

- [backend/services/mcp_client.py](backend/services/mcp_client.py)
Purpose: MCP client wrapper exposed as LangChain-compatible tools.

- [backend/mcp_server.py](backend/mcp_server.py)
Purpose: MCP server exposing safe SQL and admissions guidance tools.

- [backend/tests/test_db_tools.py](backend/tests/test_db_tools.py)
Purpose: Basic validation tests for SQL safety and required input checks.

## 3. Backend Architecture Deep Dive

### 3.1 API Layer

The API layer in [backend/main.py](backend/main.py) is responsible for:

- Request validation via Pydantic models
- CORS setup for frontend calls
- Converting chat history into LangChain message objects
- Returning final assistant output as API response

Snippet:

~~~python
@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
~~~

Why used:

- Prevents empty conversation calls
- Keeps API contract explicit and testable
- Protects downstream agent execution from malformed input

### 3.2 Configuration Layer

In [backend/core/config.py](backend/core/config.py), all environment-driven settings are centralized in a frozen dataclass.

Snippet:

~~~python
@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    use_mcp: bool = _env_bool("USE_MCP", True)
    db_host: str = os.getenv("DB_HOST", "localhost").strip()
~~~

Why used:

- Single source of truth for runtime behavior
- Avoids hardcoded credentials and magic constants
- Improves maintainability and portability across environments

### 3.3 Agent Layer

In [backend/core/agent.py](backend/core/agent.py), the app builds one cached agent instance and dynamically chooses tools.

Snippet:

~~~python
if settings.use_mcp and mcp_sql_executor and mcp_admissions_guidance:
    tools = [mcp_sql_executor, mcp_admissions_guidance]
else:
    tools = [sql_executor, admissions_guidance]
~~~

Why used:

- Supports both direct and MCP execution paths
- Keeps production robust if MCP is unavailable
- Reduces startup and per-request overhead by caching agent object

### 3.4 Deterministic Data Service Layer

The deterministic admissions logic is in [backend/services/db_tools.py](backend/services/db_tools.py).

Safety snippet:

~~~python
def is_safe_select(sql_query: str) -> bool:
    if not sql_lower.startswith("select"):
        return False
    if FORBIDDEN_SQL_PATTERN.search(sql_lower):
        return False
    if ";" in sql[:-1]:
        return False
    return True
~~~

Why used:

- Enforces read-only SQL behavior
- Blocks dangerous mutation and stacked statements
- Reduces injection and accidental destructive query risk

Deterministic query snippet:

~~~python
WHERE cr.course_name LIKE %s
  AND ec.min_10th_pct <= %s
  AND ec.min_12th_pct <= %s
  AND LOWER(ec.required_stream) LIKE %s
  AND LOWER(ec.accepted_exams) LIKE %s
~~~

Why used:

- Uses objective eligibility constraints from schema
- Guarantees repeatable filtering behavior
- Aligns result set with user profile instead of probabilistic retrieval

## 4. MCP Integration Layer

### 4.1 MCP Server

[backend/mcp_server.py](backend/mcp_server.py) exposes tools via FastMCP:

- execute_select
- admissions_guidance

Purpose:

- Standard tool protocol endpoint
- Can be consumed by any compliant MCP client
- Decouples tool execution from agent orchestration

### 4.2 MCP Client

[backend/services/mcp_client.py](backend/services/mcp_client.py) wraps MCP tool calls and exposes LangChain tool decorators.

Purpose:

- Lets the same agent code switch from local tools to MCP tools transparently
- Preserves tool signatures for LangChain compatibility
- Enables future externalization of tool execution

## 5. Frontend Architecture Deep Dive

Primary UI logic is in [FRONTEND/src/App.jsx](FRONTEND/src/App.jsx).

Responsibilities:

- Message state
- Enter-to-send behavior
- New chat reset
- Theme toggle persistence
- Error display for failed backend requests

Snippet:

~~~javascript
const response = await fetch(`${API_BASE_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ messages: nextMessages }),
});
~~~

Why used:

- Clean separation: frontend handles interaction, backend handles intelligence
- Explicit API contract supports easier testing and debugging

Markdown rendering:

- Assistant output supports bold sections and tables through markdown renderer
- This is important because backend prompt enforces formatted outputs

## 6. Full End-to-End Workflow

1. User opens frontend and types query.
2. Frontend appends user message to local chat state.
3. Frontend sends full message history to backend API route /api/chat.
4. Backend validates payload and converts role/content into LangChain message objects.
5. Backend gets cached agent.
6. Agent evaluates context and chooses next action:
   - Ask follow-up question if data is missing
   - Call admissions tool when data is sufficient
7. Tool layer runs safe SQL and fetches eligible results from MySQL.
8. Service layer builds structured response with:
   - Eligibility
   - Required documents
   - Deadlines
   - Checklist
9. Agent converts tool output into natural conversational markdown response.
10. Backend returns answer text to frontend.
11. Frontend renders answer in chat and formats markdown tables/bold sections.

## 7. Why Hybrid LangChain + MCP

The project uses a hybrid model because each component solves a different concern:

- LangChain: agent orchestration, reasoning loop, tool selection, conversation flow
- MCP: standard protocol for tool execution and tool interoperability

Why not only LangChain:

- Pure local tool coupling makes portability harder
- Harder to expose tools across different agents/frameworks in a standard way

Why not only MCP:

- MCP provides tool transport/protocol, not full conversational orchestration
- You still need an agent runtime for memory/context/tool decision logic

Hybrid benefit:

- Best of both: strong reasoning + standardized tool interface
- Incremental migration path between local and remote tool execution

## 8. Why Not RAG for This Use Case

RAG is excellent for unstructured document search, but core requirements here are deterministic and transactional.

Potential problems with RAG for this project:

- Eligibility and cutoffs are structured constraints, not semantic similarity tasks
- Deadlines require exact date fields, not approximate retrieval
- Document and checklist sections need repeatable completeness
- Hallucination risk increases when retrieval chunks are noisy or stale
- Auditability is weaker when outputs come from probabilistic chunk selection

RAG can still be added later for secondary features:

- FAQ explanations
- Brochure policy interpretation
- Rich contextual guidance from PDFs

But core eligibility decisions should remain SQL-driven.

## 9. Why SQL Was Used

SQL is the correct primary data access method because:

- Data is relational and structured
- Constraints (marks, ranks, streams, fees, locations) map directly to query filters
- Deadlines and docs are table fields requiring exact retrieval
- Query behavior is deterministic and auditable
- Indexed filtering can be efficient for production workloads

This makes SQL the strongest choice for correctness and production reliability in this domain.

## 10. Error Handling and Edge Cases

Implemented examples:

- Missing API key validation in config
- Malformed key format validation
- Empty messages rejected at API layer
- Non-SELECT and stacked SQL statements blocked
- Database connector exceptions converted into structured error responses
- Missing required inputs rejected in admissions guidance tool
- MCP unavailable fallback to direct tool mode

## 11. Testing and Validation

Current tests in [backend/tests/test_db_tools.py](backend/tests/test_db_tools.py):

- Safe select passes valid read query
- Mutation query blocked
- Stacked query blocked
- Required input validation enforced

Recommended additions for stronger coverage:

- API route tests for /api/chat and /api/health
- Mocked DB integration tests for admissions query mapping
- Frontend interaction tests for Enter send and New Chat reset
- Snapshot tests for markdown table rendering

## 12. Performance and Efficiency Notes

- Agent object is cached to avoid repeated expensive initialization
- SQL query includes bounded result limit
- Frontend reuses in-memory chat state and avoids heavy re-renders
- Structured data selection avoids costly vector retrieval pipelines for deterministic fields

## 13. Maintainability and Separation of Concerns

This codebase uses clear boundaries:

- API transport and validation in main
- Configuration in core config
- LLM orchestration in core agent
- Tool logic in services
- Protocol adapters in MCP modules
- UI behavior in frontend app
- Tests in backend tests folder

This separation is why future changes remain manageable.

## 14. Runbook

Backend:

- uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Frontend:

- cd FRONTEND
- npm run dev

Tests:

- python -m pytest -q

## 15. Final Design Summary

This implementation is intentionally SQL-first and deterministic for critical admissions outcomes, while still using LLM reasoning for conversational experience. The Hybrid LangChain + MCP approach gives flexibility and standards compliance without sacrificing practical reliability.
