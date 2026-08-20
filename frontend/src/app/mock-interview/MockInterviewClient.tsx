"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

interface Question {
  id: string;
  category: string;
  question: string;
  why_selected: string;
}

interface Feedback {
  technical_accuracy: number;
  communication: number;
  depth: number;
  relevance: number;
  overall: number;
  feedback_text: string;
  next_question: Question | null;
}

export default function MockInterviewClient() {
  const params = useSearchParams();
  const analysisId = params.get("analysis_id");

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!analysisId) return;

    api
      .post<{ session_id: string; question: Question }>(
        "/api/v1/interview/start",
        {
          analysis_id: analysisId,
        }
      )
      .then((res) => {
        setSessionId(res.session_id);
        setQuestion(res.question);
      });
  }, [analysisId]);

  async function submitAnswer() {
    if (!sessionId || !question || !answer.trim()) return;

    setLoading(true);

    try {
      const fb = await api.post<Feedback>("/api/v1/interview/answer", {
        session_id: sessionId,
        question_id: question.id,
        answer,
      });

      setFeedback(fb);

      if (fb.next_question) {
        setTimeout(() => {
          setQuestion(fb.next_question);
          setFeedback(null);
          setAnswer("");
        }, 2500);
      } else {
        setDone(true);
      }
    } finally {
      setLoading(false);
    }
  }

  if (!analysisId) {
    return (
      <main className="p-10 text-center text-gray-500">
        Start an interview from an analysis report.
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-semibold text-gray-900">
        AI Mock Interview
      </h1>

      {done && (
        <div className="card mt-6 p-8 text-center">
          <h2 className="text-xl font-semibold text-gray-900">
            Interview Complete
          </h2>

          <p className="mt-2 text-gray-500">
            Great work — check your dashboard for a detailed breakdown.
          </p>
        </div>
      )}

      {!done && question && (
        <div className="card mt-6 p-6">
          <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium capitalize text-brand-600">
            {question.category.replace(/_/g, " ")}
          </span>

          <h2 className="mt-3 text-lg font-medium text-gray-900">
            {question.question}
          </h2>

          <p className="mt-1 text-xs text-gray-400">
            {question.why_selected}
          </p>

          <textarea
            className="input mt-4 h-32"
            placeholder="Type your answer..."
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            disabled={!!feedback}
          />

          {!feedback ? (
            <button
              className="btn-primary mt-4 w-full"
              disabled={loading || !answer.trim()}
              onClick={submitAnswer}
            >
              {loading ? "Evaluating..." : "Submit Answer"}
            </button>
          ) : (
            <div className="mt-4 rounded-xl bg-gray-50 p-4 text-sm">
              <p className="text-gray-700">
                {feedback.feedback_text}
              </p>

              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500">
                <div>
                  Technical: {feedback.technical_accuracy}
                </div>

                <div>
                  Communication: {feedback.communication}
                </div>

                <div>
                  Depth: {feedback.depth}
                </div>

                <div>
                  Relevance: {feedback.relevance}
                </div>
              </div>

              <div className="mt-2 font-medium text-brand-600">
                Overall: {feedback.overall}/100
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}