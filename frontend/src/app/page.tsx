"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { postIntent } from "@/lib/api";

export default function HomePage() {
  const [intent, setIntent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = intent.trim();
    if (!text) return;
    setError(null);
    setLoading(true);
    try {
      const result = await postIntent(text);
      router.push(`/app?helper=${encodeURIComponent(result.helper_id)}&vertical=${encodeURIComponent(result.vertical_slug)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-semibold text-center mb-2">YOUI</h1>
        <p className="text-center text-gray-600 mb-6">You Intelligence – a personal AI based on your needs</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            What do you want to create or learn about?
          </label>
          <input
            type="text"
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="e.g. hiking, yoga, finance, faith, journaling..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading}
          />
          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading || !intent.trim()}
            className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating your helper…" : "Continue"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          <a href="/app" className="text-indigo-600 hover:underline">Open existing helper</a>
        </p>
      </div>
    </main>
  );
}
