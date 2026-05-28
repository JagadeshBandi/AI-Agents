"use client";

import {
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { X, Send, AlertCircle } from "lucide-react";
import { SupportAgentWS, type AgentMessage } from "@/lib/ws";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────
interface ChatMessage {
  id: string;
  role: "agent" | "user" | "system";
  content: string;
  suggestions?: string[];
  heading?: string;
}

// ── Helpers ───────────────────────────────────────────────────
function generateId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function getClientId(): string {
  if (typeof sessionStorage === "undefined") return generateId();
  const key = "tapapply_guide_client_id";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = generateId();
    sessionStorage.setItem(key, id);
  }
  return id;
}

let _cachedClientId: string | null = null;
function getStableClientId(): string {
  if (!_cachedClientId) _cachedClientId = getClientId();
  return _cachedClientId;
}

// ── Premium Avatar ────────────────────────────────────────────
// Full-body illustrated human with continuous waving arm and
// independent pupil look-around. Eyes flash red on low ATS score.
function HumanAvatar({
  size = 22,
  eyesFlashing = false,
}: {
  size?: number;
  eyesFlashing?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ overflow: "visible" }}
    >
      {/* ── Hair ── */}
      <path
        d="M9.5 13 Q10 6 16 6 Q22 6 22.5 13"
        fill="rgba(196,181,253,0.85)"
      />
      {/* ── Head ── */}
      <circle
        cx="16" cy="14" r="7"
        fill="rgba(255,255,255,0.12)"
        stroke="rgba(255,255,255,0.50)"
        strokeWidth="1.4"
      />
      {/* ── Eyebrows ── */}
      <path d="M12.5 11.5 Q13.5 10.8 14.5 11.5" stroke="rgba(255,255,255,0.5)" strokeWidth="0.9" strokeLinecap="round" />
      <path d="M17.5 11.5 Q18.5 10.8 19.5 11.5" stroke="rgba(255,255,255,0.5)" strokeWidth="0.9" strokeLinecap="round" />
      {/* ── Eyes — outer group blinks, inner pupils look-around ── */}
      <g className="animate-bot-blink" style={{ transformOrigin: "16px 13.5px" }}>
        {/* Whites */}
        <ellipse cx="13.5" cy="13.5" rx="1.3" ry="1.1" fill="white" fillOpacity="0.95" />
        <ellipse cx="18.5" cy="13.5" rx="1.3" ry="1.1" fill="white" fillOpacity="0.95" />
        {/* Pupils — look-around OR flash animation */}
        <g
          className={eyesFlashing ? "animate-eye-flash" : "animate-look-around"}
          style={{ transformBox: "fill-box", transformOrigin: "center" }}
        >
          <circle cx="13.9" cy="13.8" r="0.65"
            fill={eyesFlashing ? "#ef4444" : "#818cf8"} />
          <circle cx="18.9" cy="13.8" r="0.65"
            fill={eyesFlashing ? "#ef4444" : "#818cf8"} />
          {/* Specular highlight */}
          <circle cx="14.25" cy="13.4" r="0.22" fill="white" fillOpacity="0.8" />
          <circle cx="19.25" cy="13.4" r="0.22" fill="white" fillOpacity="0.8" />
        </g>
      </g>
      {/* ── Nose (subtle) ── */}
      <path d="M16 15.5 Q15.4 16.5 16 16.8 Q16.6 16.5 16 15.5"
        fill="rgba(255,255,255,0.12)" />
      {/* ── Smile ── */}
      <path d="M13 17.2 Q16 20 19 17.2"
        stroke="rgba(255,255,255,0.70)" strokeWidth="1.3"
        strokeLinecap="round" fill="none" />
      {/* ── Body / torso ── */}
      <path
        d="M8 28 Q8.5 22 16 21 Q23.5 22 24 28"
        fill="rgba(99,102,241,0.25)"
        stroke="rgba(255,255,255,0.22)"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      {/* ── Collar ── */}
      <path d="M13.5 21.5 L16 23.5 L18.5 21.5"
        stroke="rgba(255,255,255,0.35)" strokeWidth="1" strokeLinecap="round" fill="none" />
      {/* ── Left arm (resting) ── */}
      <path
        d="M8.5 22.5 Q5.5 24 5 27"
        stroke="rgba(255,255,255,0.22)" strokeWidth="2"
        strokeLinecap="round"
      />
      {/* ── Right arm + hand — continuously waves ── */}
      <g
        className="animate-wave-hand"
        style={{ transformBox: "fill-box", transformOrigin: "22px 22px" }}
      >
        <path
          d="M23.5 22.5 Q27 19 28.5 15.5"
          stroke="rgba(255,255,255,0.35)" strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Fingers / hand */}
        <path d="M28.5 15.5 L29.8 13.2"
          stroke="rgba(196,181,253,0.9)" strokeWidth="1.2" strokeLinecap="round" />
        <path d="M28.5 15.5 L30.5 15"
          stroke="rgba(196,181,253,0.9)" strokeWidth="1.2" strokeLinecap="round" />
        <path d="M28.5 15.5 L30.2 16.8"
          stroke="rgba(196,181,253,0.9)" strokeWidth="1.2" strokeLinecap="round" />
        <path d="M28.5 15.5 L28.8 17.5"
          stroke="rgba(196,181,253,0.75)" strokeWidth="1" strokeLinecap="round" />
      </g>
    </svg>
  );
}

