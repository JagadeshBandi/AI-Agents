"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, ExternalLink, ClipboardList } from "lucide-react";
import AppNav from "@/components/AppNav";
import { api, type Application, type ApplicationStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

// ── Constants ─────────────────────────────────────────────────
const ALL_STATUSES: ApplicationStatus[] = [
  "submitted",
  "reviewed",
  "interview_scheduled",
  "offer_extended",
  "rejected",
  "withdrawn",
  "pending",
];

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  submitted: "Submitted",
  reviewed: "Reviewed",
  interview_scheduled: "Interview Scheduled",
  offer_extended: "Offer Extended",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  pending: "Pending",
};

const PIPELINE_CARDS = [
  {
    key: "submitted" as ApplicationStatus,
    label: "Submitted",
    border: "border-blue-800/40",
    bg: "bg-blue-950/20",
    text: "text-blue-300",
    count_bg: "bg-blue-950/60",
  },
  {
    key: "reviewed" as ApplicationStatus,
    label: "Reviewed",
    border: "border-amber-800/40",
    bg: "bg-amber-950/20",
    text: "text-amber-300",
    count_bg: "bg-amber-950/60",
  },
  {
    key: "interview_scheduled" as ApplicationStatus,
    label: "Interview",
    border: "border-violet-800/40",
    bg: "bg-violet-950/20",
    text: "text-violet-300",
    count_bg: "bg-violet-950/60",
  },
  {
    key: "offer_extended" as ApplicationStatus,
    label: "Offer",
    border: "border-emerald-800/40",
    bg: "bg-emerald-950/20",
    text: "text-emerald-300",
    count_bg: "bg-emerald-950/60",
  },
];

const FILTER_TABS = [
  { value: "all", label: "All" },
  ...ALL_STATUSES.map((s) => ({ value: s, label: STATUS_LABELS[s] })),
];

