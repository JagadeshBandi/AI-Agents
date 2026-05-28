"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Zap,
  Activity,
  FileText,
  ArrowRight,
} from "lucide-react";
import AppNav from "@/components/AppNav";
import { api, type Application, type AutopilotStatus, type ApplicationStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────
interface LogEntry {
  seq: number;
  timestamp: string;
  message: string;
  type: string;
}

type StreamStatus = "connecting" | "live" | "reconnecting" | "offline";

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  submitted: "Submitted",
  reviewed: "Reviewed",
  interview_scheduled: "Interview",
  offer_extended: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  pending: "Pending",
};

const STATUS_COLORS: Record<ApplicationStatus, string> = {
  submitted: "bg-blue-950/70 text-blue-300 border-blue-800/50",
  reviewed: "bg-amber-950/70 text-amber-300 border-amber-800/50",
  interview_scheduled: "bg-violet-950/70 text-violet-300 border-violet-800/50",
  offer_extended: "bg-emerald-950/70 text-emerald-300 border-emerald-800/50",
  rejected: "bg-red-950/70 text-red-400 border-red-900/50",
  withdrawn: "bg-zinc-800/70 text-zinc-400 border-zinc-700/50",
  pending: "bg-zinc-800/70 text-zinc-400 border-zinc-700/50",
};

const LOG_TYPE_CONFIG: Record<string, { badgeClass: string; label: string; textClass: string }> = {
  activity: {
    badgeClass: "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60",
    label: "LOG",
    textClass: "text-emerald-300",
  },
  system: {
    badgeClass: "bg-zinc-800/60 text-zinc-400 border border-zinc-700/60",
    label: "SYS",
    textClass: "text-zinc-400",
  },
  error: {
    badgeClass: "bg-red-950/60 text-red-400 border border-red-800/60",
    label: "ERR",
    textClass: "text-red-300",
  },
  scan: {
    badgeClass: "bg-blue-950/60 text-blue-400 border border-blue-800/60",
    label: "SCAN",
    textClass: "text-blue-300",
  },
  found: {
    badgeClass: "bg-violet-950/60 text-violet-400 border border-violet-800/60",
    label: "FOUND",
    textClass: "text-violet-300",
  },
  sent: {
    badgeClass: "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60",
    label: "SENT",
    textClass: "text-emerald-300",
  },
};

function getLogConfig(type: string) {
  return LOG_TYPE_CONFIG[type.toLowerCase()] ?? LOG_TYPE_CONFIG["activity"];
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function formatLastActivity(ts: string | null): string {
  if (!ts) return "System idle";
  try {
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (diff < 10) return "Just now";
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  } catch {
    return "System idle";
  }
}

// ── Status badge ──────────────────────────────────────────────
function StatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium border",
        STATUS_COLORS[status] ?? STATUS_COLORS.pending
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

// ── Metric Card ───────────────────────────────────────────────
function MetricCard({
  icon: Icon,
  iconBg,
  iconColor,
  value,
  label,
  highlight,
}: {
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  value: number | string;
  label: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl p-5 flex items-center gap-4 border transition-all",
        highlight
          ? "border-amber-800/40 bg-amber-950/20"
          : "border-zinc-800/60 bg-zinc-900/50"
      )}
    >
      <div
        className={cn(
          "w-11 h-11 rounded-xl border flex items-center justify-center shrink-0",
          iconBg
        )}
      >
        <Icon size={20} className={iconColor} />
      </div>
      <div>
        <div className={cn("text-3xl font-bold tabular-nums", highlight ? "text-amber-300" : "text-zinc-50")}>
          {typeof value === "number" ? value.toLocaleString() : value}
        </div>
        <div className="text-xs text-zinc-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

// ── Autopilot Toggle ──────────────────────────────────────────
function AutopilotToggle({
  enabled,
  toggling,
  onClick,
}: {
  enabled: boolean;
  toggling: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={toggling}
      aria-label={enabled ? "Disable autopilot" : "Enable autopilot"}
      className={cn(
        "relative w-16 h-8 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:ring-offset-2 focus:ring-offset-zinc-900",
        enabled
          ? "bg-gradient-to-r from-indigo-500 to-violet-600"
          : "bg-zinc-800 border border-zinc-700/60",
        toggling && "opacity-60 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-all duration-300",
          enabled ? "left-[calc(100%-1.75rem)]" : "left-1"
        )}
      />
      {enabled && (
        <span className="absolute -inset-1 rounded-full border-2 border-indigo-400/30 animate-pulse pointer-events-none" />
      )}
    </button>
  );
}

// ── Table Skeleton ────────────────────────────────────────────
function TableSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="divide-y divide-zinc-800/40">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="px-6 py-3.5 flex items-center gap-4">
          <div className="h-3 bg-zinc-800/80 rounded w-32 animate-pulse" />
          <div className="h-3 bg-zinc-800/60 rounded w-24 animate-pulse" />
          <div className="h-3 bg-zinc-800/60 rounded w-16 animate-pulse hidden md:block" />
          <div className="h-5 bg-zinc-800/80 rounded-full w-16 animate-pulse ml-auto" />
        </div>
      ))}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────