// ── "Tap me!" speech bubble — stable, never duplicates ────────
// Rendered as a sibling of the button inside a single fixed wrapper
// so it cannot shift position or re-mount on state changes.
function TapMeBubble() {
  return (
    <div className="flex flex-col items-end pointer-events-none select-none">
      <div className="bg-zinc-900 border border-indigo-500/60 rounded-2xl rounded-br-sm px-3.5 py-2 shadow-xl shadow-black/60 flex items-center gap-2 animate-callout-in">
        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse shrink-0" />
        <span className="text-xs font-semibold text-zinc-100 whitespace-nowrap">Tap me!</span>
      </div>
      {/* Arrow pointing right toward the button */}
      <div className="mr-4 -mt-px">
        <div className="w-2.5 h-2.5 bg-zinc-900 border-r border-b border-indigo-500/60 rotate-45" />
      </div>
    </div>
  );
}

// ── Typing indicator ──────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3.5 py-2.5 bg-zinc-800/80 rounded-2xl rounded-tl-sm w-fit">
      <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 typing-dot" />
      <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 typing-dot" />
      <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 typing-dot" />
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────
export default function FloatingGuide() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [hasSuggestion, setHasSuggestion] = useState(false);
  const [connected, setConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [eyesFlashing, setEyesFlashing] = useState(false);

  const wsRef = useRef<SupportAgentWS | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sectorRef = useRef("Tech & Software");
  const focusedField = useRef<{ name: string; sector: string; startTime: number } | null>(null);
  const stallTriggered = useRef(false);
  const typingInField = useRef(false);
  const stallIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Push message (stable across renders) ─────────────────
  const pushMessage = useCallback((msg: Omit<ChatMessage, "id">) => {
    setMessages((prev) => [...prev, { id: generateId(), ...msg }]);
  }, []);

  // ── WebSocket — mount once ────────────────────────────────
  useEffect(() => {
    const clientId = getStableClientId();

    const uid = localStorage.getItem("tapapply_user_id");
    if (uid) {
      fetch(`/api/profile/${uid}`)
        .then((r) => r.json())
        .then((d: unknown) => {
          const data = d as Record<string, unknown>;
          if (typeof data.sector === "string") sectorRef.current = data.sector;
        })
        .catch(() => {});
    }

    const ws = new SupportAgentWS(
      clientId,
      (msg: AgentMessage) => {
        if (msg.type === "system") {
          setConnected(true);
        } else if (msg.type === "suggestion") {
          setIsTyping(false);
          setHasSuggestion(true);
          pushMessage({
            role: "agent",
            content: msg.heading,
            suggestions: msg.suggestions,
            heading: msg.heading,
          });
        } else if (msg.type === "response") {
          setIsTyping(false);
          pushMessage({ role: "agent", content: msg.message });
        } else if (msg.type === "error") {
          setIsTyping(false);
          pushMessage({ role: "agent", content: `⚠ ${msg.message}` });
        }
      },
      (conn) => setConnected(conn)
    );

    wsRef.current = ws;
    ws.connect();
    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [pushMessage]);

  // ── ATS score alert ───────────────────────────────────────
  useEffect(() => {
    const handler = (e: Event) => {
      const score = (e as CustomEvent<{ score: number }>).detail.score;
      if (score < 65) {
        setEyesFlashing(true);
        setHasSuggestion(true);
        setIsOpen(true);
        pushMessage({
          role: "agent",
          content:
            `That match rate (${score}/100) will likely be filtered out before a human sees it. ` +
            `Click "Generate ATS CV" below — it rewrites your profile with the missing keywords woven in naturally.`,
        });
        setTimeout(() => setEyesFlashing(false), 6000);
      }
    };
    window.addEventListener("tapapply:ats-score", handler);
    return () => window.removeEventListener("tapapply:ats-score", handler);
  }, [pushMessage]);

  // ── 7-second stall detection ──────────────────────────────
  useEffect(() => {
    const handleFocusIn = (e: Event) => {
      const target = e.target as HTMLElement;
      const isFormField =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement;
      if (!isFormField) return;

      const fieldName =
        target.dataset?.field || target.getAttribute("name") || target.id || "field";
      const fieldSector = target.dataset?.sector || sectorRef.current;

      focusedField.current = { name: fieldName, sector: fieldSector, startTime: Date.now() };
      stallTriggered.current = false;
      typingInField.current = false;
      sectorRef.current = fieldSector;
    };

    const handleFocusOut = () => {
      focusedField.current = null;
      stallTriggered.current = false;
      typingInField.current = false;
    };

    const handleInput = () => {
      typingInField.current = true;
      if (focusedField.current) {
        focusedField.current = { ...focusedField.current, startTime: Date.now() };
        stallTriggered.current = false;
      }
    };

    stallIntervalRef.current = setInterval(() => {
      if (!focusedField.current || stallTriggered.current || typingInField.current) return;
      const elapsed = (Date.now() - focusedField.current.startTime) / 1000;
      if (elapsed >= 7) {
        stallTriggered.current = true;
        wsRef.current?.notifyStall(focusedField.current.name, focusedField.current.sector);
        setHasSuggestion(true);
      }
    }, 1000);

    document.addEventListener("focusin", handleFocusIn);
    document.addEventListener("focusout", handleFocusOut);
    document.addEventListener("input", handleInput, true);

    return () => {
      document.removeEventListener("focusin", handleFocusIn);
      document.removeEventListener("focusout", handleFocusOut);
      document.removeEventListener("input", handleInput, true);
      if (stallIntervalRef.current !== null) {
        clearInterval(stallIntervalRef.current);
        stallIntervalRef.current = null;
      }
    };
  }, []);

  // ── Cleanup fallback timer on unmount ─────────────────────
  useEffect(() => {
    return () => {
      if (fallbackTimerRef.current !== null) clearTimeout(fallbackTimerRef.current);
    };
  }, []);

  // ── Auto-scroll + focus ───────────────────────────────────
  useEffect(() => {
    if (isOpen) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen, isTyping]);

  useEffect(() => {
    if (isOpen) {
      const t = setTimeout(() => inputRef.current?.focus(), 150);
      return () => clearTimeout(t);
    }
  }, [isOpen]);

  const handleOpen = () => {
    setIsOpen(true);
    setHasSuggestion(false);
  };

  const handleClose = () => setIsOpen(false);

  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    pushMessage({ role: "user", content: text });
    setInput("");
    setIsTyping(true);
    wsRef.current?.chat(text, sectorRef.current);

    if (fallbackTimerRef.current !== null) clearTimeout(fallbackTimerRef.current);
    fallbackTimerRef.current = setTimeout(() => {
      setIsTyping(false);
      fallbackTimerRef.current = null;
    }, 15_000);
  }, [input, pushMessage]);

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* ── Floating launcher — "Tap me!" bubble + avatar button ── */}
      {/* Single fixed wrapper: both elements mount/unmount together,  */}
      {/* guaranteeing no duplication or layout shift on state changes.  */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex items-end gap-3">
          {/* Speech bubble — always visible, not gated on hasSuggestion */}
          <TapMeBubble />

          {/* Avatar button */}
          <button
            onClick={handleOpen}
            aria-label="Open TapApply Guide"
            className="relative w-[56px] h-[56px] rounded-full flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 animate-bot-breathe shrink-0"
            style={{ background: "linear-gradient(135deg, #6366f1, #7c3aed)" }}
          >
            <HumanAvatar size={28} eyesFlashing={eyesFlashing} />
            {/* Suggestion dot */}
            {hasSuggestion && (
              <span
                className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-amber-400 rounded-full border-2 border-zinc-950 animate-pulse"
                aria-hidden="true"
              />
            )}
          </button>
        </div>
      )}

      {/* ── Chat panel ────────────────────────────────────── */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="TapApply Guide"
          className="fixed bottom-6 right-6 z-50 w-[calc(100vw-3rem)] sm:w-[390px] rounded-2xl shadow-2xl border border-zinc-800/60 overflow-hidden flex flex-col animate-slide-up"
          style={{ maxHeight: "540px", background: "#111113" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800/60 bg-zinc-900/60 shrink-0">
            <div className="flex items-center gap-2.5">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
                style={{ background: "linear-gradient(135deg, #6366f1, #7c3aed)" }}
              >
                <HumanAvatar size={20} eyesFlashing={eyesFlashing} />
              </div>
              <div>
                <p className="text-sm font-semibold text-zinc-100 leading-none">
                  TapApply Guide
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span
                    className={cn(
                      "w-1.5 h-1.5 rounded-full transition-colors",
                      connected ? "bg-emerald-400" : "bg-zinc-600 animate-pulse"
                    )}
                  />
                  <p className="text-[10px] text-zinc-600">
                    {connected ? "Connected" : "Connecting..."}
                  </p>
                </div>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="w-7 h-7 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/60 flex items-center justify-center transition-colors"
              aria-label="Close guide"
            >
              <X size={14} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3.5 py-3 space-y-2.5 min-h-0 chat-scroll">
            {/* Minimal disclaimer */}
            <div className="flex items-start gap-2 bg-amber-950/30 border border-amber-800/30 rounded-xl px-3 py-2">
              <AlertCircle size={11} className="text-amber-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-amber-300/70 leading-relaxed">
                AI assistant — not a regulated adviser. Review outputs before acting on them.
              </p>
            </div>

            {messages.length === 0 && (
              <div className="text-center text-zinc-700 text-[11px] py-4 px-2 leading-relaxed">
                Ask me about UK job boards, CV structure, salary ranges, interview prep — anything career related.
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex",
                  msg.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                {msg.role === "system" ? (
                  <div className="w-full flex items-start gap-2 bg-amber-950/40 border border-amber-800/40 rounded-xl px-3 py-2.5">
                    <AlertCircle size={12} className="text-amber-400 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-amber-200/80 leading-relaxed">{msg.content}</p>
                  </div>
                ) : msg.role === "user" ? (
                  <div className="bg-indigo-600 text-white text-[12px] rounded-2xl rounded-tr-sm px-3.5 py-2.5 max-w-[88%] leading-relaxed">
                    {msg.content}
                  </div>
                ) : msg.suggestions ? (
                  <div className="bg-zinc-800/80 rounded-2xl rounded-tl-sm px-3.5 py-3 max-w-[92%] space-y-2">
                    {msg.heading && (
                      <p className="text-[11px] font-semibold text-zinc-300 leading-snug">
                        {msg.heading}
                      </p>
                    )}
                    <ul className="space-y-1.5">
                      {msg.suggestions.map((s, si) => (
                        <li
                          key={`${msg.id}-${si}-${s.slice(0, 12)}`}
                          className="text-[11px] text-zinc-400 flex items-start gap-1.5 leading-relaxed"
                        >
                          <span className="text-indigo-400 shrink-0 mt-0.5">→</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="bg-zinc-800/80 rounded-2xl rounded-tl-sm px-3.5 py-2.5 max-w-[92%]">
                    <p className="text-[12px] text-zinc-300 leading-relaxed">{msg.content}</p>
                  </div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <TypingIndicator />
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-3 py-3 border-t border-zinc-800/60 bg-zinc-900/40 flex items-center gap-2 shrink-0">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about Reed, CV, salary, interview prep..."
              className="no-base flex-1 text-xs py-2 px-3 rounded-xl bg-zinc-800/80 border border-zinc-700/40 text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim()}
              aria-label="Send message"
              className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white transition-all hover:from-indigo-400 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              <Send size={13} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
