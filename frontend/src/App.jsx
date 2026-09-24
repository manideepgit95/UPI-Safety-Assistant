import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const [scenario, setScenario] = useState("");
  const [scenarioResult, setScenarioResult] = useState(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);

  const askAssistant = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    const userMessage = {
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((previous) => [...previous, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    question: trimmedQuestion,
    history: messages.map((message) => ({
      role: message.role,
      content: message.content,
    })),
  }),
});

      if (!response.ok) {
        throw new Error("Unable to connect to the assistant.");
      }

      const data = await response.json();

      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
        safety: data.safety || null,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "I couldn't connect to the UPI Safety Assistant. Please make sure the FastAPI backend is running.",
          sources: [],
          safety: null,
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeScenario = async () => {
    const trimmedScenario = scenario.trim();

    if (!trimmedScenario || scenarioLoading) {
      return;
    }

    setScenarioLoading(true);
    setScenarioResult(null);

    try {
      const response = await fetch(
        `${API_URL}/analyze-scenario`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: trimmedScenario,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to analyze the scenario.");
      }

      const data = await response.json();

      setScenarioResult(data.analysis);
    } catch (error) {
      setScenarioResult({
        level: "error",
        label: "Analysis Unavailable",
        icon: "⚠️",
        indicators: [
          "Unable to connect to the scenario analyzer. Please make sure the FastAPI backend is running.",
        ],
      });
    } finally {
      setScenarioLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askAssistant();
    }
  };

  const suggestedQuestions = [
    "Should I enter my UPI PIN to receive money?",
    "Is it safe to scan an unknown QR code?",
    "What should I do if I sent money to a scammer?",
  ];

  return (
    <div className="app">
      <div className="background-glow glow-one"></div>
      <div className="background-glow glow-two"></div>

      <header className="header">
        <div className="brand">
          <div className="brand-icon">🛡️</div>

          <div>
            <h1>UPI Safety Assistant</h1>
            <p>AI-powered digital payment safety</p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Trusted AI
        </div>
      </header>

      <main className="main">

        {/* WELCOME SCREEN */}
        {messages.length === 0 ? (
          <section className="welcome">
            <div className="hero-icon">🛡️</div>

            <div className="badge">
              <span>✦</span>
              RAG-powered safety assistant
            </div>

            <h2>
              Stay safe with
              <span> smarter UPI guidance.</span>
            </h2>

            <p className="hero-text">
              Ask questions about UPI payments, suspicious QR codes,
              payment requests, scams, and digital payment safety.
            </p>

            <div className="suggestions">
              {suggestedQuestions.map((item) => (
                <button
                  key={item}
                  className="suggestion-card"
                  onClick={() => setQuestion(item)}
                >
                  <span className="suggestion-icon">→</span>
                  <span>{item}</span>
                </button>
              ))}
            </div>
          </section>
        ) : (

          /* CHAT AREA */
          <section className="chat-area">

            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-row ${message.role}`}
              >
                <div className="message-avatar">
                  {message.role === "user" ? "👤" : "🛡️"}
                </div>

                <div className="message-content">

                  <div className="message-label">
                    {message.role === "user"
                      ? "You"
                      : "UPI Safety Assistant"}
                  </div>

                  {/* SAFETY LEVEL */}
                  {message.safety && (
                    <div
                      className={`safety-badge ${message.safety.level}`}
                    >
                      <span>{message.safety.icon}</span>
                      <span>{message.safety.label}</span>
                    </div>
                  )}

                  {/* ANSWER */}
                  <div
                    className={`message-bubble ${
                      message.error ? "error-message" : ""
                    }`}
                  >
                    {message.content}
                  </div>

                  {/* TRUSTED SOURCES */}
                  {message.sources &&
                    message.sources.length > 0 && (
                      <div className="sources">

                        <div className="sources-title">
                          📚 Trusted Sources
                        </div>

                        <div className="source-list">

                          {message.sources.map(
                            (source, sourceIndex) => (
                              <div
                                className="source-card"
                                key={`${source.chunk_id}-${sourceIndex}`}
                              >

                                <div className="source-number">
                                  {sourceIndex + 1}
                                </div>

                                <div className="source-details">

                                  <div className="source-organization">
                                    🏛️ {source.organization}
                                  </div>

                                  <strong className="source-title">
                                    {source.title}
                                  </strong>

                                  <div className="source-meta">

                                    <span className="source-trust">
                                      ✓ {source.trust_level}
                                    </span>

                                    {source.url && (
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="source-link"
                                      >
                                        View official source ↗
                                      </a>
                                    )}

                                  </div>

                                </div>

                              </div>
                            )
                          )}

                        </div>

                      </div>
                    )}

                </div>
              </div>
            ))}

            {/* LOADING INDICATOR */}
            {loading && (
              <div className="message-row assistant">

                <div className="message-avatar">
                  🛡️
                </div>

                <div className="message-content">

                  <div className="message-label">
                    UPI Safety Assistant
                  </div>

                  <div className="message-bubble loading-bubble">

                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>

                    <span className="thinking-text">
                      Checking trusted sources...
                    </span>

                  </div>

                </div>

              </div>
            )}

          </section>
        )}

        {/* SCAM SCENARIO ANALYZER */}
        <section className="scenario-section">

          <div className="scenario-header">

            <div className="scenario-icon">
              🚨
            </div>

            <div>
              <h3>Scam Scenario Analyzer</h3>

              <p>
                Describe a suspicious UPI situation and check
                for common warning signs.
              </p>
            </div>

          </div>

          <div className="scenario-input-wrapper">

            <textarea
              value={scenario}
              onChange={(event) =>
                setScenario(event.target.value)
              }
              placeholder="Example: Someone called me and asked me to scan a QR code to receive a refund..."
              rows="4"
              disabled={scenarioLoading}
            />

            <button
              className="scenario-button"
              onClick={analyzeScenario}
              disabled={
                !scenario.trim() || scenarioLoading
              }
            >
              {scenarioLoading
                ? "Analyzing..."
                : "Analyze Scenario"}
            </button>

          </div>

          {/* SCENARIO RESULT */}
          {scenarioResult && (
            <div className="scenario-result">

              <div
                className={`scenario-result-badge ${scenarioResult.level}`}
              >
                <span>
                  {scenarioResult.icon}
                </span>

                <span>
                  {scenarioResult.label}
                </span>
              </div>

              {scenarioResult.indicators &&
                scenarioResult.indicators.length > 0 && (
                  <div className="scenario-indicators">

                    <div className="scenario-result-title">
                      ⚠️ Warning Indicators
                    </div>

                    {scenarioResult.indicators.map(
                      (indicator, index) => (
                        <div
                          className="indicator-item"
                          key={index}
                        >
                          <span>•</span>

                          <span>
                            {indicator}
                          </span>
                        </div>
                      )
                    )}

                  </div>
                )}

            </div>
          )}

        </section>

        {/* MESSAGE COMPOSER */}
        <section className="composer">

          <div className="input-wrapper">

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask about UPI safety..."
              rows="1"
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={askAssistant}
              disabled={
                !question.trim() || loading
              }
              aria-label="Send question"
            >
              ➤
            </button>

          </div>

          <div className="composer-footer">

            <span>
              🔒 Answers are grounded in trusted safety sources
            </span>

            <span>
              Enter to send
            </span>

          </div>

        </section>

      </main>

      <footer className="footer">

        <span>
          🛡️ UPI Safety Assistant
        </span>

        <span>
          Built with RAG + FastAPI + React
        </span>

      </footer>

    </div>
  );
}

export default App;