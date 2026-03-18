"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const EXAMPLES = [
  "We should ship this feature before doing more user research.",
  "We need a rewrite of our codebase.",
  "We should raise a Series B now.",
  "We need to hire more engineers.",
  "We should move faster.",
];

function DepthIndicator({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: Math.min(count, 12) }).map((_, i) => (
        <div
          key={i}
          className="w-1 rounded-full transition-all duration-500"
          style={{
            height: `${Math.min(4 + i * 2, 20)}px`,
            backgroundColor:
              i < 3
                ? "#444"
                : i < 6
                ? "#666"
                : i < 9
                ? "#aaa"
                : "var(--accent)",
            opacity: i < count ? 1 : 0.15,
          }}
        />
      ))}
      {count > 0 && (
        <span
          className="text-xs ml-1 tabular-nums"
          style={{ color: "var(--muted)" }}
        >
          depth {count}
        </span>
      )}
    </div>
  );
}

function MessageBubble({
  msg,
  isStreaming,
}: {
  msg: Message;
  isStreaming?: boolean;
}) {
  const isBedrock =
    msg.role === "assistant" && msg.content.includes("We've reached bedrock");

  return (
    <div
      className={`flex flex-col gap-1 ${msg.role === "user" ? "items-end" : "items-start"}`}
    >
      <span
        className="text-xs px-1"
        style={{ color: "var(--muted)", fontFamily: "inherit" }}
      >
        {msg.role === "user" ? "you" : "why machine"}
      </span>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isBedrock ? "bedrock pl-5" : ""
        }`}
        style={{
          background:
            msg.role === "user" ? "var(--user-bg)" : "var(--claude-bg)",
          border: `1px solid ${isBedrock ? "var(--accent)" : "var(--border)"}`,
          color: isBedrock ? "var(--accent)" : "var(--text)",
          fontFamily: "inherit",
        }}
      >
        {msg.content}
        {isStreaming && (
          <span
            className="inline-block w-1.5 h-3.5 ml-0.5 align-middle animate-pulse"
            style={{ background: "var(--muted)" }}
          />
        )}
      </div>
    </div>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [started, setStarted] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const whyCount = messages.filter((m) => m.role === "assistant").length;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSubmit = async (e?: FormEvent, overrideInput?: string) => {
    e?.preventDefault();
    const text = (overrideInput ?? input).trim();
    if (!text || loading) return;

    const newMessages: Message[] = [
      ...messages,
      { role: "user", content: text },
    ];
    setMessages(newMessages);
    setInput("");
    setLoading(true);
    setStreamingContent("");
    setStarted(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });

      if (!res.ok) throw new Error("API error");
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        full += decoder.decode(value, { stream: true });
        setStreamingContent(full);
      }

      setMessages([...newMessages, { role: "assistant", content: full }]);
      setStreamingContent("");
    } catch (err) {
      console.error(err);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: "Something went wrong. Please try again.",
        },
      ]);
      setStreamingContent("");
    } finally {
      setLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  const handleReset = () => {
    setMessages([]);
    setInput("");
    setStarted(false);
    setStreamingContent("");
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const bedrockReached =
    messages.length > 0 &&
    messages[messages.length - 1]?.role === "assistant" &&
    messages[messages.length - 1]?.content.includes("We've reached bedrock");

  return (
    <div
      className="flex flex-col"
      style={{ minHeight: "100dvh", background: "var(--bg)" }}
    >
      {/* Header */}
      <header
        className="flex items-center justify-between px-6 py-4 border-b shrink-0"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-3">
          <span
            className="text-lg font-medium tracking-tight"
            style={{ color: "var(--accent)", fontFamily: "inherit" }}
          >
            why machine
          </span>
          <span className="text-xs" style={{ color: "var(--muted)" }}>
            first principles, one why at a time
          </span>
        </div>
        <div className="flex items-center gap-4">
          {started && <DepthIndicator count={whyCount} />}
          {started && (
            <button
              onClick={handleReset}
              className="text-xs px-3 py-1.5 rounded border transition-colors"
              style={{
                color: "var(--muted)",
                borderColor: "var(--border)",
                background: "transparent",
                fontFamily: "inherit",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color =
                  "var(--text)";
                (e.currentTarget as HTMLButtonElement).style.borderColor =
                  "#444";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.color =
                  "var(--muted)";
                (e.currentTarget as HTMLButtonElement).style.borderColor =
                  "var(--border)";
              }}
            >
              reset
            </button>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {!started ? (
          /* Landing state */
          <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
            <div className="w-full max-w-xl flex flex-col gap-8">
              <div className="flex flex-col gap-3">
                <p
                  className="text-3xl font-medium leading-tight"
                  style={{ color: "var(--text)", fontFamily: "inherit" }}
                >
                  State a belief.
                  <br />
                  <span style={{ color: "var(--muted)" }}>
                    I{"'"}ll ask why until we hit bedrock.
                  </span>
                </p>
                <p className="text-sm" style={{ color: "var(--muted)" }}>
                  Inspired by{" "}
                  <a
                    href="https://www.threads.net/@jen_spies"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: "#888", textDecoration: "underline" }}
                  >
                    @jen_spies
                  </a>
                  {": "}
                  &ldquo;But can Claude Code sit in meetings asking &lsquo;why?&rsquo; until
                  we reach an actual first-principles answer?&rdquo;
                </p>
              </div>

              <form
                onSubmit={handleSubmit}
                className="flex flex-col gap-3"
              >
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleTextareaChange}
                  onKeyDown={handleKeyDown}
                  placeholder="e.g. We should rewrite our codebase."
                  rows={2}
                  autoFocus
                  className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-colors leading-relaxed"
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    color: "var(--text)",
                    fontFamily: "inherit",
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = "#444";
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = "var(--border)";
                  }}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="self-end px-5 py-2 rounded-lg text-sm font-medium transition-all"
                  style={{
                    background: input.trim()
                      ? "var(--accent)"
                      : "var(--border)",
                    color: input.trim() ? "#000" : "var(--muted)",
                    fontFamily: "inherit",
                    cursor: input.trim() ? "pointer" : "not-allowed",
                    border: "none",
                  }}
                >
                  begin →
                </button>
              </form>

              <div className="flex flex-col gap-2">
                <p className="text-xs" style={{ color: "var(--muted)" }}>
                  try one of these
                </p>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLES.map((ex) => (
                    <button
                      key={ex}
                      onClick={() => {
                        setInput(ex);
                        textareaRef.current?.focus();
                      }}
                      className="text-xs px-3 py-1.5 rounded border transition-colors text-left"
                      style={{
                        color: "var(--muted)",
                        borderColor: "var(--border)",
                        background: "transparent",
                        fontFamily: "inherit",
                        cursor: "pointer",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLButtonElement).style.color =
                          "var(--text)";
                        (
                          e.currentTarget as HTMLButtonElement
                        ).style.borderColor = "#444";
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLButtonElement).style.color =
                          "var(--muted)";
                        (
                          e.currentTarget as HTMLButtonElement
                        ).style.borderColor = "var(--border)";
                      }}
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Chat state */
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <div className="max-w-xl mx-auto flex flex-col gap-5">
                {messages.map((msg, i) => (
                  <MessageBubble key={i} msg={msg} />
                ))}
                {streamingContent && (
                  <MessageBubble
                    msg={{ role: "assistant", content: streamingContent }}
                    isStreaming
                  />
                )}
                {loading && !streamingContent && (
                  <div
                    className="text-xs flex items-center gap-2"
                    style={{ color: "var(--muted)" }}
                  >
                    <span className="animate-pulse">thinking...</span>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            </div>

            {/* Input */}
            {!bedrockReached && (
              <div
                className="shrink-0 border-t px-6 py-4"
                style={{ borderColor: "var(--border)" }}
              >
                <form
                  onSubmit={handleSubmit}
                  className="max-w-xl mx-auto flex gap-3 items-end"
                >
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={handleTextareaChange}
                    onKeyDown={handleKeyDown}
                    placeholder="answer the question..."
                    rows={1}
                    disabled={loading}
                    className="flex-1 px-4 py-3 rounded-lg text-sm outline-none transition-colors leading-relaxed"
                    style={{
                      background: "var(--surface)",
                      border: "1px solid var(--border)",
                      color: "var(--text)",
                      fontFamily: "inherit",
                      opacity: loading ? 0.5 : 1,
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = "#444";
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = "var(--border)";
                    }}
                  />
                  <button
                    type="submit"
                    disabled={!input.trim() || loading}
                    className="px-4 py-3 rounded-lg text-sm font-medium transition-all shrink-0"
                    style={{
                      background:
                        input.trim() && !loading
                          ? "var(--accent)"
                          : "var(--border)",
                      color:
                        input.trim() && !loading ? "#000" : "var(--muted)",
                      fontFamily: "inherit",
                      cursor:
                        input.trim() && !loading ? "pointer" : "not-allowed",
                      border: "none",
                    }}
                  >
                    →
                  </button>
                </form>
              </div>
            )}

            {bedrockReached && (
              <div
                className="shrink-0 border-t px-6 py-5"
                style={{ borderColor: "var(--border)" }}
              >
                <div className="max-w-xl mx-auto flex items-center justify-between">
                  <p className="text-xs" style={{ color: "var(--muted)" }}>
                    bedrock reached after {whyCount} question
                    {whyCount !== 1 ? "s" : ""}
                  </p>
                  <button
                    onClick={handleReset}
                    className="text-sm px-5 py-2 rounded-lg font-medium"
                    style={{
                      background: "var(--accent)",
                      color: "#000",
                      fontFamily: "inherit",
                      border: "none",
                      cursor: "pointer",
                    }}
                  >
                    dig again →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
