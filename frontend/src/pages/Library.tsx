import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Book } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function Library() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.books
      .list()
      .then(setBooks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading books...</p>;
  if (error) return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Your Library</h1>
      {books.length === 0 ? (
        <p className="text-muted-foreground">No books yet. Import one from the API.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {books.map((book) => (
            <Card key={book.id}>
              <CardHeader>
                <CardTitle>{book.title}</CardTitle>
                <CardDescription>
                  Language: {book.language} · Status: {book.status}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Link to={`/tutor?book=${book.id}`}>
                  <Button>Start Tutoring</Button>
                </Link>
                <Link to={`/vocabulary?book=${book.id}`}>
                  <Button variant="outline">Vocabulary</Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}