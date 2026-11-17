import { useEffect, useState } from "react";
import { api, type HealthResponse, type HealthDbResponse } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type LoadState<T> =
  | { kind: "loading" }
  | { kind: "ok"; data: T }
  | { kind: "error"; message: string };

export default function Health() {
  const [backend, setBackend] = useState<LoadState<HealthResponse>>({ kind: "loading" });
  const [db, setDb] = useState<LoadState<HealthDbResponse>>({ kind: "loading" });

  async function refresh() {
    setBackend({ kind: "loading" });
    setDb({ kind: "loading" });
    try {
      const data = await api.health();
      setBackend({ kind: "ok", data });
    } catch (e) {
      setBackend({ kind: "error", message: (e as Error).message });
    }
    try {
      const data = await api.healthDb();
      setDb({ kind: "ok", data });
    } catch (e) {
      setDb({ kind: "error", message: (e as Error).message });
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">AI English Tutor</h1>
          <Button onClick={() => void refresh()}>Refresh</Button>
        </div>
        <p className="text-muted-foreground">
          System status dashboard (P1 foundation)
        </p>

        {/* Backend health */}
        <Card>
          <CardHeader>
            <CardTitle>Backend</CardTitle>
            <CardDescription>FastAPI at http://127.0.0.1:8000</CardDescription>
          </CardHeader>
          <CardContent>
            {backend.kind === "loading" && <p>Checking…</p>}
            {backend.kind === "error" && (
              <Alert variant="destructive">
                <AlertTitle>Backend unreachable</AlertTitle>
                <AlertDescription>{backend.message}</AlertDescription>
              </Alert>
            )}
            {backend.kind === "ok" && (
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-mono text-muted-foreground">status: </span>
                  <span className={backend.data.status === "ok" ? "text-green-600 font-bold" : ""}>
                    {backend.data.status}
                  </span>
                </div>
                <div>
                  <span className="font-mono text-muted-foreground">version: </span>
                  {backend.data.version}
                </div>
                <div>
                  <span className="font-mono text-muted-foreground">environment: </span>
                  {backend.data.environment}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* DB health */}
        <Card>
          <CardHeader>
            <CardTitle>Database</CardTitle>
            <CardDescription>PostgreSQL + pgvector</CardDescription>
          </CardHeader>
          <CardContent>
            {db.kind === "loading" && <p>Checking…</p>}
            {db.kind === "error" && (
              <Alert variant="destructive">
                <AlertTitle>DB check failed</AlertTitle>
                <AlertDescription>{db.message}</AlertDescription>
              </Alert>
            )}
            {db.kind === "ok" && (
              <div className="space-y-1 text-sm">
                <div>
                  <span className="font-mono text-muted-foreground">status: </span>
                  <span className={db.data.status === "ok" ? "text-green-600 font-bold" : ""}>
                    {db.data.status}
                  </span>
                </div>
                <div>
                  <span className="font-mono text-muted-foreground">db: </span>
                  {db.data.db}
                </div>
                <div>
                  <span className="font-mono text-muted-foreground">postgres: </span>
                  {db.data.postgres_version ?? "—"}
                </div>
                <div>
                  <span className="font-mono text-muted-foreground">pgvector: </span>
                  {db.data.pgvector_version ?? "—"}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <p className="text-xs text-muted-foreground text-center">
          P1 Foundation · {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}