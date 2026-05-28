"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import AppNav from "@/components/AppNav";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  AlertCircle,
  CheckCircle2,
  XCircle,
  FileText,
  Download,
  Loader2,
  ChevronRight,
  Clipboard,
  Zap,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────
interface MatchResult {
  ats_score: number;
  role_title: string;
  company_name: string;
  matched_keywords: string[];
  missing_keywords: string[];
  ats_issues: string[];
  match_reasons: string[];
}

type Phase = "idle" | "analyzing" | "results" | "generating" | "generated";

// ── Radial score ring ────────────────────────────────────────────────────────
function ScoreRing({ score, animated }: { score: number; animated: boolean }) {
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const fill = animated ? (score / 100) * circ : 0;
  const color =
    score >= 80 ? "#10b981" : score >= 65 ? "#f59e0b" : "#ef4444";
  const label =
    score >= 80 ? "Strong Match" : score >= 65 ? "Decent Match" : "Weak Match";

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
          {/* track */}
          <circle
            cx="64" cy="64" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="10"
          />
          {/* fill */}
          <circle
            cx="64" cy="64" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={circ - fill}
            style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.34,1.56,0.64,1)" }}
          />
        </svg>
        {/* centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-zinc-50 leading-none">{score}</span>
          <span className="text-[10px] text-zinc-500 font-medium mt-0.5">/ 100</span>
        </div>
      </div>
      <span
        className="text-xs font-semibold px-3 py-1 rounded-full"
        style={{ background: `${color}22`, color }}
      >
        {label}
      </span>
    </div>
  );
}

// ── Keyword badge ────────────────────────────────────────────────────────────
function KeywordBadge({ label, variant }: { label: string; variant: "match" | "miss" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border",
        variant === "match"
          ? "bg-emerald-950/60 text-emerald-300 border-emerald-800/50"
          : "bg-red-950/60 text-red-300 border-red-900/50"
      )}
    >
      {variant === "match"
        ? <CheckCircle2 size={9} className="shrink-0" />
        : <XCircle size={9} className="shrink-0" />
      }
      {label}
    </span>
  );
}

// ── Markdown renderer (lightweight, no external dep) ────────────────────────
function MarkdownBlock({ md }: { md: string }) {
  const html = md
    .replace(/^## (.+)$/gm, '<h2 class="text-sm font-bold text-zinc-100 mt-5 mb-1.5 border-b border-zinc-800/60 pb-1">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 class="text-xs font-semibold text-zinc-300 mt-3 mb-1">$1</h3>')
    .replace(/^# (.+)$/gm, '<h1 class="text-base font-bold text-zinc-50 mt-2 mb-2">$1</h1>')
    .replace(/^\*\*(.+?)\*\*/gm, '<strong class="text-zinc-100">$1</strong>')
    .replace(/^> (.+)$/gm, '<blockquote class="border-l-2 border-amber-500/50 pl-3 text-amber-300/80 text-[11px] my-2">$1</blockquote>')
    .replace(/^  •  (.+)$/gm, '<li class="ml-3 text-zinc-400 text-[11px] leading-relaxed list-none before:content-[\'•\'] before:mr-2 before:text-indigo-400">$1</li>')
    .replace(/^- (.+)$/gm, '<li class="ml-3 text-zinc-400 text-[11px] leading-relaxed list-none before:content-[\'•\'] before:mr-2 before:text-indigo-400">$1</li>')
    .replace(/\n{2,}/g, '</p><p class="text-zinc-400 text-[11px] leading-relaxed my-1">')
    .replace(/^(?!<[h|b|l|p])(.+)$/gm, '<p class="text-zinc-400 text-[11px] leading-relaxed">$1</p>');

  return (
    <div
      className="prose-sm font-mono text-zinc-300 space-y-0.5"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function AnalyzePage() {
  const [jdText, setJdText] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [cvMarkdown, setCvMarkdown] = useState("");
  const [error, setError] = useState("");
  const [ringAnimated, setRingAnimated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const printRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUserId(localStorage.getItem("tapapply_user_id"));
  }, []);

  // Trigger ring animation one frame after score appears
  useEffect(() => {
    if (phase === "results" && result) {
      const t = setTimeout(() => setRingAnimated(true), 80);
      return () => clearTimeout(t);
    } else {
      setRingAnimated(false);
    }
  }, [phase, result]);

  const analyze = useCallback(async () => {
    if (!jdText.trim()) return;
    if (!userId) {
      setError("Please complete onboarding before using this feature.");
      return;
    }
    setError("");
    setPhase("analyzing");
    setResult(null);
    setCvMarkdown("");

    try {
      const res = await fetch("/api/analyze-match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, jd_text: jdText }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error((e as { error?: string }).error || "Analysis failed");
      }
      const data: MatchResult = await res.json();
      setResult(data);
      setPhase("results");
    } catch (e) {
      setError((e as Error).message);
      setPhase("idle");
    }
  }, [jdText, userId]);

  const generateCV = useCallback(async () => {
    if (!result || !userId) return;
    setPhase("generating");

    try {
      const res = await fetch("/api/generate-ats-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          jd_text: jdText,
          missing_keywords: result.missing_keywords,
        }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error((e as { error?: string }).error || "Generation failed");
      }
      const data = await res.json() as { cv_markdown: string };
      setCvMarkdown(data.cv_markdown);
      setPhase("generated");
    } catch (e) {
      setError((e as Error).message);
      setPhase("results");
    }
  }, [result, userId, jdText]);

  const handlePrint = () => {
    window.print();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(cvMarkdown).catch(() => {});
  };

  const rightPanelVisible = phase === "results" || phase === "generating" || phase === "generated";

  return (
    <>
      <style>{`
        @media print {
          body > *:not(#print-cv) { display: none !important; }
          #print-cv { display: block !important; }
        }
      `}</style>

      {/* Hidden print target */}
      <div id="print-cv" className="hidden p-8 max-w-3xl mx-auto">
        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{cvMarkdown}</pre>
      </div>

      <AppNav />

      <main className="min-h-screen bg-zinc-950 pt-6 pb-16">
        <div className="max-w-7xl mx-auto px-6">

          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Sparkles size={15} className="text-white" />
              </div>
              <h1 className="text-xl font-bold text-zinc-50">JD Match & ATS Optimizer</h1>
            </div>
            <p className="text-sm text-zinc-500 ml-10.5">
              Paste a job description · see your ATS compatibility score · generate a tailored CV in one click.
            </p>
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-2.5 bg-red-950/40 border border-red-900/50 rounded-xl px-4 py-3">
              <AlertCircle size={14} className="text-red-400 shrink-0 mt-0.5" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Two-panel layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* ── LEFT: JD Input ──────────────────────────────────────────── */}
            <div className="flex flex-col gap-4">
              <div
                className={cn(
                  "relative rounded-2xl border transition-all duration-300",
                  jdText.trim()
                    ? "border-indigo-500/40 shadow-[0_0_24px_rgba(99,102,241,0.08)]"
                    : "border-zinc-800/60"
                )}
                style={{ background: "rgba(18,18,22,0.9)", backdropFilter: "blur(12px)" }}
              >
                {/* Glassmorphism corner accent */}
                <div className="absolute top-0 left-0 w-24 h-24 rounded-tl-2xl bg-gradient-to-br from-indigo-500/8 to-transparent pointer-events-none" />

                <div className="p-4 pb-0 flex items-center gap-2">
                  <FileText size={13} className="text-indigo-400" />
                  <span className="text-xs font-semibold text-zinc-300 tracking-wide uppercase">
                    Paste Target Job Description Here
                  </span>
                  {jdText.trim() && (
                    <span className="ml-auto text-[10px] text-zinc-600">
                      {jdText.trim().split(/\s+/).length} words
                    </span>
                  )}
                </div>

                <textarea
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste the full job description here — include the role requirements, responsibilities, and any qualifications listed…"
                  className="no-base w-full h-80 resize-none bg-transparent px-4 py-3 text-xs text-zinc-300 placeholder:text-zinc-700 focus:outline-none leading-relaxed"
                />

                <div className="px-4 pb-4">
                  <button
                    onClick={analyze}
                    disabled={!jdText.trim() || phase === "analyzing"}
                    className={cn(
                      "w-full flex items-center justify-center gap-2.5 py-3 rounded-xl text-sm font-semibold transition-all",
                      "bg-gradient-to-r from-indigo-500 to-violet-600 text-white",
                      "hover:from-indigo-400 hover:to-violet-500 hover:shadow-[0_0_24px_rgba(99,102,241,0.35)]",
                      "disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none",
                      phase === "analyzing" && "animate-pulse"
                    )}
                  >
                    {phase === "analyzing" ? (
                      <><Loader2 size={15} className="animate-spin" /> Analysing match rate…</>
                    ) : (
                      <><Zap size={15} fill="white" /> Analyze Application Match Rate</>
                    )}
                  </button>
                </div>
              </div>

              {/* Tips */}
              <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 px-4 py-3 space-y-1.5">
                <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wide">How it works</p>
                {[
                  "Paste the complete JD — more text means better keyword extraction",
                  "The engine cross-references your stored CV against the JD semantically",
                  "Click generate to get a rewritten CV with missing keywords woven in",
                ].map((tip) => (
                  <div key={tip} className="flex items-start gap-2">
                    <ChevronRight size={11} className="text-indigo-400 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-zinc-500 leading-relaxed">{tip}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── RIGHT: Analytics panel ──────────────────────────────────── */}
            <div
              className={cn(
                "rounded-2xl border border-zinc-800/60 overflow-hidden transition-all duration-500",
                rightPanelVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-4 pointer-events-none"
              )}
              style={{ background: "rgba(18,18,22,0.9)", backdropFilter: "blur(12px)" }}
            >
              {/* Blurred placeholder when idle */}
              {!rightPanelVisible && (
                <div className="h-full min-h-[480px] flex items-center justify-center">
                  <div className="text-center space-y-2 opacity-30">
                    <Sparkles size={28} className="mx-auto text-indigo-400" />
                    <p className="text-xs text-zinc-500">Results will appear here</p>
                  </div>
                </div>
              )}

              {rightPanelVisible && result && phase !== "generated" && (
                <div className="p-5 space-y-5">

                  {/* Score + role */}
                  <div className="flex items-center gap-5">
                    <ScoreRing score={result.ats_score} animated={ringAnimated} />
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] text-zinc-600 uppercase tracking-wide font-semibold mb-1">ATS Compatibility Score</p>
                      {result.role_title && (
                        <p className="text-sm font-semibold text-zinc-100 truncate">{result.role_title}</p>
                      )}
                      {result.company_name && (
                        <p className="text-xs text-zinc-500 truncate">{result.company_name}</p>
                      )}
                      {result.ats_score < 65 && (
                        <p className="text-[11px] text-red-400 mt-1.5 leading-relaxed">
                          Score below 65 — likely to be filtered out by automated systems.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Keywords grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wide flex items-center gap-1">
                        <CheckCircle2 size={10} /> Matched ({result.matched_keywords.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {result.matched_keywords.slice(0, 12).map((kw) => (
                          <KeywordBadge key={kw} label={kw} variant="match" />
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-[10px] font-semibold text-red-400 uppercase tracking-wide flex items-center gap-1">
                        <XCircle size={10} /> Missing ({result.missing_keywords.length})
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {result.missing_keywords.slice(0, 12).map((kw) => (
                          <KeywordBadge key={kw} label={kw} variant="miss" />
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* ATS issues */}
                  {result.ats_issues.length > 0 && (
                    <div className="rounded-xl border border-red-900/30 bg-red-950/20 p-3 space-y-1.5">
                      <p className="text-[10px] font-semibold text-red-400 uppercase tracking-wide">Why you might get filtered</p>
                      {result.ats_issues.map((issue) => (
                        <div key={issue} className="flex items-start gap-2">
                          <AlertCircle size={10} className="text-red-400 shrink-0 mt-0.5" />
                          <p className="text-[11px] text-zinc-400 leading-relaxed">{issue}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Match reasons */}
                  {result.match_reasons.length > 0 && (
                    <div className="rounded-xl border border-emerald-900/30 bg-emerald-950/20 p-3 space-y-1.5">
                      <p className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wide">Your strengths</p>
                      {result.match_reasons.map((r) => (
                        <div key={r} className="flex items-start gap-2">
                          <CheckCircle2 size={10} className="text-emerald-400 shrink-0 mt-0.5" />
                          <p className="text-[11px] text-zinc-400 leading-relaxed">{r}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Generate CTA */}
                  <button
                    onClick={generateCV}
                    disabled={phase === "generating"}
                    className={cn(
                      "w-full flex items-center justify-center gap-2.5 py-3.5 rounded-xl text-sm font-semibold transition-all",
                      "bg-gradient-to-r from-emerald-500 to-teal-600 text-white",
                      "hover:from-emerald-400 hover:to-teal-500 hover:shadow-[0_0_28px_rgba(16,185,129,0.35)]",
                      "disabled:opacity-50 disabled:cursor-not-allowed",
                      phase === "generating" && "animate-pulse"
                    )}
                  >
                    {phase === "generating" ? (
                      <><Loader2 size={15} className="animate-spin" /> Generating tailored CV…</>
                    ) : (
                      <><Sparkles size={15} /> Instantly Generate Tailored ATS Resume</>
                    )}
                  </button>
                </div>
              )}

              {/* Generated CV panel */}
              {phase === "generated" && cvMarkdown && (
                <div className="flex flex-col h-full">
                  {/* Toolbar */}
                  <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/60 bg-zinc-900/40 shrink-0">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span className="text-xs font-semibold text-zinc-200">ATS-Optimised CV</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
                      >
                        <Clipboard size={11} /> Copy
                      </button>
                      <button
                        onClick={handlePrint}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 border border-indigo-500/30 transition-colors"
                      >
                        <Download size={11} /> Export PDF
                      </button>
                      <button
                        onClick={() => setPhase("results")}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors"
                      >
                        ← Back
                      </button>
                    </div>
                  </div>

                  {/* CV content */}
                  <div
                    ref={printRef}
                    className="flex-1 overflow-y-auto p-5 space-y-1 terminal-scroll"
                  >
                    <MarkdownBlock md={cvMarkdown} />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
