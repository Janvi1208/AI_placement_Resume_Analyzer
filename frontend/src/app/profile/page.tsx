"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

interface ProfileData {
  name: string;
  email: string;
  plan: string;
  plan_label: string;
  free_analyses_remaining: number;
  paid_credits: number;
  total_analyses: number;
  saved_resumes: {
    id: string;
    filename: string;
    uploaded_at: string;
    skills_count: number;
    name: string;
  }[];
  saved_job_descriptions: {
    id: string;
    role: string;
    company: string;
    uploaded_at: string;
    required_skills_count: number;
  }[];
  recent_analyses: {
    id: string;
    target_role: string;
    overall_score: number;
    classification: string;
    created_at: string;
  }[];
}

export default function ProfilePage() {
  const [data, setData] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<ProfileData>("/api/v1/usage/profile")
      .then(setData)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Please log in to view your profile.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <main className="p-10 text-center text-gray-400">Loading profile...</main>;
  }

  if (error || !data) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">{error || "Profile unavailable."}</p>
          <Link href="/login" className="btn-primary mt-4 inline-flex">Log in</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-600">Profile</p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-900">{data.name}</h1>
          <p className="text-sm text-gray-500">{data.email}</p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-xs uppercase tracking-[0.2em] text-gray-400">Plan</div>
          <div className="mt-2 flex items-center gap-3">
            <span className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-sm font-semibold text-brand-700">
              {data.plan_label}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Stat label="Free analyses left" value={data.free_analyses_remaining} />
        <Stat label="Paid credits" value={data.paid_credits} />
        <Stat label="Total analyses" value={data.total_analyses} />
      </div>

      <div className="card mt-8 p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Unlimited access</h2>
            <p className="mt-1 text-sm text-gray-500">You can keep uploading resumes and job descriptions without any analysis limits.</p>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-2">
        <section className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Saved resumes</h2>
            <span className="text-sm text-gray-400">{data.saved_resumes.length}</span>
          </div>
          <div className="space-y-3">
            {data.saved_resumes.length === 0 ? (
              <p className="text-sm text-gray-500">No resumes uploaded yet.</p>
            ) : (
              data.saved_resumes.map((resume) => (
                <div key={resume.id} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="font-medium text-gray-900">{resume.name}</div>
                      <div className="text-xs text-gray-500">{resume.filename}</div>
                    </div>
                    <span className="rounded-full bg-white px-2 py-1 text-xs text-gray-600">{resume.skills_count} skills</span>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Saved job descriptions</h2>
            <span className="text-sm text-gray-400">{data.saved_job_descriptions.length}</span>
          </div>
          <div className="space-y-3">
            {data.saved_job_descriptions.length === 0 ? (
              <p className="text-sm text-gray-500">No job descriptions saved yet.</p>
            ) : (
              data.saved_job_descriptions.map((jd) => (
                <div key={jd.id} className="rounded-xl border border-gray-100 bg-gray-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <div className="font-medium text-gray-900">{jd.role}</div>
                      <div className="text-xs text-gray-500">{jd.company}</div>
                    </div>
                    <span className="rounded-full bg-white px-2 py-1 text-xs text-gray-600">{jd.required_skills_count} required</span>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    Saved {new Date(jd.uploaded_at).toLocaleDateString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="card mt-8 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Recent analyses</h2>
          <Link href="/history" className="text-sm font-medium text-brand-600">View all</Link>
        </div>

        {data.recent_analyses.length === 0 ? (
          <p className="text-sm text-gray-500">No analyses yet.</p>
        ) : (
          <div className="space-y-3">
            {data.recent_analyses.map((analysis) => (
              <Link key={analysis.id} href={`/analysis/${analysis.id}`} className="flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50 p-3 hover:bg-gray-100">
                <div>
                  <div className="font-medium text-gray-900">{analysis.target_role}</div>
                  <div className="text-xs text-gray-400">{new Date(analysis.created_at).toLocaleDateString()}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-brand-600">{analysis.overall_score}/100</div>
                  <div className="text-xs text-gray-500">{analysis.classification}</div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-gray-900">{value}</div>
    </div>
  );
}
