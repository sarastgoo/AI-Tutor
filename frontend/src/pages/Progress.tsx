import { useEffect, useState } from "react";
import { api, type Progress } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);

  useEffect(() => {
    api.progress.get().then(setData);
  }, []);

  if (!data) return <p>Loading progress...</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Your Progress</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatCard label="Sessions" value={data.sessions} />
        <StatCard label="Messages" value={data.messages} />
        <StatCard label="Speaking attempts" value={data.speaking_attempts} />
        <StatCard label="Lexemes learned" value={data.unique_lexemes} />
        <StatCard label="Due reviews" value={data.due_reviews} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}