# FRONTEND (React UI)

This folder contains a React + Vite chat UI for the college eligibility assistant.

## Features

- Chat interface for user interaction
- Markdown rendering for assistant responses
- Proper support for bold text like `**text**`
- GitHub-Flavored Markdown table rendering

## Run Instructions

1. Start backend API from project root:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

2. In this `FRONTEND` folder, install dependencies and run dev server:

```bash
npm install
npm run dev
```

3. Open the URL shown by Vite (usually `http://localhost:5173`).

## Environment

Create `.env` inside this folder (or copy `.env.example`) and set:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## If npm fails on Windows

If you see npm module path errors, reinstall Node.js LTS and reopen terminal. Then run:

```bash
node -v
npm -v
npm install
```
