import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { useJobs } from "@/contexts/JobsContext";

interface Library {
  id: string;
  name: string;
  root_path: string;
  status: string;
  created_at: string;
}

interface LibraryWithJob extends Library {
  activeJobId?: string;
  book_id?: string;
}

function JobProgress({ jobId }: { jobId: string }) {
  const { getJob } = useJobs();
  const job = getJob(jobId);
  if (!job) return <p className="text-sm text-muted-foreground">Loading...</p>;

  const progress = job.progress as {
    done?: number;
    total?: number;
    current_file?: string;
    stage?: string;
  };
  const done = progress.done ?? 0;
  const total = progress.total ?? 0;

  if (job.status === "completed") {
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium text-green-600">✅ Completed</p>
        <Progress value={100} />
        <p className="text-xs text-muted-foreground">
          Total files processed: {total}
        </p>
      </div>
    );
  }
  if (job.status === "failed") {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Job failed. Check server logs for details.
        </AlertDescription>
      </Alert>
    );
  }
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">
        Processing ({job.stage ?? "queued"})
      </p>
      <Progress value={done} max={Math.max(1, total)} />
      <p className="text-xs text-muted-foreground">
        {done} / {total} files
        {progress.current_file && ` · ${progress.current_file}`}
      </p>
    </div>
  );
}

export default function Libraries() {
  const [libraries, setLibraries] = useState<LibraryWithJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const { startJob } = useJobs();

  useEffect(() => {
    fetch("/api/v1/libraries")
      .then((r) => r.json())
      .then((libs: Library[]) => {
        const withJobs: LibraryWithJob[] = libs.map((l) => {
          const raw = localStorage.getItem(`aet_lib_job_${l.id}`);
          return { ...l, activeJobId: raw ?? undefined };
        });
        setLibraries(withJobs);
        // شروع polling برای jobهای فعال
        for (const l of withJobs) {
          if (l.activeJobId) startJob(l.activeJobId);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [startJob]);

  async function handleCreate() {
    if (!name.trim() || !path.trim()) return;
    setError(null);
    try {
      const resp = await fetch("/api/v1/libraries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, root_path: path }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const lib = await resp.json();
      setLibraries((prev) => [lib, ...prev]);
      setName("");
      setPath("");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleIngest(libraryId: string) {
    setError(null);
    try {
      const resp = await fetch(`/api/v1/libraries/${libraryId}/ingest`, {
        method: "POST",
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      localStorage.setItem(`aet_lib_job_${libraryId}`, data.job_id);
      setLibraries((prev) =>
        prev.map((l) => (l.id === libraryId ? { ...l, activeJobId: data.job_id } : l)),
      );
      startJob(data.job_id);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (loading) return <p>Loading...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Learning Libraries</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create New Library</CardTitle>
          <CardDescription>
            Specify a folder on your computer containing PDFs and audio files.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., English File 2"
              className="w-full border rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Root Folder Path</label>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="e.g., C:\Source-Temp"
              className="w-full border rounded-md px-3 py-2 font-mono text-sm"
            />
          </div>
          <Button onClick={handleCreate}>Create Library</Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {libraries.map((lib) => (
          <Card key={lib.id}>
            <CardHeader>
              <CardTitle>{lib.name}</CardTitle>
              <CardDescription className="font-mono text-xs">
                {lib.root_path}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {lib.activeJobId ? (
                <JobProgress jobId={lib.activeJobId} />
              ) : (
                <Button onClick={() => handleIngest(lib.id)}>Ingest Library</Button>
              )}
              {lib.activeJobId && (
                <Link to={`/tutor?book=${lib.book_id}`}>
                  <Button variant="outline" size="sm">Open Tutor</Button>
                </Link>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}