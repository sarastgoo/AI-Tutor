import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

type RecordingState = "idle" | "recording" | "processing" | "done";

interface SpeakingResult {
  id: string;
  transcript: string;
  feedback_text: string;
  reply_audio_url: string | null;
  pronunciation_status: string;
}

export default function Speaking() {
  const [params] = useSearchParams();
  const bookId = params.get("book");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<RecordingState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SpeakingResult | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!bookId) return;
    api.tutor
      .createSession(bookId, "free")
      .then((s) => setSessionId(s.id))
      .catch((e) => setError(e.message));
  }, [bookId]);

  async function startRecording() {
    setError(null);
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/mp4";
      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mimeType });
        await uploadRecording(blob, mimeType);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setState("recording");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && state === "recording") {
      mediaRecorderRef.current.stop();
      setState("processing");
    }
  }

  async function uploadRecording(blob: Blob, mimeType: string) {
    if (!sessionId) return;
    try {
      const formData = new FormData();
      formData.append("session_id", sessionId);
      const ext = mimeType.includes("webm") ? "webm" : "m4a";
      formData.append("audio", blob, `recording.${ext}`);

      const resp = await fetch("/api/v1/speaking/attempts", {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const data: SpeakingResult = await resp.json();
      setResult(data);
      setState("done");
    } catch (e) {
      setError((e as Error).message);
      setState("idle");
    }
  }

  if (!bookId) {
    return <p>Select a book first. Go to <a href="/" className="underline">Library</a>.</p>;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Speaking Practice</h1>

      <Card>
        <CardHeader>
          <CardTitle>Record your voice</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {state === "idle" && (
            <Button onClick={startRecording}>🎤 Start Recording</Button>
          )}
          {state === "recording" && (
            <div className="space-y-2">
              <p className="text-red-600 font-medium">🔴 Recording... (Speak now)</p>
              <Button onClick={stopRecording} variant="destructive">
                ⏹ Stop & Send
              </Button>
            </div>
          )}
          {state === "processing" && (
            <p className="text-muted-foreground">
              Processing (STT + LLM + TTS)... This takes ~30-40 seconds.
            </p>
          )}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Your transcript</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">{result.transcript}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tutor feedback</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm whitespace-pre-wrap">{result.feedback_text}</p>
              {result.reply_audio_url && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Listen to feedback:</p>
                  <audio controls src={result.reply_audio_url} className="w-full" />
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-2">
                Pronunciation: <strong>{result.pronunciation_status}</strong>
              </p>
            </CardContent>
          </Card>

          <Button onClick={() => { setState("idle"); setResult(null); }}>
            Record again
          </Button>
        </>
      )}
    </div>
  );
}