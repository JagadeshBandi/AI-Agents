"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronRight,
  ChevronLeft,
  CloudUpload,
  CheckCircle2,
  X,
  Plus,
  Trash2,
  Upload,
  Pencil,
  Code2,
  TrendingUp,
  HeartPulse,
  Megaphone,
  Settings,
  ChevronDown,
  Zap,
  Phone,
} from "lucide-react";
import { api, type ManualProfileRequest, type ExperienceEntry, type EducationEntry } from "@/lib/api";
import { cn } from "@/lib/utils";
import AutomationBackground from "@/components/AutomationBackground";

// ── Phone dial codes ──────────────────────────────────────────
const DIAL_CODES = [
  { code: "+44",  flag: "🇬🇧", name: "United Kingdom",  key: "UK" },
  { code: "+1",   flag: "🇺🇸", name: "United States",   key: "USA" },
  { code: "+1",   flag: "🇨🇦", name: "Canada",          key: "CANADA" },
  { code: "+61",  flag: "🇦🇺", name: "Australia",       key: "AUSTRALIA" },
  { code: "+64",  flag: "🇳🇿", name: "New Zealand",     key: "NEW_ZEALAND" },
  { code: "+49",  flag: "🇩🇪", name: "Germany",         key: "GERMANY" },
  { code: "+33",  flag: "🇫🇷", name: "France",          key: "FRANCE" },
  { code: "+31",  flag: "🇳🇱", name: "Netherlands",     key: "NETHERLANDS" },
  { code: "+353", flag: "🇮🇪", name: "Ireland",         key: "IRELAND" },
  { code: "+34",  flag: "🇪🇸", name: "Spain",           key: "SPAIN" },
  { code: "+91",  flag: "🇮🇳", name: "India",           key: "" },
  { code: "+86",  flag: "🇨🇳", name: "China",           key: "" },
  { code: "+81",  flag: "🇯🇵", name: "Japan",           key: "" },
  { code: "+82",  flag: "🇰🇷", name: "South Korea",     key: "" },
  { code: "+55",  flag: "🇧🇷", name: "Brazil",          key: "" },
  { code: "+27",  flag: "🇿🇦", name: "South Africa",    key: "" },
  { code: "+971", flag: "🇦🇪", name: "UAE",             key: "" },
  { code: "+65",  flag: "🇸🇬", name: "Singapore",       key: "" },
  { code: "+48",  flag: "🇵🇱", name: "Poland",          key: "" },
  { code: "+46",  flag: "🇸🇪", name: "Sweden",          key: "" },
];

const COUNTRY_TO_DIAL: Record<string, string> = {
  UK: "+44",
  USA: "+1",
  CANADA: "+1",
  AUSTRALIA: "+61",
  NEW_ZEALAND: "+64",
  GERMANY: "+49",
  FRANCE: "+33",
  NETHERLANDS: "+31",
  IRELAND: "+353",
  SPAIN: "+34",
};

