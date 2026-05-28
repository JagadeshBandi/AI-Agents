"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import {
  ArrowLeft,
  BookOpen,
  Target,
  Lightbulb,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Calendar,
  Building2,
  BrainCircuit,
} from "lucide-react";
import AppNav from "@/components/AppNav";
import { api, type InterviewPrep, type MockQuestion } from "@/lib/api";
import { cn } from "@/lib/utils";

// ── Skeleton loaders ──────────────────────────────────────────
function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-6 space-y-3 animate-pulse">
      <div className="h-4 bg-zinc-800/80 rounded w-32" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={cn("h-3 bg-zinc-800/60 rounded", i === lines - 1 ? "w-2/3" : "w-full")} />
      ))}
    </div>
  );
}

// ── STAR color labels ─────────────────────────────────────────
const STAR_PARTS = [
  { label: "S", full: "Situation", color: "text-blue-400", bg: "bg-blue-950/40 border-blue-800/40" },
  { label: "T", full: "Task", color: "text-violet-400", bg: "bg-violet-950/40 border-violet-800/40" },
  { label: "A", full: "Action", color: "text-amber-400", bg: "bg-amber-950/40 border-amber-800/40" },
  { label: "R", full: "Result", color: "text-emerald-400", bg: "bg-emerald-950/40 border-emerald-800/40" },
];