export default function DashboardPage() {
  const router = useRouter();
  const [userId, setUserId] = useState("");
  const [missingCV, setMissingCV] = useState(false);
  const [stats, setStats] = useState<AutopilotStatus>({
    is_enabled: false,
    jobs_analyzed: 0,
    applications_placed: 0,
    actions_required: 0,
    last_activity: null,
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [toggling, setToggling] = useState(false);
  const [streamStatus, setStreamStatus] = useState<StreamStatus>("connecting");
  const [appsLoading, setAppsLoading] = useState(true);

  const logPanelRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  const logSeqRef = useRef(0);

  // Connect SSE with userId so backend can filter events
  const connectStream = useCallback((uid: string) => {
    esRef.current?.close();
    setStreamStatus("connecting");

    const es = new EventSource(`/api/logs/stream?user_id=${encodeURIComponent(uid)}`);
    esRef.current = es;

    es.onopen = () => setStreamStatus("live");

    es.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data as string) as Record<string, unknown>;

        if (data.type === "stats") {
          setStats({
            is_enabled: Boolean(data.is_enabled),
            jobs_analyzed: Number(data.jobs_analyzed ?? 0),
            applications_placed: Number(data.applications_placed ?? 0),
            actions_required: Number(data.actions_required ?? 0),
            last_activity: (data.last_activity as string | null) ?? null,
          });
        } else {
          // catches "activity", "system", "error", "scan", "found", "sent"
          logSeqRef.current += 1;
          setLogs((prev) => [
            ...prev.slice(-149),
            {
              seq: logSeqRef.current,
              timestamp: (data.timestamp as string) || new Date().toISOString(),
              message: (data.message as string) || "",
              type: (data.type as string) || "activity",
            },
          ]);
          // Refresh application list when a new one is submitted
          if ((data.message as string)?.toLowerCase().includes("submitted") ||
              (data.message as string)?.toLowerCase().includes("placed")) {
            setAppsLoading(true);
            api.applications.list(uid)
              .then((res) => setApplications((res.applications ?? []).slice(0, 10)))
              .catch(() => null)
              .finally(() => setAppsLoading(false));
          }
        }
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      setStreamStatus("reconnecting");
      es.close();
      setTimeout(() => connectStream(uid), 5000);
    };
  }, []);

  const loadApplications = useCallback(async (uid: string) => {
    setAppsLoading(true);
    try {
      const res = await api.applications.list(uid);
      setApplications((res.applications ?? []).slice(0, 10));
    } catch {
      // silently fail
    } finally {
      setAppsLoading(false);
    }
  }, []);

  // Fetch autopilot status from API (initial + after toggle)
  const syncAutopilotStatus = useCallback(async () => {
    try {
      const s = await api.autopilot.status();
      setStats(s);
    } catch {
      // silently fail
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
    syncAutopilotStatus();
    connectStream(uid);

    // Check whether user has a CV / profile built
    fetch(`/api/profile/${encodeURIComponent(uid)}`)
      .then((r) => r.json())
      .then((d: unknown) => {
        const data = d as Record<string, unknown>;
        // If no cv_filename and onboarding_path is still default, prompt them
        if (!data.cv_filename && !data.onboarding_path) setMissingCV(true);
      })
      .catch(() => setMissingCV(true));

    return () => {
      esRef.current?.close();
    };
  }, [connectStream, loadApplications, syncAutopilotStatus, router]);

  // Auto-scroll log panel on new entries
  useEffect(() => {
    if (logPanelRef.current) {
      logPanelRef.current.scrollTop = logPanelRef.current.scrollHeight;
    }
  }, [logs]);

  const toggleAutopilot = useCallback(async () => {
    if (!userId || toggling) return;
    setToggling(true);
    try {
      if (stats.is_enabled) {
        await api.autopilot.disable(userId);
      } else {
        await api.autopilot.enable(userId);
      }
      await syncAutopilotStatus();
    } catch {
      // silently fail
    } finally {
      setToggling(false);
    }
  }, [userId, toggling, stats.is_enabled, syncAutopilotStatus]);

  const streamBadge = {
    connecting: "bg-amber-950/60 text-amber-400 border border-amber-800/60",
    live: "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60",
    reconnecting: "bg-red-950/60 text-red-400 border border-red-800/60",
    offline: "bg-zinc-800/60 text-zinc-400 border border-zinc-700/60",
  }[streamStatus];

  const streamDot = {
    connecting: "bg-amber-400 animate-pulse",
    live: "bg-emerald-400 animate-pulse",
    reconnecting: "bg-red-400 animate-pulse",
    offline: "bg-zinc-500",
  }[streamStatus];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <AppNav />

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

        {/* ── CV safe-path banner ───────────────────────────── */}
        {missingCV && (
          <div className="flex items-center justify-between gap-4 bg-indigo-950/40 border border-indigo-700/50 rounded-2xl px-5 py-4 animate-slide-up">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-900/60 border border-indigo-700/40 flex items-center justify-center shrink-0">
                <FileText size={16} className="text-indigo-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-zinc-100">Complete your profile to unlock autopilot</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Upload your CV or fill in the profile form — takes under 2 minutes.
                </p>
              </div>
            </div>
            <a
              href="/onboarding"
              className="shrink-0 flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              Set up profile <ArrowRight size={12} />
            </a>
          </div>
        )}

        {/* ── Metric Cards ─────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricCard
            icon={BarChart3}
            iconBg="bg-blue-950/50 border-blue-800/40"
            iconColor="text-blue-400"
            value={stats.jobs_analyzed}
            label="Total Scanned"
          />
          <MetricCard
            icon={CheckCircle2}
            iconBg="bg-emerald-950/50 border-emerald-800/40"
            iconColor="text-emerald-400"
            value={stats.applications_placed}
            label="Applications Sent"
          />
          <MetricCard
            icon={AlertTriangle}
            iconBg={stats.actions_required > 0 ? "bg-amber-950/50 border-amber-800/40" : "bg-zinc-800/50 border-zinc-700/40"}
            iconColor={cn(stats.actions_required > 0 ? "text-amber-400 animate-pulse" : "text-zinc-500")}
            value={stats.actions_required}
            label="Review Required"
            highlight={stats.actions_required > 0}
          />
        </div>

        {/* ── Middle row ───────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* Autopilot control panel */}
          <div className="lg:col-span-2 bg-zinc-900/60 border border-zinc-800/60 rounded-2xl p-6 flex flex-col gap-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center shrink-0">
                <Zap size={16} className="text-indigo-400" fill="currentColor" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-zinc-50">Autopilot Engine</h2>
                <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">
                  Discovers and applies to roles automatically.
                </p>
              </div>
            </div>

            {/* Toggle row */}
            <div
              className={cn(
                "flex items-center justify-between p-4 rounded-xl border transition-all",
                stats.is_enabled
                  ? "bg-indigo-950/20 border-indigo-800/40"
                  : "bg-zinc-950/60 border-zinc-800/40"
              )}
            >
              <div className="flex flex-col gap-0.5">
                <span
                  className={cn(
                    "text-sm font-semibold transition-colors",
                    stats.is_enabled ? "text-emerald-400" : "text-zinc-400"
                  )}
                >
                  {toggling
                    ? "Updating..."
                    : stats.is_enabled
                    ? "Active — Searching"
                    : "Paused"}
                </span>
                <span className="text-xs text-zinc-600">
                  {stats.is_enabled
                    ? formatLastActivity(stats.last_activity)
                    : "Click to activate"}
                </span>
              </div>
              <AutopilotToggle
                enabled={stats.is_enabled}
                toggling={toggling}
                onClick={toggleAutopilot}
              />
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-zinc-950/60 border border-zinc-800/40 rounded-xl p-3 text-center">
                <div className="text-lg font-bold text-zinc-200 tabular-nums">{stats.jobs_analyzed}</div>
                <div className="text-[10px] text-zinc-600 mt-0.5">Jobs Scanned</div>
              </div>
              <div className="bg-zinc-950/60 border border-zinc-800/40 rounded-xl p-3 text-center">
                <div className="text-lg font-bold text-zinc-200 tabular-nums">{stats.applications_placed}</div>
                <div className="text-[10px] text-zinc-600 mt-0.5">Applied</div>
              </div>
            </div>

            {/* Sub-info */}
            <div className="space-y-2 border-t border-zinc-800/60 pt-4">
              {[
                { label: "Cycle interval", value: "8 seconds" },
                { label: "Mode", value: "Autonomous" },
                {
                  label: "Stream",
                  value: (
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md border text-[10px] font-medium",
                        streamBadge
                      )}
                    >
                      <span className={cn("w-1.5 h-1.5 rounded-full", streamDot)} />
                      {streamStatus === "live" ? "Live" : streamStatus === "connecting" ? "Connecting" : "Reconnecting"}
                    </span>
                  ),
                },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between text-xs">
                  <span className="text-zinc-600">{row.label}</span>
                  {typeof row.value === "string" ? (
                    <span className="text-zinc-300 font-medium">{row.value}</span>
                  ) : (
                    row.value
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Live Activity Console */}
          <div className="lg:col-span-3 bg-zinc-950 border border-zinc-800/60 rounded-2xl flex flex-col overflow-hidden min-h-[360px]">
            {/* Console chrome */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/60 bg-zinc-900/40 shrink-0">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-500/70" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/70" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/70" />
                </div>
                <div className="flex items-center gap-2">
                  <Activity size={12} className="text-zinc-500" />
                  <span className="text-xs font-medium text-zinc-400">Live Activity</span>
                </div>
              </div>
              <span
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium",
                  streamBadge
                )}
              >
                <span className={cn("w-1.5 h-1.5 rounded-full", streamDot)} />
                {streamStatus}
              </span>
            </div>

            {/* Log content */}
            <div
              ref={logPanelRef}
              className="flex-1 overflow-y-auto p-4 font-mono space-y-0.5 terminal-scroll"
            >
              {logs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 py-12">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center",
                      stats.is_enabled
                        ? "bg-indigo-950/60 border border-indigo-800/40"
                        : "bg-zinc-900 border border-zinc-800/40"
                    )}
                  >
                    <Activity
                      size={18}
                      className={stats.is_enabled ? "text-indigo-400 animate-pulse" : "text-zinc-600"}
                    />
                  </div>
                  <p className="text-zinc-600 text-xs text-center">
                    {stats.is_enabled
                      ? "Waiting for first activity..."
                      : "Activate autopilot to begin scanning for roles."}
                  </p>
                </div>
              ) : (
                logs.map((log) => {
                  const cfg = getLogConfig(log.type);
                  return (
                    <div
                      key={log.seq}
                      className="flex items-start gap-2 text-xs py-0.5 animate-console-in"
                    >
                      <span className="text-zinc-700 shrink-0 tabular-nums">
                        [{formatTimestamp(log.timestamp)}]
                      </span>
                      <span
                        className={cn(
                          "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0",
                          cfg.badgeClass
                        )}
                      >
                        {cfg.label}
                      </span>
                      <span className={cn("leading-relaxed break-all", cfg.textClass)}>
                        {log.message}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* ── Recent Applications ───────────────────────────── */}
        <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/60">
            <h2 className="text-sm font-semibold text-zinc-100">Recent Applications</h2>
            <div className="flex items-center gap-3">
              <button
                onClick={() => loadApplications(userId)}
                disabled={appsLoading}
                className="p-1.5 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors disabled:opacity-40"
                aria-label="Refresh applications"
              >
                <RefreshCw size={13} className={appsLoading ? "animate-spin" : ""} />
              </button>
              <Link
                href="/track"
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
              >
                View all <ExternalLink size={11} />
              </Link>
            </div>
          </div>

          {appsLoading ? (
            <TableSkeleton rows={4} />
          ) : applications.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <div className="flex justify-center">
                <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800/40 flex items-center justify-center">
                  <CheckCircle2 size={22} className="text-zinc-700" />
                </div>
              </div>
              <div>
                <p className="text-zinc-500 text-sm font-medium">No applications yet</p>
                <p className="text-zinc-700 text-xs mt-1">
                  {stats.is_enabled
                    ? "Autopilot is running — applications will appear shortly."
                    : "Activate autopilot above to start applying automatically."}
                </p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-zinc-600 border-b border-zinc-800/60 bg-zinc-900/30">
                    <th className="px-6 py-3 font-medium">Role</th>
                    <th className="px-6 py-3 font-medium">Company</th>
                    <th className="px-6 py-3 font-medium hidden md:table-cell">Location</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium hidden sm:table-cell">Applied</th>
                    <th className="px-6 py-3 font-medium text-right">Prep</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40">
                  {applications.map((app) => (
                    <tr
                      key={app.id}
                      className="hover:bg-zinc-800/20 transition-colors group"
                    >
                      <td className="px-6 py-3.5 font-medium text-zinc-200 max-w-[180px] truncate">
                        {app.job_title}
                      </td>
                      <td className="px-6 py-3.5 text-zinc-400">{app.company}</td>
                      <td className="px-6 py-3.5 text-zinc-500 text-xs hidden md:table-cell">
                        {app.location || "—"}
                      </td>
                      <td className="px-6 py-3.5">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="px-6 py-3.5 text-zinc-600 text-xs hidden sm:table-cell">
                        {app.submitted_at
                          ? new Date(app.submitted_at).toLocaleDateString("en-GB", {
                              day: "2-digit",
                              month: "short",
                            })
                          : "—"}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        {app.status === "interview_scheduled" ? (
                          <Link
                            href={`/interview/${app.id}`}
                            className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors font-medium"
                          >
                            Prep <ExternalLink size={10} />
                          </Link>
                        ) : (
                          <Link
                            href={`/interview/${app.id}`}
                            className="inline-flex items-center gap-1 text-xs text-zinc-600 hover:text-zinc-400 transition-colors opacity-0 group-hover:opacity-100"
                          >
                            Generate
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
      </div>
    </div>
  );
}