// ── Countries ─────────────────────────────────────────────────
const COUNTRIES = [
  {
    value: "UK",
    label: "United Kingdom",
    flag: "🇬🇧",
    platforms: [
      { name: "Reed",       color: "bg-red-900/50 text-red-300 border-red-800/50" },
      { name: "TotalJobs",  color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
      { name: "CWJobs",     color: "bg-purple-900/50 text-purple-300 border-purple-800/50" },
      { name: "CV-Library", color: "bg-amber-900/50 text-amber-300 border-amber-800/50" },
    ],
  },
  {
    value: "USA",
    label: "United States",
    flag: "🇺🇸",
    platforms: [
      { name: "Indeed",    color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
      { name: "Dice",      color: "bg-orange-900/50 text-orange-300 border-orange-800/50" },
      { name: "LinkedIn",  color: "bg-sky-900/50 text-sky-300 border-sky-800/50" },
      { name: "Glassdoor", color: "bg-emerald-900/50 text-emerald-300 border-emerald-800/50" },
    ],
  },
  {
    value: "CANADA",
    label: "Canada",
    flag: "🇨🇦",
    platforms: [
      { name: "Indeed CA",  color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
      { name: "Monster CA", color: "bg-purple-900/50 text-purple-300 border-purple-800/50" },
      { name: "Workopolis", color: "bg-orange-900/50 text-orange-300 border-orange-800/50" },
    ],
  },
  {
    value: "AUSTRALIA",
    label: "Australia",
    flag: "🇦🇺",
    platforms: [
      { name: "SEEK",     color: "bg-violet-900/50 text-violet-300 border-violet-800/50" },
      { name: "Indeed AU", color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
    ],
  },
  {
    value: "NEW_ZEALAND",
    label: "New Zealand",
    flag: "🇳🇿",
    platforms: [
      { name: "SEEK NZ", color: "bg-violet-900/50 text-violet-300 border-violet-800/50" },
      { name: "TradeMe",  color: "bg-teal-900/50 text-teal-300 border-teal-800/50" },
    ],
  },
  {
    value: "GERMANY",
    label: "Germany",
    flag: "🇩🇪",
    platforms: [
      { name: "StepStone", color: "bg-orange-900/50 text-orange-300 border-orange-800/50" },
      { name: "Xing",      color: "bg-emerald-900/50 text-emerald-300 border-emerald-800/50" },
      { name: "Indeed DE", color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
    ],
  },
  {
    value: "FRANCE",
    label: "France",
    flag: "🇫🇷",
    platforms: [
      { name: "Welcome TTJ", color: "bg-rose-900/50 text-rose-300 border-rose-800/50" },
      { name: "APEC",        color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
      { name: "Cadremploi",  color: "bg-amber-900/50 text-amber-300 border-amber-800/50" },
    ],
  },
  {
    value: "NETHERLANDS",
    label: "Netherlands",
    flag: "🇳🇱",
    platforms: [
      { name: "Jobbird",     color: "bg-teal-900/50 text-teal-300 border-teal-800/50" },
      { name: "Intermediair", color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
    ],
  },
  {
    value: "IRELAND",
    label: "Ireland",
    flag: "🇮🇪",
    platforms: [
      { name: "IrishJobs", color: "bg-emerald-900/50 text-emerald-300 border-emerald-800/50" },
      { name: "Jobs.ie",   color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
    ],
  },
  {
    value: "SPAIN",
    label: "Spain",
    flag: "🇪🇸",
    platforms: [
      { name: "InfoJobs",    color: "bg-indigo-900/50 text-indigo-300 border-indigo-800/50" },
      { name: "Tecnoempleo", color: "bg-blue-900/50 text-blue-300 border-blue-800/50" },
    ],
  },
] as const;

const SECTORS = [
  { value: "Tech & Software",        icon: Code2,      color: "text-indigo-400",  bg: "bg-indigo-950/40",  desc: "Software · Data · Infrastructure · Product" },
  { value: "Finance & Banking",      icon: TrendingUp,  color: "text-emerald-400", bg: "bg-emerald-950/40", desc: "Investment · Risk · Advisory · Accounting" },
  { value: "Healthcare & Medical",   icon: HeartPulse,  color: "text-rose-400",    bg: "bg-rose-950/40",    desc: "Clinical · Research · Pharma · MedTech" },
  { value: "Marketing & Creative",   icon: Megaphone,   color: "text-amber-400",   bg: "bg-amber-950/40",   desc: "Brand · Performance · Content · Creative" },
  { value: "Engineering & Operations", icon: Settings,  color: "text-blue-400",    bg: "bg-blue-950/40",    desc: "Process · Manufacturing · Supply Chain" },
] as const;

const TONES = [
  { value: "professional",   label: "Professional" },
  { value: "executive",      label: "Executive" },
  { value: "conversational", label: "Conversational" },
] as const;

const EXP_LEVELS = [
  { value: "junior",    label: "Junior / Graduate" },
  { value: "mid",       label: "Mid-level" },
  { value: "senior",    label: "Senior" },
  { value: "executive", label: "Executive / Director" },
] as const;

// ── Types ─────────────────────────────────────────────────────
type Step = 1 | 2 | 3;

interface WorkExp {
  title: string;
  company: string;
  location: string;
  start: string;
  end: string;
  bullets: string;
}

interface EduEntry {
  degree: string;
  institution: string;
  year: string;
  honours: string;
}

// ── Shared class strings ──────────────────────────────────────
const inputCls =
  "no-base w-full rounded-xl border border-zinc-700/60 bg-zinc-900 px-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all";

const selectCls =
  "no-base w-full rounded-xl border border-zinc-700/60 bg-zinc-900 px-3.5 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all appearance-none";

// ── Progress Indicator ────────────────────────────────────────
function StepIndicator({ current }: { current: Step }) {
  const labels = ["Region", "Sector", "Profile"];
  return (
    <div className="flex items-center gap-2 justify-center mb-10">
      {([1, 2, 3] as Step[]).map((s, i) => (
        <div key={s} className="flex items-center gap-2">
          <div className="flex flex-col items-center gap-1.5">
            <div
              className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all duration-300",
                s < current
                  ? "bg-indigo-600 border-indigo-600 text-white"
                  : s === current
                  ? "bg-indigo-500/20 border-indigo-500 text-indigo-400"
                  : "bg-zinc-900 border-zinc-700 text-zinc-600"
              )}
            >
              {s < current ? <CheckCircle2 size={14} /> : s}
            </div>
            <span className={cn("text-[10px] font-medium hidden sm:block",
              s === current ? "text-indigo-400" : "text-zinc-600"
            )}>{labels[i]}</span>
          </div>
          {s < 3 && (
            <div className={cn("h-0.5 w-10 rounded-full transition-all duration-500 mb-4",
              s < current ? "bg-indigo-600" : "bg-zinc-800"
            )} />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Field Label ───────────────────────────────────────────────
function FieldLabel({ children, required }: { children: React.ReactNode; required?: boolean }) {
  return (
    <label className="block text-xs font-medium text-zinc-400 mb-1.5 tracking-wide">
      {children}
      {required && <span className="text-indigo-400 ml-0.5">*</span>}
    </label>
  );
}

// ── Phone Input with dial-code selector ──────────────────────
function PhoneInput({
  dialCode,
  number,
  sector,
  onDialChange,
  onNumberChange,
}: {
  dialCode: string;
  number: string;
  sector: string;
  onDialChange: (code: string) => void;
  onNumberChange: (n: string) => void;
}) {
  const selected = DIAL_CODES.find((d) => d.code === dialCode) ?? DIAL_CODES[0];
  return (
    <div className="flex gap-0 rounded-xl border border-zinc-700/60 bg-zinc-900 overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500/50 focus-within:border-indigo-500/50 transition-all">
      {/* Dial code picker */}
      <div className="relative flex-shrink-0 border-r border-zinc-700/60">
        {/* Spacer — invisible, sets container width, never rendered visually */}
        <span className="invisible text-sm pl-3 pr-7 py-2.5 inline-flex items-center gap-1.5" aria-hidden="true">
          <span className="text-base leading-none">{selected.flag}</span>
          <span>{selected.code}</span>
        </span>
        {/* Visual overlay — sole source of flag + code display */}
        <div className="absolute inset-0 flex items-center gap-1.5 pl-3 pr-6 pointer-events-none">
          <span className="text-base leading-none">{selected.flag}</span>
          <span className="text-sm text-zinc-300 font-medium">{selected.code}</span>
        </div>
        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
          <ChevronDown size={11} className="text-zinc-500" />
        </div>
        {/* Interaction layer — opacity-0, sits on top, handles all clicks */}
        <select
          value={dialCode}
          onChange={(e) => onDialChange(e.target.value)}
          className="no-base absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          aria-label="Country dial code"
        >
          {DIAL_CODES.map((d, i) => (
            <option key={`${d.code}-${i}`} value={d.code}>
              {d.flag} {d.code} ({d.name})
            </option>
          ))}
        </select>
      </div>
      {/* Phone number */}
      <div className="flex items-center flex-1 relative">
        <Phone size={13} className="absolute left-3 text-zinc-600 pointer-events-none" />
        <input
          type="tel"
          className="no-base w-full bg-transparent pl-8 pr-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none"
          placeholder="7700 000000"
          value={number}
          onChange={(e) => onNumberChange(e.target.value)}
          data-field="phone"
          data-sector={sector}
        />
      </div>
    </div>
  );
}

// ── Accordion section ─────────────────────────────────────────
function AccordionSection({
  title,
  children,
  defaultOpen = false,
  hasData = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  hasData?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-zinc-800/60 rounded-xl overflow-hidden">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3.5 bg-zinc-900/60 hover:bg-zinc-800/40 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-center gap-2">
          {hasData && <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />}
          <span className="text-sm font-medium text-zinc-200">{title}</span>
        </div>
        <ChevronDown
          size={15}
          className={cn("text-zinc-500 transition-transform duration-200", open && "rotate-180")}
        />
      </button>
      {open && <div className="px-4 pb-4 pt-3 bg-zinc-950/40 space-y-3">{children}</div>}
    </div>
  );
}

// ── Main Onboarding ───────────────────────────────────────────
export default function OnboardingPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>(1);
  const [userId, setUserId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Step 1
  const [country, setCountry] = useState("");

  // Step 2
  const [sector, setSector] = useState("");

  // Step 3 – Upload panel
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [linkedin, setLinkedin] = useState("");
  const [github, setGithub] = useState("");
  const [tone, setTone] = useState("professional");

  // Step 3 – Manual panel
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [dialCode, setDialCode] = useState("+44");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [location, setLocation] = useState("");
  const [summary, setSummary] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [targetLevel, setTargetLevel] = useState("mid");
  const [techSkills, setTechSkills] = useState("");
  const [softSkills, setSoftSkills] = useState("");
  const [certs, setCerts] = useState("");
  const [experience, setExperience] = useState<WorkExp[]>([
    { title: "", company: "", location: "", start: "", end: "", bullets: "" },
  ]);
  const [education, setEducation] = useState<EduEntry[]>([
    { degree: "", institution: "", year: "", honours: "" },
  ]);

  // When country is selected, auto-set dial code
  const handleCountrySelect = useCallback(
    async (val: string) => {
      setCountry(val);
      setError("");
      setLoading(true);
      // Auto-select the matching dial code
      const defaultDial = COUNTRY_TO_DIAL[val];
      if (defaultDial) setDialCode(defaultDial);
      try {
        const res = await api.onboarding.step1(val, userId || undefined);
        setUserId(res.user_id);
        localStorage.setItem("tapapply_user_id", res.user_id);
        setStep(2);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to save country");
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  const handleSectorContinue = useCallback(async () => {
    if (!sector || !userId) return;
    setError("");
    setLoading(true);
    try {
      await api.onboarding.step2(userId, sector);
      setStep(3);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save sector");
    } finally {
      setLoading(false);
    }
  }, [sector, userId]);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setCvFile(f);
  };

  const canContinue = cvFile !== null || (fullName.trim() !== "" && email.trim() !== "");

  const handleStep3Submit = useCallback(async () => {
    if (!userId || !canContinue) return;
    setError("");
    setLoading(true);

    try {
      const promises: Promise<unknown>[] = [];

      if (cvFile) {
        promises.push(
          api.onboarding.uploadCV(userId, cvFile, tone, linkedin || undefined, github || undefined)
        );
      }

      if (fullName.trim() && email.trim()) {
        const combinedPhone = phoneNumber.trim()
          ? `${dialCode} ${phoneNumber.trim()}`
          : undefined;

        const expEntries: ExperienceEntry[] = experience
          .filter((e) => e.title && e.company)
          .map((e) => ({
            title: e.title,
            company: e.company,
            location: e.location || undefined,
            start: e.start || undefined,
            end: e.end || undefined,
            bullets: e.bullets || undefined,
            achievements: e.bullets
              ? e.bullets.split("\n").map((s) => s.trim()).filter(Boolean)
              : undefined,
          }));

        const eduEntries: EducationEntry[] = education
          .filter((e) => e.degree && e.institution)
          .map((e) => ({
            degree: e.degree,
            institution: e.institution,
            year: e.year || undefined,
            honours: e.honours || undefined,
          }));

        const payload: ManualProfileRequest = {
          user_id: userId,
          full_name: fullName,
          email,
          phone: combinedPhone,
          location: location || undefined,
          professional_summary: summary || undefined,
          target_role: targetRole || undefined,
          target_level: targetLevel,
          linkedin_url: linkedin || undefined,
          github_url: github || undefined,
          tone_preference: tone,
          experience_entries: expEntries.length ? expEntries : undefined,
          education_entries: eduEntries.length ? eduEntries : undefined,
          skills_technical: techSkills
            ? techSkills.split(",").map((s) => s.trim()).filter(Boolean)
            : undefined,
          skills_soft: softSkills
            ? softSkills.split(",").map((s) => s.trim()).filter(Boolean)
            : undefined,
          certifications: certs
            ? certs.split(",").map((s) => s.trim()).filter(Boolean)
            : undefined,
        };
        promises.push(api.onboarding.manualProfile(payload));
      }

      await Promise.all(promises);
      router.push("/dashboard");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to save profile. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [
    userId, cvFile, fullName, email, dialCode, phoneNumber, location, summary,
    targetRole, targetLevel, linkedin, github, tone, techSkills,
    softSkills, certs, experience, education, canContinue, router,
  ]);

  const addExp = () =>
    setExperience((prev) => [...prev, { title: "", company: "", location: "", start: "", end: "", bullets: "" }]);

  const removeExp = (i: number) =>
    setExperience((prev) => prev.filter((_, idx) => idx !== i));

  const updateExp = (i: number, key: keyof WorkExp, val: string) =>
    setExperience((prev) => prev.map((e, idx) => (idx === i ? { ...e, [key]: val } : e)));

  const addEdu = () =>
    setEducation((prev) => [...prev, { degree: "", institution: "", year: "", honours: "" }]);

  const updateEdu = (i: number, key: keyof EduEntry, val: string) =>
    setEducation((prev) => prev.map((e, idx) => (idx === i ? { ...e, [key]: val } : e)));

  const hasPersonal = !!(fullName && email);
  const hasExperience = experience.some((e) => e.title && e.company);
  const hasSkills = !!(techSkills || softSkills);
  const hasTarget = !!(targetRole);

  return (
    <main className="relative min-h-screen w-full overflow-x-hidden">
      <AutomationBackground />
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-16">
      {/* Logo */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-[0_0_32px_rgba(99,102,241,0.4)]">
          <Zap size={22} className="text-white" fill="white" />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold text-zinc-50 tracking-tight">TapApply</h1>
          <p className="text-zinc-500 text-sm mt-0.5">Autonomous job application platform</p>
        </div>
      </div>

      <StepIndicator current={step} />

      {/* Error banner */}
      {error && (
        <div className="w-full max-w-2xl mb-4 bg-red-950/40 border border-red-800/60 text-red-300 text-sm rounded-xl px-4 py-3 flex items-start gap-2">
          <X size={14} className="shrink-0 mt-0.5" />
          <span>{error}</span>
          <button onClick={() => setError("")} className="ml-auto text-red-400 hover:text-red-300">
            <X size={12} />
          </button>
        </div>
      )}

      {/* ── STEP 1: Region ─────────────────────────────────── */}
      {step === 1 && (
        <div className="w-full max-w-2xl animate-slide-up">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-zinc-50">Where are you targeting your search?</h2>
            <p className="text-zinc-500 text-sm mt-2">
              Select your primary job market — TapApply searches local boards in that region.
            </p>
          </div>

          {loading && (
            <div className="flex items-center justify-center gap-2 mb-4 text-zinc-400 text-sm">
              <div className="w-4 h-4 border-2 border-zinc-600 border-t-indigo-400 rounded-full animate-spin" />
              Saving region...
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {COUNTRIES.map((c) => (
              <button
                key={c.value}
                onClick={() => !loading && handleCountrySelect(c.value)}
                disabled={loading}
                className={cn(
                  "flex flex-col gap-3 p-4 rounded-2xl border text-left transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] group",
                  country === c.value
                    ? "border-indigo-500 bg-indigo-950/30 shadow-[0_0_20px_rgba(99,102,241,0.25)]"
                    : "border-zinc-800/60 bg-zinc-900/40 backdrop-blur-md hover:border-zinc-700/60 hover:bg-zinc-800/50"
                )}
              >
                <span className="text-4xl leading-none group-hover:scale-110 transition-transform inline-block">
                  {c.flag}
                </span>
                <div>
                  <div className="text-sm font-semibold text-zinc-100">{c.label}</div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {c.platforms.map((p) => (
                      <span
                        key={p.name}
                        className={cn("inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-medium border", p.color)}
                      >
                        {p.name}
                      </span>
                    ))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── STEP 2: Sector ─────────────────────────────────── */}
      {step === 2 && (
        <div className="w-full max-w-lg animate-slide-up">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-zinc-50">What&apos;s your professional field?</h2>
            <p className="text-zinc-500 text-sm mt-2">
              We&apos;ll optimise your applications and job search for your specific sector.
            </p>
          </div>

          <div className="space-y-3">
            {SECTORS.map((s) => {
              const Icon = s.icon;
              return (
                <button
                  key={s.value}
                  onClick={() => setSector(s.value)}
                  className={cn(
                    "w-full flex items-center gap-4 p-5 rounded-2xl border text-left transition-all duration-200 hover:scale-[1.01] active:scale-[0.99]",
                    sector === s.value
                      ? "border-indigo-500 bg-indigo-950/30 shadow-[0_0_20px_rgba(99,102,241,0.2)]"
                      : "border-zinc-800/60 bg-zinc-900/40 backdrop-blur-md hover:border-zinc-700/60 hover:bg-zinc-800/50"
                  )}
                >
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center shrink-0", s.bg)}>
                    <Icon size={20} className={s.color} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-zinc-100 text-sm">{s.value}</div>
                    <div className="text-xs text-zinc-500 mt-0.5">{s.desc}</div>
                  </div>
                  {sector === s.value && (
                    <CheckCircle2 size={16} className="text-indigo-400 shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl border border-zinc-700/60 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800/60 transition-all"
            >
              <ChevronLeft size={15} /> Back
            </button>
            <button
              onClick={handleSectorContinue}
              disabled={!sector || loading}
              className="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-semibold text-sm hover:from-indigo-400 hover:to-violet-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>Continue <ChevronRight size={15} /></>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ── STEP 3: Dual Panel Profile ──────────────────────── */}
      {step === 3 && (
        <div className="w-full max-w-5xl animate-slide-up">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-zinc-50">Set up your professional profile</h2>
            <p className="text-zinc-500 text-sm mt-2">
              Upload your CV, fill the form, or do both — everything helps the autopilot target the right roles.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* ── Left: Upload Panel ── */}
            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-6 flex flex-col gap-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-950/60 border border-indigo-800/30 flex items-center justify-center">
                  <Upload size={15} className="text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-100 text-sm">Upload your CV</h3>
                  <p className="text-xs text-zinc-600 mt-0.5">PDF, DOCX, or TXT · Max 10 MB</p>
                </div>
              </div>

              {/* Drop zone */}
              <div
                className={cn(
                  "relative rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all",
                  dragOver
                    ? "border-indigo-500 bg-indigo-950/20 scale-[1.02]"
                    : cvFile
                    ? "border-emerald-600/60 bg-emerald-950/20"
                    : "border-zinc-700/60 hover:border-zinc-600/60 hover:bg-zinc-800/30"
                )}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) setCvFile(f); }}
                />
                {cvFile ? (
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle2 size={36} className="text-emerald-400" />
                    <p className="font-medium text-zinc-100 text-sm">{cvFile.name}</p>
                    <p className="text-xs text-zinc-500">{(cvFile.size / 1024).toFixed(0)} KB</p>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setCvFile(null); }}
                      className="mt-1 text-xs text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
                    >
                      <X size={11} /> Remove
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <CloudUpload size={36} className="text-zinc-600" />
                    <div>
                      <p className="text-sm font-medium text-zinc-300">Drop your CV here</p>
                      <p className="text-xs text-zinc-600 mt-0.5">or click to browse files</p>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <FieldLabel>LinkedIn URL (optional)</FieldLabel>
                <input
                  className={inputCls}
                  placeholder="linkedin.com/in/yourname"
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                  data-field="linkedin_url"
                  data-sector={sector}
                />
              </div>

              <div>
                <FieldLabel>GitHub URL (optional)</FieldLabel>
                <input
                  className={inputCls}
                  placeholder="github.com/yourname"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                  data-field="github_url"
                  data-sector={sector}
                />
              </div>

              <div>
                <FieldLabel>Tone preference</FieldLabel>
                <div className="relative">
                  <select
                    className={cn(selectCls, "pr-8")}
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                  >
                    {TONES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
                </div>
              </div>
            </div>

            {/* ── Right: Manual Profile Panel ── */}
            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-2xl p-6 flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-violet-950/60 border border-violet-800/30 flex items-center justify-center">
                  <Pencil size={15} className="text-violet-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-100 text-sm">Build your profile</h3>
                  <p className="text-xs text-zinc-600 mt-0.5">Name + Email minimum to continue</p>
                </div>
              </div>

              <div className="space-y-3 overflow-y-auto max-h-[560px] pr-1 terminal-scroll">

                {/* Personal Information */}
                <AccordionSection title="Personal Information" defaultOpen hasData={hasPersonal}>
                  <div className="space-y-3">
                    <div>
                      <FieldLabel required>Full name</FieldLabel>
                      <input
                        className={inputCls}
                        placeholder="Jane Smith"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        data-field="full_name"
                        data-sector={sector}
                      />
                    </div>
                    <div>
                      <FieldLabel required>Email address</FieldLabel>
                      <input
                        type="email"
                        className={inputCls}
                        placeholder="jane@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        data-field="email"
                        data-sector={sector}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="col-span-2">
                        <FieldLabel>Phone number</FieldLabel>
                        <PhoneInput
                          dialCode={dialCode}
                          number={phoneNumber}
                          sector={sector}
                          onDialChange={setDialCode}
                          onNumberChange={setPhoneNumber}
                        />
                      </div>
                      <div className="col-span-2">
                        <FieldLabel>Location</FieldLabel>
                        <input
                          className={inputCls}
                          placeholder="London, UK"
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          data-field="location"
                          data-sector={sector}
                        />
                      </div>
                    </div>
                    <div>
                      <FieldLabel>Professional summary</FieldLabel>
                      <textarea
                        rows={3}
                        className="no-base w-full rounded-xl border border-zinc-700/60 bg-zinc-900 px-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all resize-none"
                        placeholder="Briefly describe your background and what you're looking for..."
                        value={summary}
                        onChange={(e) => setSummary(e.target.value)}
                        data-field="summary"
                        data-sector={sector}
                      />
                    </div>
                  </div>
                </AccordionSection>

                {/* Work Experience */}
                <AccordionSection title="Work Experience" hasData={hasExperience}>
                  {experience.map((exp, i) => (
                    <div key={i} className="border border-zinc-700/40 rounded-xl p-3 space-y-2.5 mb-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-zinc-500">Role {i + 1}</span>
                        {experience.length > 1 && (
                          <button type="button" onClick={() => removeExp(i)} className="text-zinc-600 hover:text-red-400 transition-colors">
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <FieldLabel>Job title</FieldLabel>
                          <input className={inputCls} placeholder="Software Engineer" value={exp.title} onChange={(e) => updateExp(i, "title", e.target.value)} data-field="experience" data-sector={sector} />
                        </div>
                        <div>
                          <FieldLabel>Company</FieldLabel>
                          <input className={inputCls} placeholder="Company name" value={exp.company} onChange={(e) => updateExp(i, "company", e.target.value)} />
                        </div>
                        <div>
                          <FieldLabel>Location</FieldLabel>
                          <input className={inputCls} placeholder="London, UK" value={exp.location} onChange={(e) => updateExp(i, "location", e.target.value)} />
                        </div>
                        <div className="grid grid-cols-2 gap-1.5">
                          <div>
                            <FieldLabel>From</FieldLabel>
                            <input className={inputCls} placeholder="2021" value={exp.start} onChange={(e) => updateExp(i, "start", e.target.value)} />
                          </div>
                          <div>
                            <FieldLabel>To</FieldLabel>
                            <input className={inputCls} placeholder="Present" value={exp.end} onChange={(e) => updateExp(i, "end", e.target.value)} />
                          </div>
                        </div>
                        <div className="col-span-2">
                          <FieldLabel>Key achievements (one per line)</FieldLabel>
                          <textarea
                            rows={3}
                            className="no-base w-full rounded-xl border border-zinc-700/60 bg-zinc-900 px-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all resize-none"
                            placeholder="Reduced deployment time by 40%..."
                            value={exp.bullets}
                            onChange={(e) => updateExp(i, "bullets", e.target.value)}
                            data-field="experience"
                            data-sector={sector}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  <button type="button" onClick={addExp} className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors mt-1">
                    <Plus size={12} /> Add another role
                  </button>
                </AccordionSection>

                {/* Skills */}
                <AccordionSection title="Skills & Certifications" hasData={hasSkills}>
                  <div className="space-y-3">
                    <div>
                      <FieldLabel>Technical skills (comma separated)</FieldLabel>
                      <input className={inputCls} placeholder="Python, AWS, React, PostgreSQL" value={techSkills} onChange={(e) => setTechSkills(e.target.value)} data-field="skills_technical" data-sector={sector} />
                    </div>
                    <div>
                      <FieldLabel>Soft skills (comma separated)</FieldLabel>
                      <input className={inputCls} placeholder="Leadership, stakeholder management" value={softSkills} onChange={(e) => setSoftSkills(e.target.value)} data-field="skills_soft" data-sector={sector} />
                    </div>
                    <div>
                      <FieldLabel>Certifications (comma separated)</FieldLabel>
                      <input className={inputCls} placeholder="AWS Solutions Architect, GCP Professional" value={certs} onChange={(e) => setCerts(e.target.value)} data-field="certifications" data-sector={sector} />
                    </div>
                  </div>
                </AccordionSection>

                {/* Target Role */}
                <AccordionSection title="Target Role" hasData={hasTarget}>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <FieldLabel>Target role title</FieldLabel>
                      <input className={inputCls} placeholder="e.g. Senior Software Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} data-field="target_role" data-sector={sector} />
                    </div>
                    <div>
                      <FieldLabel>Experience level</FieldLabel>
                      <div className="relative">
                        <select className={cn(selectCls, "pr-8")} value={targetLevel} onChange={(e) => setTargetLevel(e.target.value)} data-field="target_level" data-sector={sector}>
                          {EXP_LEVELS.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
                        </select>
                        <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
                      </div>
                    </div>
                    <div>
                      <FieldLabel>Tone preference</FieldLabel>
                      <div className="relative">
                        <select className={cn(selectCls, "pr-8")} value={tone} onChange={(e) => setTone(e.target.value)}>
                          {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                        <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
                      </div>
                    </div>
                  </div>
                </AccordionSection>

                {/* Education */}
                <AccordionSection title="Education">
                  {education.map((edu, i) => (
                    <div key={i} className="border border-zinc-700/40 rounded-xl p-3 space-y-2 mb-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="col-span-2">
                          <FieldLabel>Degree / Qualification</FieldLabel>
                          <input className={inputCls} placeholder="B.Sc. Computer Science" value={edu.degree} onChange={(e) => updateEdu(i, "degree", e.target.value)} />
                        </div>
                        <div>
                          <FieldLabel>Institution</FieldLabel>
                          <input className={inputCls} placeholder="University name" value={edu.institution} onChange={(e) => updateEdu(i, "institution", e.target.value)} />
                        </div>
                        <div>
                          <FieldLabel>Year</FieldLabel>
                          <input className={inputCls} placeholder="2020" value={edu.year} onChange={(e) => updateEdu(i, "year", e.target.value)} />
                        </div>
                        <div className="col-span-2">
                          <FieldLabel>Grade / Honours (optional)</FieldLabel>
                          <input className={inputCls} placeholder="First Class Honours" value={edu.honours} onChange={(e) => updateEdu(i, "honours", e.target.value)} />
                        </div>
                      </div>
                    </div>
                  ))}
                  <button type="button" onClick={addEdu} className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors mt-1">
                    <Plus size={12} /> Add qualification
                  </button>
                </AccordionSection>

              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 flex items-center gap-4">
            <button
              onClick={() => setStep(2)}
              className="flex items-center gap-1.5 px-5 py-3 rounded-xl border border-zinc-700/60 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800/60 transition-all"
            >
              <ChevronLeft size={15} /> Back
            </button>

            <div className="flex-1 flex flex-col gap-2">
              <button
                onClick={handleStep3Submit}
                disabled={!canContinue || loading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-600 text-white font-semibold text-sm hover:from-indigo-400 hover:to-violet-500 transition-all shadow-[0_0_24px_rgba(99,102,241,0.3)] disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Setting up autopilot...
                  </>
                ) : (
                  <>
                    <Zap size={15} fill="white" />
                    Launch Autopilot
                    <ChevronRight size={15} />
                  </>
                )}
              </button>

              {!canContinue && (
                <p className="text-center text-xs text-zinc-600">
                  Add a CV or fill in Full Name + Email to continue
                </p>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </main>
  );
}
