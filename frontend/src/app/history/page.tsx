"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface AnalysisSummary {
  id: string;
  overall_score: number;
  classification: string;
  created_at: string;
}

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[] | null>(null);

  useEffect(() => {
    api.get<AnalysisSummary[]>("/api/v1/analyze").then(setAnalyses).catch(() => setAnalyses([]));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900">Analysis History</h1>

      {!analyses && <p className="mt-6 text-gray-400">Loading...</p>}

      {analyses && analyses.length === 0 && (
        <div className="card mt-6 p-10 text-center">
          <p className="text-gray-500">You haven&apos;t run any analyses yet.</p>
          <Link href="/analyze" className="btn-primary mt-4 inline-flex">Run your first analysis</Link>
        </div>
      )}

      <div className="mt-6 space-y-3">
        {analyses?.map((a) => (
          <Link key={a.id} href={`/analysis/${a.id}`} className="card flex items-center justify-between p-5 hover:bg-gray-50">
            <div>
              <div className="font-medium text-gray-900">{a.classification}</div>
              <div className="text-xs text-gray-400">{new Date(a.created_at).toLocaleString()}</div>
            </div>
            <div className="text-xl font-semibold text-brand-600">{a.overall_score}</div>
          </Link>
        ))}
      </div>
    </main>
  );
}
