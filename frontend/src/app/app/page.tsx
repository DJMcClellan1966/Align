"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  getHelpers,
  getHelper,
  postQuery,
  postFeedback,
  getSuggest,
  type Helper,
  type QueryResponse,
  type SuggestResponse,
} from "@/lib/api";
import { HikingTemplate } from "@/components/templates/HikingTemplate";
import { FinanceTemplate } from "@/components/templates/FinanceTemplate";
import { FaithTemplate } from "@/components/templates/FaithTemplate";
import { GeneralTemplate } from "@/components/templates/GeneralTemplate";

function AppContent() {
  const searchParams = useSearchParams();
  const helperId = searchParams.get("helper");
  const verticalParam = searchParams.get("vertical") || "general";

  const [helpers, setHelpers] = useState<Helper[]>([]);
  const [current, setCurrent] = useState<(Helper & { statement_count: number }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestResponse | null>(null);

  useEffect(() => {
    getHelpers()
      .then((r) => setHelpers(r.helpers))
      .catch(() => setHelpers([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!helperId) return;
    setError(null);
    getHelper(helperId)
      .then(setCurrent)
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load helper");
        setCurrent(null);
      });
    getSuggest(helperId).then(setSuggestions).catch(() => setSuggestions(null));
  }, [helperId]);

  if (loading && !helperId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading…</p>
      </div>
    );
  }

  if (!helperId) {
    return (
      <div className="min-h-screen p-6 max-w-2xl mx-auto">
        <h1 className="text-xl font-semibold mb-4">Your helpers</h1>
        {helpers.length === 0 ? (
          <p className="text-gray-600 mb-4">No helpers yet. Create one from the home page.</p>
        ) : (
          <ul className="space-y-2">
            {helpers.map((h) => (
              <li key={h.helper_id}>
                <Link
                  href={`/app?helper=${encodeURIComponent(h.helper_id)}&vertical=${encodeURIComponent(h.vertical_slug)}`}
                  className="text-indigo-600 hover:underline"
                >
                  {h.intent || h.helper_id} ({h.vertical_slug})
                </Link>
              </li>
            ))}
          </ul>
        )}
        <Link href="/" className="mt-6 inline-block text-indigo-600 hover:underline">
          ← Create new helper
        </Link>
      </div>
    );
  }

  if (error || !current) {
    return (
      <div className="min-h-screen p-6">
        <p className="text-red-600">{error || "Helper not found"}</p>
        <Link href="/app" className="mt-4 inline-block text-indigo-600 hover:underline">
          Back to helpers
        </Link>
      </div>
    );
  }

  const vertical = current.vertical_slug || verticalParam || "general";
  const commonProps = {
    helperId: current.helper_id,
    intent: current.intent,
    statementCount: current.statement_count,
    suggestions: suggestions?.suggestions ?? [],
    onQuery: postQuery,
    onFeedback: postFeedback,
    onSuggest: () => getSuggest(current.helper_id).then(setSuggestions),
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white px-4 py-3 flex items-center justify-between">
        <div>
          <Link href="/" className="text-indigo-600 hover:underline text-sm">YOUI</Link>
          <span className="mx-2 text-gray-400">/</span>
          <span className="font-medium">{current.intent || current.helper_id}</span>
        </div>
        <Link href="/app" className="text-sm text-gray-600 hover:underline">Switch helper</Link>
      </header>
      <main className="flex-1 p-4 md:p-6">
        {vertical === "hiking" && <HikingTemplate {...commonProps} />}
        {vertical === "finance" && <FinanceTemplate {...commonProps} />}
        {vertical === "faith" && <FaithTemplate {...commonProps} />}
        {["general", "journaling", "yoga"].includes(vertical) && (
          <GeneralTemplate {...commonProps} vertical={vertical} />
        )}
        {!["hiking", "finance", "faith", "general", "journaling", "yoga"].includes(vertical) && (
          <GeneralTemplate {...commonProps} vertical={vertical} />
        )}
      </main>
    </div>
  );
}

export default function AppPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading…</div>}>
      <AppContent />
    </Suspense>
  );
}
