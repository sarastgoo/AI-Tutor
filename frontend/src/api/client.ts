const API_BASE = "/api/v1";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// Types
export interface Book {
  id: string;
  title: string;
  language: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  book_id: string;
  mode: string;
  status: string;
  created_at: string;
}

export interface TutorMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
  sources?: { items: unknown[] };
}

export interface Progress {
  sessions: number;
  messages: number;
  speaking_attempts: number;
  exercise_attempts: number;
  unique_lexemes: number;
  due_reviews: number;
}

export interface VocabItem {
  lexeme_id: string;
  lemma: string;
  pos: string;
  occurrence_count: number;
}

// API methods
export const api = {
  books: {
    list: () => request<Book[]>("/books"),
    get: (id: string) => request<Book>(`/books/${id}`),
    create: (title: string) =>
      request<Book>("/books", {
        method: "POST",
        body: JSON.stringify({ title, language: "en" }),
      }),
  },
  tutor: {
    createSession: (book_id: string, mode = "free") =>
      request<Session>("/tutor/sessions", {
        method: "POST",
        body: JSON.stringify({ book_id, mode }),
      }),
    sendMessage: (session_id: string, text: string) =>
      request<{
        user_message_id: string;
        assistant_message_id: string;
        reply: string;
        sources: unknown[];
        elapsed_s: number;
      }>(`/tutor/sessions/${session_id}/messages`, {
        method: "POST",
        body: JSON.stringify({ text }),
      }),
    listMessages: (session_id: string) =>
      request<{ items: TutorMessage[] }>(`/tutor/sessions/${session_id}/messages`),
  },
  vocabulary: {
    list: (book_id: string, limit = 50) =>
      request<{ total_lexemes: number; items: VocabItem[] }>(
        `/books/${book_id}/vocabulary?limit=${limit}`,
      ),
  },
  progress: {
    get: () => request<Progress>("/progress"),
  },
  exports: {
    vocabulary: (book_id: string) =>
      request<{
        filename: string;
        download_url: string;
        total_lexemes: number;
        total_occurrences: number;
      }>(`/books/${book_id}/export/vocabulary`, { method: "POST" }),
  },
};