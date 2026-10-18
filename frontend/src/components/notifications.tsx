"use client";
import { useEffect, useState } from "react";
import { AccountError, apiRequest } from "@/lib/auth-api";
import { Badge, Button, Pill } from "./ui";
type Item = { id: string; type: string; message: string; is_read: boolean };
export function Notifications() {
  const [items, setItems] = useState<Item[]>([]);
  const [problem, setProblem] = useState("");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  useEffect(() => {
    let active = true;
    apiRequest<{ results: Item[]; next: string | null }>(
      `notifications?page=${page}`,
      "GET",
      undefined,
      true,
    )
      .then((data) => {
        if (active) {
          setItems(data.results);
          setHasNext(!!data.next);
        }
      })
      .catch((error) => {
        if (active)
          setProblem(
            error instanceof AccountError
              ? error.message
              : "Could not load notifications.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page]);
  async function read(item: Item) {
    try {
      await apiRequest(
        `notifications/${item.id}/read`,
        "POST",
        undefined,
        true,
      );
      setItems((current) =>
        current.map((row) =>
          row.id === item.id ? { ...row, is_read: true } : row,
        ),
      );
    } catch {
      setProblem("Could not update notification. Please retry.");
    }
  }
  return (
    <main id="main" className="container account-page">
      <Pill>YOUR UPDATES</Pill>
      <h1>Stay in the loop.</h1>
      {problem && (
        <p role="alert" className="auth-error">
          {problem}
        </p>
      )}
      {loading && <p role="status">Loading…</p>}
      {!loading && !problem && !items.length && <p>No notifications yet.</p>}
      <div className="event-list">
        {items.map((item) => (
          <article className="card auth-card" key={item.id}>
            <Badge>{item.is_read ? "Read" : "New"}</Badge>
            <p>{item.message}</p>
            {!item.is_read && (
              <Button variant="secondary" onClick={() => read(item)}>
                Mark as read
              </Button>
            )}
          </article>
        ))}
      </div>
      <div className="auth-actions">
        {page > 1 && (
          <Button onClick={() => setPage(page - 1)}>Previous page</Button>
        )}
        {hasNext && (
          <Button onClick={() => setPage(page + 1)}>Next page</Button>
        )}
      </div>
    </main>
  );
}