// ── Status Badge ──────────────────────────────────────────────
function StatusBadge({ status }: { status: ApplicationStatus }) {
  const map: Record<ApplicationStatus, string> = {
    submitted: "bg-blue-950/70 text-blue-300 border-blue-800/50",
    reviewed: "bg-amber-950/70 text-amber-300 border-amber-800/50",
    interview_scheduled: "bg-violet-950/70 text-violet-300 border-violet-800/50",
    offer_extended: "bg-emerald-950/70 text-emerald-300 border-emerald-800/50",
    rejected: "bg-red-950/70 text-red-400 border-red-900/50",
    withdrawn: "bg-zinc-800/70 text-zinc-400 border-zinc-700/50",
    pending: "bg-zinc-800/70 text-zinc-400 border-zinc-700/50",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border",
        map[status] ?? map.pending
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

// ── Skeleton loader ───────────────────────────────────────────
function TableSkeleton() {
  return (
    <div className="divide-y divide-zinc-800/40">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="px-6 py-4 flex items-center gap-4">
          <div className="h-3.5 bg-zinc-800/80 rounded-md w-40 animate-pulse" />
          <div className="h-3.5 bg-zinc-800/60 rounded-md w-28 animate-pulse" />
          <div className="h-3.5 bg-zinc-800/60 rounded-md w-20 hidden md:block animate-pulse" />
          <div className="h-5 bg-zinc-800/80 rounded-full w-20 animate-pulse" />
        </div>
      ))}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────
export default function TrackPage() {
  const router = useRouter();
  const [userId, setUserId] = useState("");
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | ApplicationStatus>("all");

  const loadApplications = useCallback(async (uid: string) => {
    setLoading(true);
    try {
      const res = await api.applications.list(uid);
      setApplications(res.applications ?? []);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const uid = localStorage.getItem("tapapply_user_id");
    if (!uid) {
      router.push("/onboarding");
      return;
    }
    setUserId(uid);
    loadApplications(uid);
  }, [router, loadApplications]);

  const updateStatus = useCallback(
    async (appId: string, newStatus: ApplicationStatus) => {
      setUpdating(appId);
      try {
        await api.applications.updateStatus(appId, newStatus);
        setApplications((prev) =>
          prev.map((a) => (a.id === appId ? { ...a, status: newStatus } : a))
        );
      } catch {
        // silently fail
      } finally {
        setUpdating(null);
      }
    },
    []
  );

  const filtered =
    filter === "all" ? applications : applications.filter((a) => a.status === filter);

  const pipelineCounts = PIPELINE_CARDS.reduce<Record<string, number>>(
    (acc, p) => {
      acc[p.key] = applications.filter((a) => a.status === p.key).length;
      return acc;
    },
    {}
  );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <AppNav />

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

        {/* Page header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="p-2 rounded-xl text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors"
            >
              <ArrowLeft size={16} />
            </Link>
            <div>
              <h1 className="text-lg font-bold text-zinc-50 flex items-center gap-2">
                <ClipboardList size={18} className="text-indigo-400" />
                Application Ledger
              </h1>
              <p className="text-xs text-zinc-500 mt-0.5">
                {applications.length} total applications tracked
              </p>
            </div>
          </div>
          <button
            onClick={() => loadApplications(userId)}
            className="p-2 rounded-xl text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors"
            aria-label="Refresh"
          >
            <RefreshCw size={15} />
          </button>
        </div>

        {/* Pipeline summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {PIPELINE_CARDS.map((p) => (
            <button
              key={p.key}
              onClick={() => setFilter(filter === p.key ? "all" : p.key)}
              className={cn(
                "border rounded-2xl p-4 text-left transition-all hover:scale-[1.01] active:scale-[0.99]",
                p.border,
                p.bg,
                filter === p.key && "ring-1 ring-inset",
                filter === p.key && p.border.replace("border-", "ring-")
              )}
            >
              <div className={cn("text-3xl font-bold tabular-nums", p.text)}>
                {pipelineCounts[p.key] ?? 0}
              </div>
              <div className="text-xs text-zinc-500 mt-1">{p.label}</div>
            </button>
          ))}
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setFilter(tab.value as "all" | ApplicationStatus)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                filter === tab.value
                  ? "bg-indigo-600 text-white shadow-glow-indigo"
                  : "bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 border border-zinc-700/40"
              )}
            >
              {tab.label}
              {tab.value !== "all" && (
                <span className="ml-1 opacity-60">
                  ({applications.filter((a) => a.status === tab.value).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Applications data grid */}
        <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl overflow-hidden">
          {loading ? (
            <TableSkeleton />
          ) : filtered.length === 0 ? (
            <div className="py-16 text-center">
              <div className="text-zinc-700 text-sm">
                {filter === "all"
                  ? "No applications yet. Activate autopilot to get started."
                  : `No applications with status "${STATUS_LABELS[filter as ApplicationStatus] ?? filter}".`}
              </div>
              {filter !== "all" && (
                <button
                  onClick={() => setFilter("all")}
                  className="mt-3 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Clear filter →
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-zinc-600 border-b border-zinc-800/60 bg-zinc-900/30">
                    <th className="px-6 py-3.5 font-medium">Company</th>
                    <th className="px-6 py-3.5 font-medium">Role</th>
                    <th className="px-6 py-3.5 font-medium hidden lg:table-cell">Region</th>
                    <th className="px-6 py-3.5 font-medium hidden md:table-cell">Date</th>
                    <th className="px-6 py-3.5 font-medium">Status</th>
                    <th className="px-6 py-3.5 font-medium">Update Status</th>
                    <th className="px-6 py-3.5 font-medium text-right">Interview Prep</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40">
                  {filtered.map((app) => (
                    <tr
                      key={app.id}
                      className="hover:bg-zinc-800/20 transition-colors group"
                    >
                      <td className="px-6 py-4 font-medium text-zinc-100">
                        {app.company}
                      </td>
                      <td className="px-6 py-4 text-zinc-300">{app.job_title}</td>
                      <td className="px-6 py-4 text-zinc-500 text-xs hidden lg:table-cell">
                        {app.location || "—"}
                      </td>
                      <td className="px-6 py-4 text-zinc-500 text-xs hidden md:table-cell">
                        {app.submitted_at
                          ? new Date(app.submitted_at).toLocaleDateString("en-GB", {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            })
                          : "—"}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="px-6 py-4">
                        <div className="relative">
                          <select
                            value={app.status}
                            disabled={updating === app.id}
                            onChange={(e) =>
                              updateStatus(app.id, e.target.value as ApplicationStatus)
                            }
                            className={cn(
                              "appearance-none text-xs py-1.5 pl-2.5 pr-7 rounded-lg border border-zinc-700/60 bg-zinc-900 text-zinc-300 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all",
                              updating === app.id && "opacity-50 cursor-not-allowed"
                            )}
                          >
                            {ALL_STATUSES.map((s) => (
                              <option key={s} value={s} className="bg-zinc-900">
                                {STATUS_LABELS[s]}
                              </option>
                            ))}
                          </select>
                          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none text-[10px]">
                            ▾
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {app.status === "interview_scheduled" ? (
                          <Link
                            href={`/interview/${app.id}`}
                            className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 font-medium transition-colors"
                          >
                            Prep <ExternalLink size={10} />
                          </Link>
                        ) : (
                          <Link
                            href={`/interview/${app.id}`}
                            className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-indigo-400 transition-colors opacity-0 group-hover:opacity-100"
                          >
                            Generate prep
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer count */}
        {!loading && filtered.length > 0 && (
          <p className="text-xs text-zinc-700 text-center">
            Showing {filtered.length} of {applications.length} applications
          </p>
        )}
      </div>
    </div>
  );
}
