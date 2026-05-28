"""
TapApply conversational support agent.

Handles WebSocket messages from the floating guide widget. Uses Claude AI
when the API key is available; falls back to a rich, platform-aware keyword
engine that covers UK/global job-market specifics, Reed, TotalJobs, LinkedIn,
Indeed and general career advice — never the same generic loop.
"""

import os
import re
import random
from typing import Dict, List, Optional, Tuple
from .ws_hub import WSHub

DISCLAIMER = (
    "Hey — I'm an AI assistant, not a regulated career adviser. "
    "Double-check anything before you act on it, but I'm genuinely here to help. "
    "What are you working on?"
)

# ---------------------------------------------------------------------------
# Claude AI — lazy singleton
# ---------------------------------------------------------------------------

_claude_client = None


def _get_claude_client():
    global _claude_client
    if _claude_client is not None:
        return _claude_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        _claude_client = anthropic.Anthropic(api_key=api_key)
        print("[SupportAgent] Claude AI client initialised.")
    except Exception as exc:
        print(f"[SupportAgent] Could not init Claude client: {exc}")
    return _claude_client


_SYSTEM_PROMPT = """You are TapApply Guide — a sharp, direct, knowledgeable career peer embedded in TapApply, an autonomous job-application platform.

Your personality: you are confident, practical, and human — like a senior colleague who has hired people and been hired themselves. You give real information, not motivational coaching. You have specific knowledge of UK, US, Canadian, Australian, and EU job markets.

Platform knowledge you must use when relevant:
- Reed.co.uk: best for agency-placed roles, certification-heavy fields (accountancy, nursing, engineering), and volume recruitment. CV must use chronological format, no photos.
- TotalJobs: dominant for direct employer postings, operational and corporate roles. Strong in engineering, logistics, retail. Slightly more flexible on CV style.
- Indeed: global reach, strong for SME and startup roles. Apply-with-Indeed is common; optimise headline and summary for keyword scanning.
- LinkedIn: best for networking, recruiter outreach, and senior roles. Headline + About section are the first things recruiters read — not the job history.
- Adzuna: UK aggregator — pulls from multiple boards, good for salary benchmarking.

Formatting rules:
- 2–4 sentences max unless the question genuinely needs a list.
- Never say "certainly!", "great question!", "of course!", "as an AI", "I'd be happy to".
- Never start with a compliment or filler.
- Be direct — answer the question first, then add one useful follow-up detail.
- If the user mentions a specific sector or role, tailor every answer to it.
- For salary questions, give concrete market-rate figures for the user's region.
- For platform questions, compare directly with specific strengths and weaknesses.
- Never ask the user to "think of a concrete example" — coach them by asking a focused question or giving a structural template instead.
"""


