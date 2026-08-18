"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface DashboardData {
  name: string;
  free_analyses_remaining: number;
  paid_credits: number;
  total_analyses: number;
  average_readiness: number;
  best_matched_role: string | null;
  skill_gaps_identified: number;
  recent_analyses: {
    id: string;
    target_role: string | null;
    overall_score: number;
    classification: string;
    created_at: string;
  }[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<DashboardData>("/api/v1/usage/dashboard")
      .then(setData)
      .catch(() => setError("Please log in to view your dashboard."));
  }, []);

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">{error}</p>
          <Link href="/login" className="btn-primary mt-4 inline-flex">Log in</Link>
        </div>
      </main>
    );
  }

  if (!data) {
    return <main className="p-10 text-center text-gray-400">Loading dashboard...</main>;
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Welcome back, {data.name.split(" ")[0]}</h1>
          <p className="text-sm text-gray-500">Here&apos;s your placement readiness overview.</p>
        </div>
        <Link href="/analyze" className="btn-primary">New Analysis</Link>
      </div>

      <div className="card mt-6 flex flex-wrap items-center justify-between gap-4 p-5">
        <div className="text-sm font-medium text-gray-800">
          Unlimited analyses: no credit limits, no upgrade needed.
        </div>
      </div>

      {/* Stats grid */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total Analyses" value={data.total_analyses} />
        <Stat label="Average Readiness" value={`${data.average_readiness}%`} />
        <Stat label="Strongest Match" value={data.best_matched_role || "—"} />
        <Stat label="Skill Gaps Identified" value={data.skill_gaps_identified} />
      </div>

      {/* Recent analyses */}
      <div className="card mt-8 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Recent Analyses</h2>
          <Link href="/history" className="text-sm font-medium text-brand-600">View all</Link>
        </div>
        <div className="mt-4 divide-y divide-gray-100">
          {data.recent_analyses.length === 0 && (
            <p className="py-6 text-center text-sm text-gray-400">
              No analyses yet — start your first one to see results here.
            </p>
          )}
          {data.recent_analyses.map((a) => (
            <Link key={a.id} href={`/analysis/${a.id}`}
              className="flex items-center justify-between py-4 hover:bg-gray-50">
              <div>
                <div className="font-medium text-gray-900">{a.target_role || "Untitled role"}</div>
                <div className="text-xs text-gray-400">{new Date(a.created_at).toLocaleDateString()}</div>
              </div>
              <div className="text-right">
                <div className="font-semibold text-brand-600">{a.overall_score}/100</div>
                <div className="text-xs text-gray-400">{a.classification}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
    </div>
  );
}
