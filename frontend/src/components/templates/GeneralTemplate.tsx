"use client";

import { SharedQuery } from "./SharedQuery";
import type { QueryResponse } from "@/lib/api";

type GeneralTemplateProps = {
  helperId: string;
  intent: string;
  statementCount: number;
  suggestions: string[];
  vertical: string;
  onQuery: (helperId: string, message: string) => Promise<QueryResponse>;
  onFeedback: (helperId: string, query: string, response: string, useful: boolean, note?: string) => Promise<void>;
  onSuggest: () => void;
};

const verticalLabels: Record<string, string> = {
  general: "General helper",
  journaling: "Journaling & ideas",
  yoga: "Yoga & mindfulness",
};

export function GeneralTemplate(props: GeneralTemplateProps) {
  const label = verticalLabels[props.vertical] || props.vertical;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 mb-4">
        <h1 className="text-lg font-semibold text-gray-800">{label}</h1>
        <p className="text-sm text-gray-700 mt-1">{props.intent}</p>
        <p className="text-xs text-gray-600 mt-2">Knowledge base: {props.statementCount} items</p>
      </div>
      <div className="rounded-lg border border-gray-200 p-4">
        <p className="text-sm text-gray-600">
          Use the question box below to get answers from your personal knowledge base. Your helper learns from your feedback over time.
        </p>
      </div>
      {props.suggestions.length > 0 && (
        <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <h3 className="text-sm font-medium text-amber-800 mb-1">Suggestions for you</h3>
          <ul className="text-sm text-amber-700 list-disc list-inside">
            {props.suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
          <button
            type="button"
            onClick={props.onSuggest}
            className="mt-2 text-xs text-amber-700 underline"
          >
            Refresh suggestions
          </button>
        </div>
      )}
      <SharedQuery helperId={props.helperId} onQuery={props.onQuery} onFeedback={props.onFeedback} />
    </div>
  );
}
