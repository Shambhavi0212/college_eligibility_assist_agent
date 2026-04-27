from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

try:
    from backend.core.agent import get_agent
except ModuleNotFoundError:
    from core.agent import get_agent


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    answer: str


app = FastAPI(title="College Eligibility Assistant API", version="2.0.0")

MAX_CHAT_MESSAGES = 8
MAX_MESSAGE_CHARS = 2000

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


def _build_history(messages: List[ChatMessage]):
    trimmed_messages = messages[-MAX_CHAT_MESSAGES:]
    history = []

    for message in trimmed_messages:
        content = message.content.strip()
        if len(content) > MAX_MESSAGE_CHARS:
            content = content[:MAX_MESSAGE_CHARS]

        history.append(HumanMessage(content=content) if message.role == "user" else AIMessage(content=content))

    return history


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    history = _build_history(request.messages)

    try:
        response = get_agent().invoke({"messages": history})
        answer = response["messages"][-1].content
        return ChatResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {exc}") from exc
