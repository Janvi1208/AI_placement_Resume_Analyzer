import Link from "next/link";
import Navbar from "@/components/Navbar";
import {
  UploadCloud, FileSearch, Target, MessageSquare, BarChart3, ShieldCheck,
} from "lucide-react";

const steps = [
  { icon: UploadCloud, title: "Upload your resume", desc: "PDF or DOCX. Parsed instantly and securely." },
  { icon: FileSearch, title: "Paste a job description", desc: "Or drop in a job posting URL." },
  { icon: Target, title: "Get your readiness report", desc: "Score, skill gaps, and a prep roadmap — in seconds." },
];

const features = [
  { icon: BarChart3, title: "Deterministic readiness score", desc: "A transparent, weighted score — never an AI guess." },
  { icon: MessageSquare, title: "AI mock interviews", desc: "Practice with questions built from your resume and the JD." },
  { icon: ShieldCheck, title: "Evidence-based, never fabricated", desc: "Every claim about your skills is traceable to your resume." },
];

export default function LandingPage() {
  return (
    <main>
      <Navbar />

      {/* Hero */}
      <section className="mx-auto max-w-5xl px-6 pb-20 pt-20 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
          Know exactly how ready you are for your next job.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600">
          Upload your resume, add a job description, and let AI analyze your
          strengths, skill gaps, interview readiness, and more.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link href="/signup" className="btn-primary">Analyze My Resume</Link>
          <Link href="/#how-it-works" className="btn-secondary">See How It Works</Link>
        </div>
        <p className="mt-4 text-sm text-gray-400">Unlimited analysis access for all resume and job description uploads.</p>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-center text-3xl font-semibold text-gray-900">How it works</h2>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {steps.map((s, i) => (
            <div key={s.title} className="card p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                <s.icon size={22} />
              </div>
              <div className="mt-4 text-sm font-medium text-brand-600">Step {i + 1}</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{s.title}</div>
              <p className="mt-2 text-sm text-gray-600">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-semibold text-gray-900">Built for real placement prep</h2>
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="card p-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <f.icon size={22} />
                </div>
                <div className="mt-4 text-lg font-semibold text-gray-900">{f.title}</div>
                <p className="mt-2 text-sm text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sample report preview */}
      <section className="mx-auto max-w-4xl px-6 py-16">
        <h2 className="text-center text-3xl font-semibold text-gray-900">Example readiness report</h2>
        <div className="card mt-10 p-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">AI Engineer · Acme Corp</div>
              <div className="mt-1 text-3xl font-bold text-gray-900">78 / 100</div>
              <div className="mt-1 text-sm font-medium text-brand-600">Strong Candidate</div>
            </div>
            <div className="h-24 w-24 rounded-full border-8 border-brand-500" style={{ borderRightColor: "#e5e7eb", borderBottomColor: "#e5e7eb" }} />
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            {["Technical Skills", "AI/ML", "Experience", "Projects", "JD Alignment", "Resume Quality"].map((k) => (
              <div key={k} className="rounded-lg bg-gray-50 px-3 py-2">
                <div className="text-gray-500">{k}</div>
                <div className="font-semibold text-gray-900">{Math.floor(60 + Math.random() * 35)}%</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-3xl px-6 py-16">
        <h2 className="text-center text-3xl font-semibold text-gray-900">FAQ</h2>
        <div className="mt-10 space-y-4">
          {[
            ["Is my resume data safe?", "Your resume is treated as private data, stored securely, and never shared."],
            ["Do you fabricate skills I don't have?", "No — every skill match and gap is evidence-based, traced back to your resume text."],
            ["How many analyses can I run?", "You can run as many analyses as you want with unlimited access."],
          ].map(([q, a]) => (
            <div key={q} className="card p-5">
              <div className="font-medium text-gray-900">{q}</div>
              <div className="mt-1 text-sm text-gray-600">{a}</div>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-100 py-10 text-center text-sm text-gray-400">
        © {new Date().getFullYear()} Placement AI. All rights reserved.
      </footer>
    </main>
  );
}
