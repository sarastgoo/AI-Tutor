import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type VocabItem } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Vocabulary() {
  const [params] = useSearchParams();
  const bookId = params.get("book");
  const [items, setItems] = useState<VocabItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!bookId) return;
    api.vocabulary
      .list(bookId, 200)
      .then((d) => {
        setItems(d.items);
        setTotal(d.total_lexemes);
      })
      .finally(() => setLoading(false));
  }, [bookId]);

  async function handleExport() {
    if (!bookId) return;
    setExporting(true);
    try {
      const r = await api.exports.vocabulary(bookId);
      window.open(r.download_url, "_blank");
    } finally {
      setExporting(false);
    }
  }

  if (!bookId) return <p>Select a book first.</p>;
  if (loading) return <p>Loading vocabulary...</p>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Vocabulary</h1>
          <p className="text-muted-foreground text-sm">{total} unique lexemes</p>
        </div>
        <Button onClick={handleExport} disabled={exporting}>
          {exporting ? "Exporting..." : "Export DOCX"}
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>All lexemes</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead className="text-left border-b">
              <tr>
                <th className="py-2">#</th>
                <th>Lemma</th>
                <th>POS</th>
                <th className="text-right">Occurrences</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={it.lexeme_id} className="border-b">
                  <td className="py-1 text-muted-foreground">{i + 1}</td>
                  <td>{it.lemma}</td>
                  <td className="text-muted-foreground">{it.pos}</td>
                  <td className="text-right">{it.occurrence_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}