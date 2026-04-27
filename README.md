# College Eligibility Assist Agent

A production-oriented full-stack application for college admissions guidance.

## Project Structure

- `FRONTEND/`: React + Vite chat UI
- `backend/`: FastAPI backend, agent wiring, database tools, MCP integration, and tests

## Architecture Overview

### Frontend (`FRONTEND`)

- React app with a single-card chat UI
- Markdown/table rendering via `react-markdown` + `remark-gfm`
- Features: Enter-to-send, New Chat reset, light/dark theme toggle

### Backend (`backend`)

- `backend/main.py`: FastAPI entry point (`/api/health`, `/api/chat`)
- `backend/core/config.py`: environment configuration and validation
- `backend/core/agent.py`: LangChain agent construction
- `backend/core/prompt.py`: system prompt and response contract
- `backend/services/db_tools.py`: safe SQL execution and deterministic admissions guidance
- `backend/services/mcp_client.py`: optional MCP client tools
- `backend/mcp_server.py`: MCP server exposing admissions tools

## Setup Instructions

### 1. Clone and prepare env

```bash
git clone <your-repo-url>
cd college_eligibility_assist_agent
copy .env.example .env
```

Fill `.env` values, especially `GROQ_API_KEY` and DB credentials.

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd FRONTEND
npm install
cd ..
```

## Run Instructions (End-to-End)

### Terminal 1: Backend API

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend

```bash
cd FRONTEND
npm i
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`).

## Usage

1. Start a chat and provide marks/exam/course/location details.
2. The assistant asks for missing data step-by-step.
3. Final recommendations include mandatory sections:
   - Eligibility
   - Required Documents
   - Deadlines
   - Step-by-Step Checklist

## Testing and Validation

### Backend unit tests

```bash
pytest -q
```

### Frontend build validation

```bash
cd FRONTEND
npm run build
```

## Error Handling and Edge Cases Covered

- Missing or malformed API key validation
- Empty chat messages validation
- Read-only SQL enforcement (single SELECT only)
- Database exception handling with structured responses
- Required input checks for admissions guidance queries

## Performance Notes

- Backend agent object is cached (`lru_cache`) for reuse across requests
- SQL queries use targeted filtering and bounded result limits
- Frontend avoids unnecessary re-renders and auto-scrolls smoothly

## Git and Maintenance

- Keep `.env` out of commits
- Use feature branches and PRs for changes
- Run `pytest` and frontend build before merging
