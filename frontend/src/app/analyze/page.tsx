"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, X, Loader2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";

type Step = 1 | 2 | 3;

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);

  const [file, setFile] = useState<File | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [jdText, setJdText] = useState("");
  const [jdUrl, setJdUrl] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);

  const [targetRole, setTargetRole] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  async function handleFileSelect(f: File) {
    setFile(f);
    setError(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", f);
      const res = await api.post<{ id: string }>("/api/v1/resume/upload", form);
      setResumeId(res.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
      setFile(null);
    } finally {
      setUploading(false);
    }
  }

  async function submitJobDescription() {
    setError(null);
    try {
      const res = await api.post<{ id: string }>("/api/v1/jobs", {
        raw_text: jdText || undefined,
        url: jdText ? undefined : jdUrl || undefined,
        role: targetRole || undefined,
      });
      setJobId(res.id);
      setStep(3);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not process job description.");
    }
  }

  async function runAnalysis() {
    if (!resumeId || !jobId) return;
    setAnalyzing(true);
    setError(null);
    try {
      const res = await api.post<{ id: string }>("/api/v1/analyze/readiness", {
        resume_id: resumeId,
        job_description_id: jobId,
        target_role: targetRole || undefined,
        experience_level: experienceLevel || undefined,
      });
      router.push(`/analysis/${res.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900">Analyze My Placement Readiness</h1>

      {/* Step indicator */}
      <div className="mt-4 flex items-center gap-2 text-xs text-gray-400">
        {[1, 2, 3].map((s) => (
          <div key={s} className={`h-1.5 flex-1 rounded-full ${s <= step ? "bg-brand-500" : "bg-gray-200"}`} />
        ))}
      </div>

      {error && <div className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-600">{error}</div>}

      {step === 1 && (
        <div className="card mt-6 p-6">
          <h2 className="font-semibold text-gray-900">Step 1 · Upload Resume</h2>
          <p className="mt-1 text-sm text-gray-500">PDF or DOCX, up to 8MB.</p>

          {!file ? (
            <label className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 p-10 text-center hover:border-brand-300">
              <UploadCloud className="text-gray-400" />
              <span className="mt-2 text-sm text-gray-500">Click to select a file</span>
              <input type="file" accept=".pdf,.docx" className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])} />
            </label>
          ) : (
            <div className="mt-4 flex items-center justify-between rounded-xl border border-gray-200 p-4">
              <div>
                <div className="text-sm font-medium text-gray-900">{file.name}</div>
                <div className="text-xs text-gray-400">{(file.size / 1024).toFixed(0)} KB</div>
              </div>
              {uploading ? (
                <Loader2 className="animate-spin text-brand-500" size={18} />
              ) : (
                <button onClick={() => { setFile(null); setResumeId(null); }} className="text-gray-400 hover:text-gray-600">
                  <X size={18} />
                </button>
              )}
            </div>
          )}

          <button className="btn-primary mt-6 w-full" disabled={!resumeId} onClick={() => setStep(2)}>
            Continue
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="card mt-6 p-6">
          <h2 className="font-semibold text-gray-900">Step 2 · Job Description</h2>
          <textarea className="input mt-4 h-40" placeholder="Paste the job description here..."
            value={jdText} onChange={(e) => setJdText(e.target.value)} />
          <div className="mt-3 text-center text-xs text-gray-400">— or —</div>
          <input className="input mt-3" placeholder="Paste a job posting URL"
            value={jdUrl} onChange={(e) => setJdUrl(e.target.value)} disabled={!!jdText} />

          <div className="mt-6 grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-gray-700">Target role (optional)</label>
              <input className="input mt-1" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Experience level</label>
              <select className="input mt-1" value={experienceLevel} onChange={(e) => setExperienceLevel(e.target.value)}>
                <option value="">Select...</option>
                <option value="entry">Entry-level</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button className="btn-secondary flex-1" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary flex-1" disabled={!jdText && !jdUrl} onClick={submitJobDescription}>
              Continue
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card mt-6 p-6 text-center">
          <h2 className="font-semibold text-gray-900">Ready to analyze</h2>
          <p className="mt-2 text-sm text-gray-500">
            We&apos;ll check your entitlement, then run the full readiness pipeline.
          </p>
          <button className="btn-primary mt-6 w-full" disabled={analyzing} onClick={runAnalysis}>
            {analyzing ? "Analyzing..." : "Analyze My Placement Readiness"}
          </button>
        </div>
      )}
    </main>
  );
}