// Split STAR template text into parts by parsing the template
function StarFramework({ template }: { template: string }) {
  // Try to split on S: T: A: R: markers if present
  const hasMarkers = /\bS[:\s]|Situation[:\s]/i.test(template);

  if (!hasMarkers) {
    return (
      <div className="bg-zinc-900/60 border border-zinc-800/40 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2 mb-2">
          {STAR_PARTS.map((p) => (
            <span
              key={p.label}
              className={cn(
                "px-2 py-0.5 rounded-md text-xs font-bold border",
                p.bg,
                p.color
              )}
            >
              {p.label}
            </span>
          ))}
          <span className="text-xs text-zinc-500 ml-1">Framework Guide</span>
        </div>
        <p className="text-xs text-zinc-400 leading-relaxed">{template}</p>
      </div>
    );
  }

  // Parse markers
  const parts = template.split(/(?=\b(?:Situation|Task|Action|Result)\b)/i);

  return (
    <div className="bg-zinc-900/60 border border-zinc-800/40 rounded-xl px-4 py-3 space-y-2">
      <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-3">
        STAR Framework Guide
      </p>
      {STAR_PARTS.map((sp, idx) => (
        <div key={sp.label} className="flex items-start gap-2.5">
          <span
            className={cn(
              "w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold border shrink-0 mt-0.5",
              sp.bg,
              sp.color
            )}
          >
            {sp.label}
          </span>
          <div>
            <span className={cn("text-xs font-semibold", sp.color)}>{sp.full}: </span>
            <span className="text-xs text-zinc-400 leading-relaxed">
              {parts[idx]
                ? parts[idx].replace(/^(Situation|Task|Action|Result)[:\s]*/i, "").trim()
                : "Provide specific details here"}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Individual Question ───────────────────────────────────────
function QuestionItem({
  question,
  index,
  expanded,
  onToggle,
}: {
  question: MockQuestion;
  index: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  const [practiceText, setPracticeText] = useState("");

  return (
    <div
      className={cn(
        "border rounded-2xl overflow-hidden transition-all",
        expanded ? "border-indigo-800/40 bg-indigo-950/10" : "border-zinc-800/40 bg-zinc-900/30"
      )}
    >
      {/* Question header */}
      <button
        onClick={onToggle}
        className="w-full flex items-start justify-between gap-3 px-5 py-4 text-left hover:bg-zinc-800/20 transition-colors"
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <span className="shrink-0 w-6 h-6 rounded-lg bg-zinc-800/80 border border-zinc-700/60 flex items-center justify-center text-xs font-bold text-zinc-400 mt-0.5">
            {index + 1}
          </span>
          <span className="text-sm text-zinc-200 font-medium leading-relaxed">{question.question}</span>
        </div>
        {expanded ? (
          <ChevronUp size={15} className="text-zinc-500 shrink-0 mt-1" />
        ) : (
          <ChevronDown size={15} className="text-zinc-500 shrink-0 mt-1" />
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-zinc-800/40">
          {/* Guidance */}
          <div className="pt-4">
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2">
              What they want to hear
            </p>
            <p className="text-sm text-zinc-300 leading-relaxed">{question.guidance}</p>
          </div>

          {/* STAR Framework */}
          <StarFramework template={question.star_template} />

          {/* Practice textarea */}
          <div>
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2">
              Practice your answer
            </p>
            <textarea
              rows={4}
              className="no-base w-full rounded-xl border border-zinc-700/40 bg-zinc-950/80 px-4 py-3 text-sm text-zinc-200 placeholder:text-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/40 transition-all resize-none"
              placeholder="Type your practice answer here... Use the STAR framework above as a guide."
              value={practiceText}
              onChange={(e) => setPracticeText(e.target.value)}
            />
            {practiceText.length > 0 && (
              <p className="text-xs text-zinc-700 mt-1 text-right">
                {practiceText.length} characters
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────
export default function InterviewPrepPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [prep, setPrep] = useState<InterviewPrep | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedQ, setExpandedQ] = useState<number | null>(0);

  useEffect(() => {
    api.interview
      .getPrep(id)
      .then((data) => setPrep(data))
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Failed to load prep materials")
      )
      .finally(() => setLoading(false));
  }, [id]);

  const toggleQuestion = (idx: number) => {
    setExpandedQ((prev) => (prev === idx ? null : idx));
  };

  // ── Loading state ─────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <AppNav />
        <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
          {/* Breadcrumb skeleton */}
          <div className="h-4 bg-zinc-800/60 rounded w-48 animate-pulse" />

          {/* Hero skeleton */}
          <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-6 animate-pulse space-y-3">
            <div className="h-6 bg-zinc-800/80 rounded w-48" />
            <div className="h-4 bg-zinc-800/60 rounded w-32" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <CardSkeleton lines={6} />
            <div className="lg:col-span-2 space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <CardSkeleton key={i} lines={2} />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────────
  if (error || !prep) {
    return (
      <div className="min-h-screen bg-zinc-950">
        <AppNav />
        <div className="max-w-lg mx-auto px-6 py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-950/40 border border-red-800/40 flex items-center justify-center mx-auto mb-5">
            <BrainCircuit size={24} className="text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-zinc-100 mb-2">
            Prep materials unavailable
          </h2>
          <p className="text-zinc-500 text-sm mb-6">
            {error || "Interview prep not found for this application."}
          </p>
          <Link
            href="/track"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700/60 text-zinc-300 text-sm font-medium hover:bg-zinc-700/60 transition-colors"
          >
            <ArrowLeft size={14} /> Back to Applications
          </Link>
        </div>
      </div>
    );
  }

  // ── Main content ──────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <AppNav />

      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Link href="/track" className="hover:text-zinc-400 transition-colors">
            Applications
          </Link>
          <span>/</span>
          <span className="text-zinc-400">{prep.company}</span>
          <span>/</span>
          <span className="text-zinc-500">Interview Prep</span>
        </div>

        {/* Hero */}
        <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <Link
                href="/track"
                className="w-9 h-9 rounded-xl bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/60 transition-all shrink-0"
              >
                <ArrowLeft size={15} />
              </Link>
              <div>
                <h1 className="text-xl font-bold text-zinc-50">{prep.job_title}</h1>
                <div className="flex items-center gap-3 mt-1.5">
                  <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                    <Building2 size={12} />
                    {prep.company}
                  </div>
                  {prep.generated_at && (
                    <div className="flex items-center gap-1.5 text-xs text-zinc-600">
                      <Calendar size={12} />
                      Generated{" "}
                      {new Date(prep.generated_at).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-xs font-medium text-indigo-300">
              <BrainCircuit size={13} />
              AI-Generated Brief
            </div>
          </div>
        </div>

        {/* Three-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left column — Company Intelligence */}
          <div className="space-y-5">

            {/* Company brief */}
            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-5">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-8 h-8 rounded-lg bg-indigo-950/50 border border-indigo-800/40 flex items-center justify-center">
                  <BookOpen size={14} className="text-indigo-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-zinc-100">Company Intelligence</h2>
                  <p className="text-xs text-zinc-600">{prep.company}</p>
                </div>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">{prep.company_brief}</p>
            </div>

            {/* Key Challenges */}
            {prep.key_challenges.length > 0 && (
              <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-amber-950/50 border border-amber-800/40 flex items-center justify-center">
                    <Target size={14} className="text-amber-400" />
                  </div>
                  <h2 className="text-sm font-semibold text-zinc-100">Key Challenges</h2>
                </div>
                <ul className="space-y-3">
                  {prep.key_challenges.map((c, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-amber-950/60 border border-amber-800/40 text-amber-400 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      <span className="text-xs text-zinc-300 leading-relaxed">{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Culture Signals */}
            {prep.culture_signals.length > 0 && (
              <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-violet-950/50 border border-violet-800/40 flex items-center justify-center">
                    <Lightbulb size={14} className="text-violet-400" />
                  </div>
                  <h2 className="text-sm font-semibold text-zinc-100">Culture Signals</h2>
                </div>
                <ul className="space-y-3">
                  {prep.culture_signals.map((c, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-violet-500 text-base leading-none shrink-0 mt-0.5">→</span>
                      <span className="text-xs text-zinc-300 leading-relaxed">{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right column — Mock Questions */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-950/50 border border-emerald-800/40 flex items-center justify-center">
                <MessageSquare size={14} className="text-emerald-400" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-zinc-100">
                  Mock Interview Questions
                </h2>
                <p className="text-xs text-zinc-600">
                  {prep.mock_questions.length} tailored questions with STAR response guides
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {prep.mock_questions.map((q, i) => (
                <QuestionItem
                  key={i}
                  question={q}
                  index={i}
                  expanded={expandedQ === i}
                  onToggle={() => toggleQuestion(i)}
                />
              ))}
            </div>

            {prep.mock_questions.length === 0 && (
              <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-8 text-center">
                <p className="text-zinc-600 text-sm">
                  No mock questions available for this application.
                </p>
              </div>
            )}

            <p className="text-xs text-zinc-700 text-center pt-2">
              Generated{" "}
              {new Date(prep.generated_at).toLocaleString("en-GB", {
                dateStyle: "medium",
                timeStyle: "short",
              })}{" "}
              · Based on sector patterns and role profile
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
