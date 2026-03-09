"use client";

import { useState } from "react";
import type { QueryResponse } from "@/lib/api";

type SharedQueryProps = {
  helperId: string;
  onQuery: (helperId: string, message: string) => Promise<QueryResponse>;
  onFeedback: (helperId: string, query: string, response: string, useful: boolean, note?: string) => Promise<void>;
};

export function SharedQuery({ helperId, onQuery, onFeedback }: SharedQueryProps) {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setResult(null);
    setFeedbackSent(false);
    try {
      const res = await onQuery(helperId, message);
      setResult(res);
    } catch {
      setResult({ answer: "Sorry, the request failed.", citations: [], user_context_used: false });
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(useful: boolean) {
    if (!result) return;
    try {
      await onFeedback(helperId, message, result.answer, useful);
      setFeedbackSent(true);
    } catch {
      // ignore
    }
  }

  return (
    <section className="mt-6 border-t pt-6">
      <h2 className="text-lg font-semibold mb-3">Ask your helper</h2>
      <form onSubmit={handleAsk} className="flex gap-2 mb-4">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask a question..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "…" : "Ask"}
        </button>
      </form>
      {result && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <p className="whitespace-pre-wrap text-sm">{result.answer}</p>
          {result.citations?.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">Based on {result.citations.length} knowledge items.</p>
          )}
          {!feedbackSent && (
            <div className="flex gap-2 mt-2">
              <span className="text-xs text-gray-500">Was this useful?</span>
              <button
                type="button"
                onClick={() => sendFeedback(true)}
                className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded"
              >
                Yes
              </button>
              <button
                type="button"
                onClick={() => sendFeedback(false)}
                className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded"
              >
                No
              </button>
            </div>
          )}
          {feedbackSent && <p className="text-xs text-gray-500">Thanks for your feedback.</p>}
        </div>
      )}
    </section>
  );
}
