import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type TutorMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
}

export default function Tutor() {
  const [params] = useSearchParams();
  const bookId = params.get("book");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!bookId) return;
    api.tutor
      .createSession(bookId, "free")
      .then((s) => setSessionId(s.id))
      .catch((e) => setError(e.message));
  }, [bookId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!sessionId || !input.trim() || sending) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    setError(null);
    try {
      const resp = await api.tutor.sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: resp.reply }]);
    } catch (e) {
      setError((e as Error).message);
      setMessages((prev) => [...prev, { role: "assistant", content: "(Failed to get response)" }]);
    } finally {
      setSending(false);
    }
  }

  if (!bookId) {
    return <p>No book selected. Go to <a href="/" className="underline">Library</a>.</p>;
  }
  if (!sessionId) return <p>Starting session...</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Tutor</h1>
      <Card>
        <CardContent className="p-4 h-[500px] overflow-y-auto space-y-3">
          {messages.length === 0 && (
            <p className="text-muted-foreground text-center">Ask anything about the book!</p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 ${
                  m.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{m.content}</p>
              </div>
            </div>
          ))}
          {sending && <p className="text-sm text-muted-foreground">Tutor is thinking...</p>}
          <div ref={endRef} />
        </CardContent>
      </Card>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask a question..."
          className="flex-1 border rounded-md px-3 py-2"
          disabled={sending}
        />
        <Button onClick={handleSend} disabled={sending || !input.trim()}>
          Send
        </Button>
      </div>
    </div>
  );
}