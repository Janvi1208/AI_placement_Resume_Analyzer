"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

interface SkillMatch {
  skill: string;
  match_type: "exact" | "related" | "partial" | "missing";
  confidence: number;
  evidence?: string;
}
interface SkillGap {
  skill: string;
  priority: "critical" | "high" | "medium" | "low";
  reason: string;
}
interface Analysis {
  id: string;
  overall_score: number;
  classification: string;
  breakdown: Record<string, number>;
  matching_skills: SkillMatch[];
  skill_gaps: SkillGap[];
  recommendations: string[];
}

const PRIORITY_COLOR: Record<string, string> = {
  critical: "bg-red-50 text-red-700 border-red-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-gray-50 text-gray-600 border-gray-200",
};

const MATCH_COLOR: Record<string, string> = {
  exact: "text-green-600",
  related: "text-blue-600",
  partial: "text-yellow-600",
  missing: "text-gray-400",
};

export default function AnalysisResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<Analysis | null>(null);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.get<Analysis>(`/api/v1/analyze/${id}`).then(setData).catch(() => {});
  }, [id]);

  if (!data) return <main className="p-10 text-center text-gray-400">Loading report...</main>;

  const circumference = 2 * Math.PI * 54;
  const offset = circumference * (1 - data.overall_score / 100);

  const filteredGaps = filter === "all"
    ? data.skill_gaps
    : data.skill_gaps.filter((g) => g.priority === filter);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="card p-8">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <div className="text-sm text-gray-500">Placement Readiness</div>
            <div className="mt-1 text-4xl font-bold text-gray-900">{data.overall_score} / 100</div>
            <div className="mt-1 font-medium text-brand-600">{data.classification}</div>
          </div>
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#e5e7eb" strokeWidth="10" />
            <circle cx="60" cy="60" r="54" fill="none" stroke="#4f6df5" strokeWidth="10"
              strokeDasharray={circumference} strokeDashoffset={offset}
              strokeLinecap="round" transform="rotate(-90 60 60)" />
          </svg>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {Object.entries(data.breakdown).map(([k, v]) => (
            <div key={k} className="rounded-lg bg-gray-50 px-3 py-2">
              <div className="text-xs capitalize text-gray-500">{k.replace(/_/g, " ")}</div>
              <div className="font-semibold text-gray-900">{v}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Matching skills */}
      <div className="card mt-6 p-6">
        <h2 className="font-semibold text-gray-900">Matching Skills</h2>
        <div className="mt-4 space-y-2">
          {data.matching_skills.filter((m) => m.match_type !== "missing").map((m) => (
            <div key={m.skill} className="flex items-start justify-between rounded-lg border border-gray-100 p-3">
              <div>
                <div className="font-medium text-gray-900">{m.skill}</div>
                {m.evidence && <div className="text-xs text-gray-500">{m.evidence}</div>}
              </div>
              <span className={`text-xs font-medium capitalize ${MATCH_COLOR[m.match_type]}`}>{m.match_type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Skill gaps */}
      <div className="card mt-6 p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Skill Gaps</h2>
          <div className="flex gap-1 text-xs">
            {["all", "critical", "high", "medium", "low"].map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                className={`rounded-full px-3 py-1 capitalize ${filter === f ? "bg-brand-500 text-white" : "bg-gray-100 text-gray-600"}`}>
                {f}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-4 space-y-2">
          {filteredGaps.map((g) => (
            <div key={g.skill} className={`rounded-lg border p-3 ${PRIORITY_COLOR[g.priority]}`}>
              <div className="flex items-center justify-between">
                <span className="font-medium">{g.skill}</span>
                <span className="text-xs uppercase">{g.priority}</span>
              </div>
              <div className="mt-1 text-sm">{g.reason}</div>
            </div>
          ))}
          {filteredGaps.length === 0 && <p className="text-sm text-gray-400">No gaps at this priority level.</p>}
        </div>
      </div>

      {/* Recommendations */}
      <div className="card mt-6 p-6">
        <h2 className="font-semibold text-gray-900">AI Recommendations</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-gray-700">
          {data.recommendations.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button className="btn-primary" onClick={() => router.push(`/mock-interview?analysis_id=${id}`)}>
          Start Mock Interview
        </button>
        <Link href="/history" className="btn-secondary">Back to History</Link>
      </div>
    </main>
  );
}
