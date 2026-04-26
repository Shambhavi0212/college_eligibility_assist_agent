import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const assistantWelcome = {
  role: "assistant",
  content:
    "Hi, I am your admissions assistant. Share your marks, stream, exam, and preferred course/location, and I will guide you.",
};

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
  const [messages, setMessages] = useState([assistantWelcome]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) {
      return;
    }

    setError("");
    const nextMessages = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages: nextMessages }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const detail = payload?.detail || `HTTP ${response.status}`;
        throw new Error(detail);
      }

      const payload = await response.json();
      const answer = payload?.answer || "No response from assistant.";
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (err) {
      setError(err.message || "Unable to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (event) => {
    event.preventDefault();
    sendMessage();
  };

  const onInputKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    if (loading) {
      return;
    }
    setMessages([assistantWelcome]);
    setInput("");
    setError("");
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <div className="page">
      <main className="app-card">
        <header className="card-header">
          <div>
            <h1>College Eligibility Assistant</h1>
            <p>Ask about eligibility, documents, deadlines, and admission checklists.</p>
          </div>
          <div className="header-actions">
            <button type="button" className="theme-btn" onClick={toggleTheme}>
              {theme === "light" ? "Dark Mode" : "Light Mode"}
            </button>
            <span className="status-pill">Online</span>
          </div>
        </header>

        <section className="messages" aria-live="polite">
          {messages.map((message, index) => (
            <article key={`${message.role}-${index}`} className={`bubble ${message.role}`}>
              <p className="role-label">{message.role === "assistant" ? "Assistant" : "You"}</p>
              {message.role === "assistant" ? (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
            </article>
          ))}

          {loading ? <article className="bubble assistant pending">Thinking...</article> : null}
          <div ref={messagesEndRef} />
        </section>

        <form className="composer" onSubmit={onSubmit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={onInputKeyDown}
            placeholder="Try: best CSE colleges in Chennai under 2 lakh fee"
            rows={2}
          />

          <div className="composer-actions">
            <button type="submit" disabled={!canSend}>
              Send
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={startNewChat}
              disabled={loading}
            >
              New Chat
            </button>
          </div>
        </form>

        {error ? <p className="error">{error}</p> : null}
      </main>
    </div>
  );
}

export default App;