async def _ask_claude(message: str, sector: str, history: List[dict]) -> Optional[str]:
    client = _get_claude_client()
    if client is None:
        return None
    try:
        messages = []
        # Include recent conversation history for context (last 6 turns)
        for turn in history[-6:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        # Inject sector context into the final user message
        full_message = f"[User sector: {sector}]\n\n{message}" if sector else message
        messages.append({"role": "user", "content": full_message})

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=350,
            system=_SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception as exc:
        print(f"[SupportAgent] Claude API error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Keyword fallback — rich, platform-aware, never repeats
# ---------------------------------------------------------------------------

# Each entry: (list_of_trigger_patterns, list_of_responses)
# A random response is selected each time a trigger matches.
_CHAT_RULES: List[Tuple[List[str], List[str]]] = [

    # ── UK job application ──────────────────────────────────────────────────
    (
        ["how.*apply.*uk", "uk.*how.*apply", "apply.*job.*uk", "uk.*job.*apply",
         "get.*job.*uk", "find.*job.*uk", "uk.*job.*search"],
        [
            "Applying in the UK comes down to two strategies: high-volume boards like Reed and TotalJobs, "
            "or direct recruiter outreach via LinkedIn. Reed is stronger for agency-placed roles; TotalJobs "
            "dominates direct employer postings. Tell me your target sector and I'll tell you which one to hit first.",

            "UK applications live on a short shortlist: Reed.co.uk for agency and certification-backed roles, "
            "TotalJobs for corporate direct listings, and LinkedIn for anything senior or networking-driven. "
            "Which sector are you targeting? That changes the platform priority significantly.",
        ]
    ),

    # ── Reed vs TotalJobs ───────────────────────────────────────────────────
    (
        ["reed.*totaljobs", "totaljobs.*reed", "reed or total", "which.*reed.*total",
         "reed.*better", "totaljobs.*better", "reed.*vs", "vs.*totaljobs"],
        [
            "Both are giants with distinct strengths. Reed dominates agency placements and certification-heavy roles — "
            "accountancy, nursing, engineering. TotalJobs has a stronger foothold in direct corporate listings and "
            "operational sectors. Cross-reference your target role: if it's appearing on agency sites, Reed first; "
            "direct employer postings, TotalJobs.",

            "Reed is phenomenal for recruiter-placed roles and volume hiring — it's where agencies post first. "
            "TotalJobs skews toward direct employer listings and is especially strong in engineering, logistics, "
            "and corporate ops. If you're in tech, both will have coverage but LinkedIn will catch what they miss.",
        ]
    ),

    # ── LinkedIn strategy ───────────────────────────────────────────────────
    (
        ["linkedin", "linked in", "recruiter.*outreach", "network.*job"],
        [
            "LinkedIn is less a job board and more a recruiter radar. Your headline and About section are read "
            "before your experience — optimise those for your target role title and 2–3 core keywords. "
            "Open to Work turned on privately still signals to recruiters without broadcasting to connections.",

            "For LinkedIn, the hierarchy is: headline → About → most recent role. Recruiters search by title "
            "and location filter first. Make sure your headline matches the exact job title you're targeting, "
            "not a creative variation. What sector are you targeting — I can give you the right keyword density.",
        ]
    ),

    # ── Indeed ──────────────────────────────────────────────────────────────
    (
        ["indeed", "indeed.com", "indeed.co.uk"],
        [
            "Indeed aggregates listings from boards and company pages — you'll see overlap with Reed and TotalJobs. "
            "Where it wins is SME and startup roles that don't have recruitment budget. The 'Apply with Indeed' "
            "resume needs a strong summary line since that's what employers see first in their dashboard.",

            "Indeed is strongest for roles under £60k and SME/startup postings. For senior or specialist roles, "
            "it's a secondary channel. The algorithm weights keyword match in your resume against the job title "
            "heavily — more so than Reed's matching logic.",
        ]
    ),

    # ── ATS / CV optimisation ────────────────────────────────────────────────
    (
        ["ats", "applicant tracking", "keyword.*cv", "cv.*keyword", "cv.*pass",
         "get.*through.*filter", "algorithm.*cv"],
        [
            "ATS systems scan for exact keyword matches between your CV and the job description. "
            "Copy the key noun phrases from the JD verbatim into your skills section and summary — "
            "don't paraphrase them. Use the Match CV tool in TapApply to run an instant gap analysis.",

            "Three ATS quick wins: (1) Use the exact job title from the posting in your summary. "
            "(2) Mirror the JD's noun phrases — 'stakeholder management' not 'managing stakeholders'. "
            "(3) Plain formatting — no tables, columns, or text boxes that confuse parsers.",
        ]
    ),

    # ── CV structure / format ────────────────────────────────────────────────
    (
        ["cv.*format", "format.*cv", "cv.*structure", "resume.*format",
         "cv.*layout", "how.*write.*cv", "write.*cv"],
        [
            "UK CV format: name + contact → 3-line summary → skills → experience (reverse chronological) → "
            "education. One or two pages — two is fine for 5+ years experience. No photo, no DOB. "
            "Each role: 3–5 bullets, each starting with a strong action verb and ending with a result.",

            "For UK roles: keep it 1–2 pages, reverse chronological, no photo. Lead with a punchy 2-line summary "
            "that names your discipline and years. For US roles: 'resume' not 'CV', one page for under 10 years, "
            "include a LinkedIn URL. Both: quantify every bullet you can.",
        ]
    ),

    # ── Salary questions ─────────────────────────────────────────────────────
    (
        ["salary", "pay", "compensation", "wage", "how much", "rate"],
        [
            "UK tech benchmarks: junior £30–45k, mid £50–75k, senior £80–110k, principal/staff £120k+. "
            "London adds ~15–20% but remote roles are converging. Always give a range, not a single figure — "
            "it anchors the negotiation without boxing you in.",

            "Name a range based on your research, not gut feel. Check Glassdoor, Levels.fyi (tech), "
            "and the Adzuna salary tracker for your sector. Saying 'I'd like to discuss the full package' "
            "is valid for senior roles where equity or bonus is part of the comp picture.",
        ]
    ),

    # ── Cover letter ─────────────────────────────────────────────────────────
    (
        ["cover letter", "covering letter", "cover note"],
        [
            "Three paragraphs: why this specific company (reference something real — a product, a recent hire, "
            "a problem they're solving), why you're qualified (one concrete achievement with a number), "
            "and a direct close asking for a conversation. 250–350 words. Don't restate your CV.",

            "Skip 'I am writing to apply for...' — that wastes the first sentence recruiters actually read. "
            "Open with your strongest credential or a specific observation about the company. "
            "Then one quantified result. Then a clean ask for a call.",
        ]
    ),

    # ── Interview prep ────────────────────────────────────────────────────────
    (
        ["interview", "prepare.*interview", "interview.*question", "how.*interview",
         "practice.*interview"],
        [
            "Build 5 core stories using STAR format — each under 90 seconds when spoken aloud. "
            "Cover: a challenge you solved under pressure, a conflict you navigated, an impact you delivered, "
            "something you'd approach differently now. These cover 80% of competency questions.",

            "Research the company in three layers: (1) what they do and who they compete with, "
            "(2) the team or department you're joining, (3) the interviewer's background on LinkedIn. "
            "The best candidates connect their answers to the company's specific context — not generic examples.",
        ]
    ),

    # ── Notice period / start date ────────────────────────────────────────────
    (
        ["notice period", "start date", "when.*start", "notice"],
        [
            "State your contractual notice clearly. UK standard is 1–3 months depending on seniority; "
            "US is typically 2 weeks. If you can negotiate early release, mention you're open to that conversation "
            "once an offer is on the table — don't volunteer it before.",

            "For senior roles, a 3-month notice is normal and won't disadvantage you. "
            "Mention if your contract has a garden leave clause — that matters to the hiring timeline. "
            "Most companies will wait for the right person.",
        ]
    ),

    # ── Profile / onboarding ──────────────────────────────────────────────────
    (
        ["profile", "summary", "professional summary", "about me", "bio"],
        [
            "3–4 sentences: discipline + years → your strongest domain or achievement → what you're targeting. "
            "First-person, no 'I'. Lead with a credential or a scale signal, not a personality trait. "
            "Example: 'Backend engineer, 8 years, distributed systems and high-throughput APIs at £200M-ARR SaaS companies.'",

            "The summary is the first thing recruiters read — make it scannable. State your role title, "
            "years of experience, your strongest technical area, and one scale or impact signal. "
            "Skip 'passionate about' and 'results-driven' — those phrases signal a generic CV.",
        ]
    ),

    # ── Skills section ────────────────────────────────────────────────────────
    (
        ["skills", "competencies", "what skills", "which skills"],
        [
            "Group them: core technical skills → tools/platforms → soft skills (briefly). "
            "Only list skills you can actually discuss in an interview. ATS matches your skills "
            "against the JD literally — so mirror the JD's phrasing exactly.",

            "For technical roles: Languages → Frameworks → Cloud/Infra → Databases. "
            "For non-tech: Tools → Methodologies → Domain expertise. "
            "Senior roles should also include architecture, leadership, or strategic skills — not just tooling.",
        ]
    ),

    # ── Autopilot / TapApply features ────────────────────────────────────────
    (
        ["autopilot", "how.*work", "tapapply", "what.*do", "how.*use"],
        [
            "Autopilot scans job boards for roles matching your profile, generates tailored cover letters, "
            "and submits applications — all running in the background. Enable it on the Dashboard, "
            "and check the Activity console to see what it's doing in real time.",

            "TapApply runs three things autonomously: job discovery (scanning boards for your sector/location), "
            "application generation (tailored CV + cover letter per role), and tracking (every application logged "
            "to your Applications tab). The Match CV tool lets you manually score any JD against your profile.",
        ]
    ),
]


def _keyword_fallback(message: str, sector: str) -> str:
    lower = message.lower()

    # Walk rules — return first match (random pick from that rule's pool)
    for patterns, responses in _CHAT_RULES:
        if any(re.search(p, lower) for p in patterns):
            return random.choice(responses)

    # Sector-aware fallback for unmatched messages
    _sector_defaults: Dict[str, List[str]] = {
        "Tech & Software": [
            f"For a {sector} role, the key move is getting your tech stack visible at the top of your CV — "
            "not buried in a skills section at the bottom. Which part of the application are you working on?",
            f"In {sector}, recruiters scan for specific technologies before they read anything else. "
            "Make sure your headline and summary name the stack — not just 'software engineer'.",
        ],
        "Finance & Banking": [
            f"For {sector} roles, your designation or qualification is the first filter — CFA, ACA, ACCA. "
            "If you have one, it should be in your name line, not buried in education.",
            f"In {sector}, deal size, AUM, or portfolio value are the credibility signals. "
            "Name a number in your first experience bullet — it separates you immediately.",
        ],
        "Healthcare & Medical": [
            f"For {sector} roles, your registration body and number must be in your CV header — "
            "HCPC, GMC, NMC. Recruiters filter on this before reading anything else.",
            f"In {sector}, clinical volume and patient population are the key signals. "
            "Name your caseload size and specialist area in your summary.",
        ],
        "Marketing & Creative": [
            f"For {sector} roles, one quantified campaign result is worth more than three general claims. "
            "Lead with your best metric — budget, reach, conversion, revenue attributed.",
            f"In {sector}, channel specialisation matters. Name your primary disciplines explicitly: "
            "paid search, brand, CRM, content — not just 'marketing'.",
        ],
        "Engineering & Operations": [
            f"For {sector} roles, site scale and operational metrics are what hiring managers scan for. "
            "Name production volumes, team size, or capex managed in your summary.",
            f"In {sector}, certifications like NEBOSH, Chartered Engineer, or ISO qualifications "
            "carry real weight — list them prominently, not just in a skills appendix.",
        ],
    }

    pool = _sector_defaults.get(sector, [
        "What specific part of the application process are you working on right now? "
        "I can give you much more targeted advice once I know.",
        f"For a {sector} role, the most important thing is matching the JD's language. "
        "What does the job posting emphasise? Let's work from that.",
    ])

    return random.choice(pool)


# ---------------------------------------------------------------------------
# Field-level stall suggestions (unchanged — already strong)
# ---------------------------------------------------------------------------

_FIELD_SUGGESTIONS: Dict[str, Dict[str, List[str]]] = {
    "summary": {
        "Tech & Software": [
            "Drop your discipline and years up front — 'Backend engineer, 7 years, distributed systems' hits harder than a vague opener.",
            "Name the type of systems you actually build. 'High-throughput data pipelines' is 10× more useful than 'worked on backend'.",
            "Skip 'passionate' and 'driven' — those words say nothing. What do you build, at what scale, for how many users?",
        ],
        "Finance & Banking": [
            "Lead with your designation if you have one (CFA, ACA, ACCA) — that's literally the first thing recruiters scan for.",
            "Name your actual domain: credit risk, equity research, FP&A, treasury. 'Finance professional' is too vague.",
            "A size signal helps: portfolio value, AUM, deal size — even a rough figure makes your summary far more credible.",
        ],
        "Healthcare & Medical": [
            "Lead with your registration — 'HCPC-registered Physiotherapist' or 'GMC-registered GP'. Don't make them hunt for it.",
            "State your specialty and post-qualification years up front. Recruiters filter on exactly this.",
        ],
        "Marketing & Creative": [
            "Name your actual disciplines: brand, performance, CRM, content. 'Marketing professional' tells them almost nothing.",
            "One number makes the whole thing land — campaign result, budget size, audience. Pick your best one.",
        ],
        "Engineering & Operations": [
            "Open with your engineering discipline — mechanical, civil, process. Don't make them guess from your job titles.",
            "Call out your sectors: manufacturing, energy, infrastructure, logistics. Context shows you're not generic.",
        ],
        "_default": [
            "3–4 sentences max. Recruiters spend under 10 seconds here — make every word earn its place.",
            "Lead with your strongest credential or achievement, not a personality trait.",
        ],
    },
    "experience": {
        "Tech & Software": [
            "Every bullet: action verb → what you built/did → measurable result. That's it.",
            "Quantify where you can: 'reduced latency by 40%', 'served 2M daily active users'.",
            "List the tech stack per role — ATS systems scan for specific technologies.",
        ],
        "Finance & Banking": [
            "Include deal sizes or portfolio values, even approximate. 'Managed a £50M portfolio' beats 'managed portfolios'.",
            "Be precise with financial terms — recruiters know when someone's using language they don't fully own.",
        ],
        "Healthcare & Medical": [
            "Clinical roles: patient population, caseload volume, acuity level. Three things that tell the whole story.",
            "Include leadership: supervising juniors, managing rosters, leading audits — it signals progression.",
        ],
        "Marketing & Creative": [
            "Name the campaign types: brand awareness, demand gen, product launch, retention.",
            "Budget managed + results vs target — this is what hiring managers look for first.",
        ],
        "Engineering & Operations": [
            "Scale matters: site size, production volumes, team headcount, capex managed.",
            "Projects with outcomes: cost savings, efficiency improvements, safety metrics.",
        ],
        "_default": [
            "Strong action verbs: built, led, delivered, managed, reduced, improved. Start each bullet with one.",
            "End every bullet with a result, even approximate — 'saving around 3 hours per week' is still useful.",
        ],
    },
    "skills": {
        "Tech & Software": [
            "Group them: Languages, Frameworks, Cloud & DevOps, Databases. A structured list reads better than a keyword wall.",
            "Only list skills you can actually discuss in an interview. Padding tends to backfire.",
        ],
        "Finance & Banking": [
            "Technical skills that matter: Excel (advanced), Bloomberg, FactSet, SQL, Python. List them explicitly.",
            "Regulatory frameworks: Basel III, IFRS, MiFID II, Solvency II. These are searchable keywords.",
        ],
        "Healthcare & Medical": [
            "Clinical tools and systems: EMIS, SystmOne, Epic, Meditech — plus specialist assessment tools.",
            "Relevant guidelines: NICE, GCP, ICH, CQC. List the ones you've actually worked within.",
        ],
        "_default": [
            "Group them logically rather than one long block. Easier to scan = more likely to get read.",
            "Prioritise skills that appear in the job description — ATS systems match against those first.",
        ],
    },
    "cover_letter": {
        "_default": [
            "One page max — 250–350 words. Open with why this company specifically, not 'I am writing to apply'.",
            "Three sections: why them (specific reference), why you (one quantified achievement), close (direct ask for a call).",
        ],
    },
    "salary_expectation": {
        "Tech & Software": [
            "UK benchmarks: junior £30–45k, mid £50–75k, senior £80–110k, principal £120k+.",
            "For startups: separate your equity expectation from base. They're different conversations.",
        ],
        "_default": [
            "A range based on market research is better than a single number. It shows you've done the homework.",
            "It's fine to say you'd like to discuss once you know more about the full package.",
        ],
    },
    "notice_period": {
        "_default": [
            "State your contractual notice period clearly — employers plan their hiring timeline around this.",
            "UK standard: 1–3 months depending on seniority. US: typically 2 weeks.",
        ],
    },
}


def _get_suggestions(field_name: str, sector: str) -> List[str]:
    field_key = None
    for key in _FIELD_SUGGESTIONS:
        if key.lower() in field_name.lower() or field_name.lower() in key.lower():
            field_key = key
            break

    if field_key is None:
        return [
            "Make your answer specific to this role rather than a generic one you'd use anywhere.",
            "Concrete examples and real situations are always more convincing than broad claims.",
        ]

    sector_suggestions = _FIELD_SUGGESTIONS[field_key].get(
        sector, _FIELD_SUGGESTIONS[field_key].get("_default", [])
    )
    return random.sample(sector_suggestions, min(2, len(sector_suggestions)))


# ---------------------------------------------------------------------------
# Support Agent
# ---------------------------------------------------------------------------

# Per-client conversation history stored in memory — cleared on WS disconnect
_conversation_history: Dict[str, List[dict]] = {}


class SupportAgent:
    async def handle(self, client_id: str, data: dict, hub: WSHub) -> None:
        msg_type = data.get("type", "")

        if msg_type == "ping":
            await hub.send_to(client_id, {"type": "pong"})

        elif msg_type == "stall":
            field = data.get("field", "field")
            sector = data.get("sector", "Tech & Software")
            suggestions = _get_suggestions(field, sector)
            await hub.send_to(client_id, {
                "type": "suggestion",
                "field": field,
                "heading": "Quick pointers for this field:",
                "suggestions": suggestions,
            })

        elif msg_type == "chat":
            message = data.get("message", "")
            sector = data.get("sector", "Tech & Software")
            if not message.strip():
                return

            history = _conversation_history.setdefault(client_id, [])
            response = await self._generate_response(message, sector, history)

            # Append to history (keep last 12 turns)
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})
            if len(history) > 12:
                _conversation_history[client_id] = history[-12:]

            await hub.send_to(client_id, {"type": "response", "message": response})

        elif msg_type == "context_update":
            pass

        elif msg_type == "disconnect":
            _conversation_history.pop(client_id, None)

    async def _generate_response(self, message: str, sector: str, history: List[dict]) -> str:
        ai_response = await _ask_claude(message, sector, history)
        if ai_response:
            return ai_response
        return _keyword_fallback(message, sector)


support_agent = SupportAgent()
