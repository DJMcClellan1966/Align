"use client";

import { SharedQuery } from "./SharedQuery";
import type { QueryResponse } from "@/lib/api";

type FinanceTemplateProps = {
  helperId: string;
  intent: string;
  statementCount: number;
  suggestions: string[];
  onQuery: (helperId: string, message: string) => Promise<QueryResponse>;
  onFeedback: (helperId: string, query: string, response: string, useful: boolean, note?: string) => Promise<void>;
  onSuggest: () => void;
};

export function FinanceTemplate(props: FinanceTemplateProps) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 mb-4">
        <h1 className="text-lg font-semibold text-blue-800">Personal finance</h1>
        <p className="text-sm text-blue-700 mt-1">{props.intent}</p>
        <p className="text-xs text-blue-600 mt-2">Knowledge base: {props.statementCount} items</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="font-medium text-gray-800 mb-2">Budget & goals</h2>
          <p className="text-sm text-gray-600">Ask about budgeting, savings, or debt payoff strategies.</p>
        </div>
        <div className="rounded-lg border border-gray-200 p-4">
          <h2 className="font-medium text-gray-800 mb-2">Investing & retirement</h2>
          <p className="text-sm text-gray-600">Get guidance on diversification and long-term planning from your knowledge base.</p>
        </div>
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
