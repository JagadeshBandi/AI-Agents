"""
Interview preparation engine.

Generates a Company Intelligence Sheet and a tailored mock-interview pack
for a specific role. Works entirely from structured data — no LLM key required.
When ANTHROPIC_API_KEY is set, enhances the company brief with live context.
"""

import random
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Sector-specific challenge banks — realistic problems companies face
# ---------------------------------------------------------------------------

_SECTOR_CHALLENGES: Dict[str, List[str]] = {
    "Tech & Software": [
        "Scaling infrastructure to handle non-linear user growth without proportional cost increases",
        "Reducing deployment lead time while maintaining reliability and test coverage",
        "Managing technical debt accumulated during rapid product development cycles",
        "Hiring and retaining senior engineering talent in a competitive market",
        "Migrating legacy monolithic systems to a distributed, service-oriented architecture",
        "Ensuring data security and privacy compliance across multiple jurisdictions",
    ],
    "Finance & Banking": [
        "Navigating increasing regulatory scrutiny and capital adequacy requirements",
        "Competing with fintech disruptors on speed-to-market and user experience",
        "Managing credit risk exposure in an uncertain macro environment",
        "Modernising core banking systems while maintaining 24/7 operational continuity",
        "Attracting institutional and retail clients in a low-yield environment",
        "Ensuring AML and KYC processes are robust without creating friction for legitimate customers",
    ],
    "Healthcare & Medical": [
        "Meeting growing patient demand with constrained clinical staffing levels",
        "Integrating digital health tools while maintaining data privacy and clinical safety",
        "Managing the cost and complexity of regulatory submissions in multiple markets",
        "Reducing time-to-market for new therapeutics while upholding trial integrity",
        "Building workforce resilience after significant post-pandemic burnout",
        "Demonstrating health-economic value to payers and commissioners",
    ],
    "Marketing & Creative": [
        "Maintaining brand relevance across increasingly fragmented media channels",
        "Proving marketing ROI in a landscape where attribution is increasingly difficult",
        "Navigating data privacy constraints on personalisation and targeting",
        "Building genuine brand communities rather than just transactional audiences",
        "Adapting campaigns quickly in response to real-time social and cultural shifts",
        "Balancing global brand consistency with local market relevance",
    ],
    "Engineering & Operations": [
        "Improving throughput and yield without additional capital expenditure",
        "Building supply-chain resilience in the face of geopolitical and logistics disruptions",
        "Meeting sustainability and net-zero commitments on an accelerated timeline",
        "Integrating new automation technologies with existing legacy infrastructure",
        "Retaining skilled technical operators and reducing knowledge-transfer risk",
        "Maintaining quality standards and regulatory compliance at higher production volumes",
    ],
}

_SECTOR_CULTURE_SIGNALS: Dict[str, List[str]] = {
    "Tech & Software": [
        "Values engineers who ship iteratively and learn from production data",
        "Rewards ownership — people who see problems through end-to-end",
        "Direct, written communication culture over unnecessary meetings",
        "Strong bias for reversible decisions made quickly",
        "Psychological safety to surface technical concerns early",
    ],
    "Finance & Banking": [
        "Values intellectual rigour and evidence-based decision making",
        "Detail orientation is rewarded; precision matters more than speed",
        "Hierarchical with clear seniority signals, but meritocratic at analysis level",
        "Expectation of proactive risk identification, not just execution",
        "Strong team cohesion under pressure — high-stakes culture",
    ],
    "Healthcare & Medical": [
        "Patient safety is the non-negotiable first principle in every decision",
        "Collaborative multidisciplinary working across clinical and non-clinical teams",
        "Evidence-based mindset — claims must be supported by data",
        "Regulatory compliance is a shared responsibility, not a compliance team function",
        "Resilience and composure under time and resource pressure",
    ],
    "Marketing & Creative": [
        "Creative confidence is expected — bring ideas, defend them, accept feedback",
        "Data and intuition are both valued; neither is subordinate",
        "Consumer empathy is a hiring signal, not just a phrase on the job spec",
        "Comfort with ambiguity and rapid pivoting when campaigns underperform",
        "Cross-functional collaboration with product, sales, and external agencies",
    ],
    "Engineering & Operations": [
        "Safety-first culture — near-misses are reported and learned from openly",
        "Continuous improvement mindset; the current state is never the best state",
        "Structured problem-solving using established methodologies (PDCA, A3, etc.)",
        "Respect for frontline operators as the primary source of process insight",
        "Results orientation — KPIs are taken seriously and reviewed frequently",
    ],
}


# ---------------------------------------------------------------------------
# Mock interview question banks — 10 per sector
# ---------------------------------------------------------------------------

_MOCK_QUESTIONS: Dict[str, List[dict]] = {
    "Tech & Software": [
        {
            "question": "Walk me through a system you designed that needed to scale unexpectedly. What decisions did you make under pressure?",
            "guidance": "Focus on the specific architectural choices, the trade-offs you accepted, and what you'd do differently now.",
            "star_template": "Situation: [context and scale], Task: [your responsibility], Action: [specific technical decisions], Result: [measurable outcome — latency, throughput, uptime].",
        },
        {
            "question": "Describe a time you disagreed with a technical direction set by a senior engineer or architect. How did you handle it?",
            "guidance": "Interviewers are testing psychological safety and communication maturity. Show you can disagree respectfully and constructively.",
            "star_template": "Situation: [the technical decision], Task: [your concern], Action: [how you raised it and what data you brought], Result: [what happened and what you learned].",
        },
        {
            "question": "Tell me about the most complex bug you've diagnosed in production. How did you find the root cause?",
            "guidance": "Be specific about your debugging methodology. Mention observability tools, logs, and how you narrowed down hypotheses.",
            "star_template": "Situation: [symptoms and impact], Task: [your role in the investigation], Action: [debugging steps, tools, reasoning], Result: [fix deployed, monitoring added].",
        },
        {
            "question": "How do you decide when technical debt is worth addressing versus when to continue building new features?",
            "guidance": "Frame this as a business decision, not a technical preference. Show you weigh user impact, risk, and velocity.",
            "star_template": "Describe your framework, then give a concrete example where you either chose to address debt or deliberately deferred it — and the outcome.",
        },
        {
            "question": "Describe a project where you mentored a less experienced engineer. What did you focus on, and how did you measure progress?",
            "guidance": "Show that you invest in people, not just code. Mention feedback cadence, code review approach, and how you adapted your style.",
            "star_template": "Situation: [engineer's background and gaps], Task: [your mentoring brief], Action: [specific techniques and feedback], Result: [their growth and team impact].",
        },
        {
            "question": "Tell me about a time you shipped something and it didn't work as expected in production. What happened next?",
            "guidance": "Ownership and post-mortems are critical in strong engineering cultures. Be honest about what went wrong and what changed.",
            "star_template": "Situation: [what shipped], Task: [your role], Action: [how you responded, hotfix, communication], Result: [customer impact mitigated, process improvement].",
        },
        {
            "question": "How do you approach code review, and what do you look for beyond correctness?",
            "guidance": "Talk about readability, maintainability, test coverage, and how you keep reviews collaborative rather than adversarial.",
            "star_template": "Describe your philosophy, then give a specific example of a code review where your feedback improved the codebase or the author's skills.",
        },
        {
            "question": "Describe your experience with CI/CD pipelines. What improvements have you made, and why?",
            "guidance": "Focus on the before/after. Show you understand deployment risk, rollback strategies, and the link between pipeline health and team velocity.",
            "star_template": "Situation: [existing pipeline state], Task: [your remit], Action: [specific changes — tooling, stages, gates], Result: [faster deploys, fewer incidents, time saved].",
        },
        {
            "question": "How do you stay current with evolving technologies, and how do you decide what's worth investing time in versus what's hype?",
            "guidance": "Show intellectual curiosity balanced with pragmatism. Name specific resources, communities, or projects.",
            "star_template": "Describe your learning system, then give an example of a technology you adopted early that paid off, and one you consciously deprioritised.",
        },
        {
            "question": "What's the largest codebase you've worked in, and how did you navigate it as a new contributor?",
            "guidance": "They want to know you can be productive without hand-holding. Mention documentation habits, pairing, and how you ask good questions.",
            "star_template": "Situation: [codebase size and complexity], Task: [your onboarding], Action: [specific strategies to get up to speed], Result: [first meaningful contribution timeline].",
        },
    ],
    "Finance & Banking": [
        {
            "question": "Walk me through a financial model you built under time pressure. How did you ensure accuracy?",
            "guidance": "Demonstrate process discipline — structured assumptions, cross-checks, and clear documentation of key sensitivities.",
            "star_template": "Situation: [context and deadline], Task: [model scope], Action: [methodology, data sources, validation steps], Result: [output quality and decision made].",
        },
        {
            "question": "Describe a time you identified a risk that others had overlooked. How did you present it and what was the outcome?",
            "guidance": "Show independent thinking and the ability to communicate risk clearly to non-specialists.",
            "star_template": "Situation: [context], Task: [your analytical mandate], Action: [how you found and quantified the risk], Result: [action taken, loss avoided].",
        },
        {
            "question": "Tell me about a client or stakeholder who was difficult to manage. How did you maintain the relationship?",
            "guidance": "Focus on active listening, setting clear expectations, and finding common ground on priorities.",
            "star_template": "Situation: [client background and issue], Task: [relationship management], Action: [specific interventions], Result: [relationship outcome, retained mandate or resolved tension].",
        },
        {
            "question": "How do you stay on top of regulatory changes relevant to your area, and how do you translate them into operational requirements?",
            "guidance": "Show you treat regulation as a strategic input, not a compliance checklist.",
            "star_template": "Describe your monitoring process, then give an example where you pre-empted a regulatory change and built readiness before the deadline.",
        },
        {
            "question": "Describe a complex deal or transaction you worked on. What was your role and what made it challenging?",
            "guidance": "Use deal-specific terminology accurately. Focus on your personal contribution, not team-level activity.",
            "star_template": "Situation: [deal structure and context], Task: [your responsibilities], Action: [analysis, negotiations, documentation], Result: [successful close and value delivered].",
        },
        {
            "question": "How have you used data to challenge a prevailing view within your team or with a client?",
            "guidance": "Show analytical courage. Walk through your data, your conclusion, and how you communicated a contrarian view professionally.",
            "star_template": "Situation: [prevailing view], Task: [your independent analysis], Action: [data gathered and how you structured the argument], Result: [decision changed or defended with evidence].",
        },
        {
            "question": "Tell me about a time you had to explain a complex financial concept to a non-financial audience. How did you approach it?",
            "guidance": "Shows communication skills and the ability to simplify without being condescending.",
            "star_template": "Situation: [audience and concept], Task: [your brief], Action: [analogies, visuals, and structure used], Result: [audience understanding and any decisions that followed].",
        },
        {
            "question": "What is your approach to building and stress-testing valuation assumptions?",
            "guidance": "Show that you don't just build the base case — you think adversarially about what could break the thesis.",
            "star_template": "Describe your methodology and give a specific example where your scenario analysis changed the conclusion or the way a deal was structured.",
        },
        {
            "question": "Describe a situation where you made a mistake in your analysis. How did you handle it?",
            "guidance": "Accountability without catastrophising. Show what process you put in place to prevent recurrence.",
            "star_template": "Situation: [the error], Task: [discovery and ownership], Action: [correction and communication], Result: [client or management response, process improvement].",
        },
        {
            "question": "How do you prioritise when you have multiple competing deadlines from different stakeholders?",
            "guidance": "Show structured prioritisation, proactive communication, and the ability to push back when necessary.",
            "star_template": "Describe your prioritisation framework, then give a concrete example where competing demands forced a difficult trade-off and how you resolved it.",
        },
    ],
    "Healthcare & Medical": [
        {
            "question": "Describe a situation where patient safety was at risk. What did you do and what was the outcome?",
            "guidance": "Patient safety is the first principle — demonstrate structured, calm decision-making under pressure.",
            "star_template": "Situation: [clinical context], Task: [your role], Action: [specific interventions and escalation], Result: [patient outcome and any learnings recorded].",
        },
        {
            "question": "Tell me about a time you had to deliver difficult news to a patient or their family. How did you approach it?",
            "guidance": "Show empathy, clear communication, and your understanding of the emotional dimension of clinical work.",
            "star_template": "Situation: [clinical context], Task: [communication brief], Action: [preparation, language used, support offered], Result: [patient/family response and follow-up].",
        },
        {
            "question": "Describe an instance where you disagreed with a clinical decision made by a colleague or superior. What did you do?",
            "guidance": "Show you speak up professionally while respecting clinical hierarchy.",
            "star_template": "Situation: [clinical decision in question], Task: [your concern], Action: [how you raised it, evidence referenced], Result: [outcome and team dynamic].",
        },
        {
            "question": "Walk me through a protocol or process you improved in your current or previous role.",
            "guidance": "Show initiative and structured thinking. Quantify the improvement — time, error rate, patient outcome.",
            "star_template": "Situation: [existing process and its gaps], Task: [your mandate or self-initiated project], Action: [steps taken, stakeholders involved], Result: [measurable improvement].",
        },
        {
            "question": "How do you manage your own wellbeing and resilience in a high-pressure clinical environment?",
            "guidance": "Interviewers want to see genuine self-awareness and sustainable strategies — not platitudes.",
            "star_template": "Describe your specific routines and support structures, then give an example of a period of high pressure and how you navigated it.",
        },
        {
            "question": "Tell me about a time you worked in a multidisciplinary team. What was your contribution and how did you handle any friction?",
            "guidance": "Show you are a collaborative, valuable team member who also advocates for your patients and discipline.",
            "star_template": "Situation: [MDT context], Task: [your role], Action: [contribution and any conflict resolved], Result: [patient outcome and team effectiveness].",
        },
        {
            "question": "Describe a clinical audit or quality improvement project you've been involved in.",
            "guidance": "Show methodological discipline — data collection, analysis, intervention, and re-audit.",
            "star_template": "Situation: [clinical area and gap identified], Task: [audit scope], Action: [methodology and findings], Result: [improvement implemented and re-audited outcome].",
        },
        {
            "question": "How do you keep your clinical knowledge current? Give a recent example.",
            "guidance": "Name specific journals, guidelines, or CPD activities relevant to your specialty.",
            "star_template": "Describe your CPD approach, then walk through one specific piece of evidence you applied to your practice in the last 12 months.",
        },
        {
            "question": "Tell me about a time you had to manage a high caseload with limited resources. How did you prioritise?",
            "guidance": "Show structured triage thinking, proactive communication with supervisors, and safe decision-making.",
            "star_template": "Situation: [caseload and resource constraint], Task: [your responsibility], Action: [triage framework and escalation], Result: [all patients safely managed, no adverse outcomes].",
        },
        {
            "question": "How do you ensure informed consent is genuinely meaningful for patients with varying levels of health literacy?",
            "guidance": "Show patient-centred communication skills and adaptability.",
            "star_template": "Describe your approach, then give an example of a patient who required a different communication strategy and what you did.",
        },
    ],
    "Marketing & Creative": [
        {
            "question": "Walk me through a campaign you led from brief to results. What would you do differently?",
            "guidance": "Show end-to-end ownership — strategy, execution, measurement, and honest reflection.",
            "star_template": "Situation: [brand/business context], Task: [campaign objectives], Action: [strategy, channels, creative choices], Result: [results vs. targets, and learnings].",
        },
        {
            "question": "How do you defend a creative idea when stakeholders want to water it down?",
            "guidance": "Show creative conviction backed by consumer insight and data, not just aesthetic preference.",
            "star_template": "Situation: [idea and stakeholder objection], Task: [your creative stance], Action: [evidence and framing used], Result: [outcome and quality of the work].",
        },
        {
            "question": "Describe a time a campaign underperformed. How did you respond and what did you learn?",
            "guidance": "Show accountability, rapid learning, and what process you put in place for the next campaign.",
            "star_template": "Situation: [campaign context and expectation], Task: [your ownership], Action: [diagnosis, pivot, and communication], Result: [adjusted outcome and process change].",
        },
        {
            "question": "How do you balance brand consistency with the need to personalise at scale?",
            "guidance": "Show you understand both the brand architecture and the data/tech that enables personalisation.",
            "star_template": "Describe your philosophy, then give a specific example where you maintained brand guardrails while executing personalised content at scale.",
        },
        {
            "question": "Tell me about a time you worked with a complex agency or partner relationship. How did you keep the work on track?",
            "guidance": "Show you can be both a demanding client and a collaborative partner.",
            "star_template": "Situation: [agency and project context], Task: [your management role], Action: [briefing, check-ins, and quality control], Result: [output quality and relationship outcome].",
        },
        {
            "question": "How do you approach channel strategy for a new product launch with limited budget?",
            "guidance": "Show strategic prioritisation, audience understanding, and the ability to sequence investment.",
            "star_template": "Describe your methodology, then walk through a specific launch where budget constraints forced creative channel prioritisation.",
        },
        {
            "question": "Describe a time you used consumer or customer data to challenge your own assumptions.",
            "guidance": "Show intellectual honesty and a data-first approach to creative decisions.",
            "star_template": "Situation: [your hypothesis], Task: [research or testing approach], Action: [data gathered], Result: [how the insight changed the strategy and what the outcome was].",
        },
        {
            "question": "How do you measure the success of brand-building activity versus performance marketing?",
            "guidance": "Show you understand the difference between long and short-term metrics and can articulate trade-offs.",
            "star_template": "Describe your measurement framework, then give a specific example where you successfully balanced or reconciled brand and performance metrics for a leadership audience.",
        },
        {
            "question": "Tell me about a time you had to rebuild or reposition a brand. What was your process?",
            "guidance": "Show strategic thinking, stakeholder alignment, and the courage to challenge existing positioning.",
            "star_template": "Situation: [brand context and problem], Task: [repositioning brief], Action: [research, strategy, and execution], Result: [brand perception shift and business outcome].",
        },
        {
            "question": "How do you brief a creative team to get the best possible work?",
            "guidance": "Show that a strong brief is the foundation of great creative — not just a formality.",
            "star_template": "Walk through your briefing structure, then give an example where a well-constructed brief produced significantly better work than the team initially expected.",
        },
    ],
    "Engineering & Operations": [
        {
            "question": "Describe a process failure you were responsible for resolving. How did you diagnose and fix it?",
            "guidance": "Show structured problem-solving (5 Whys, Ishikawa, or equivalent) and clear ownership.",
            "star_template": "Situation: [failure and its impact], Task: [your investigation mandate], Action: [diagnostic process and corrective actions], Result: [recurrence rate, KPI improvement].",
        },
        {
            "question": "Walk me through a continuous improvement project you led. How did you sustain the gains?",
            "guidance": "Show that you focus as much on control and sustainment as you do on the initial improvement.",
            "star_template": "Situation: [process and baseline metric], Task: [improvement scope], Action: [PDCA/Lean/Six Sigma methodology applied], Result: [gain achieved and control mechanism].",
        },
        {
            "question": "Tell me about a time you managed a project that was running late or over budget. What did you do?",
            "guidance": "Show that you escalate early, recalibrate scope honestly, and communicate clearly with stakeholders.",
            "star_template": "Situation: [project status], Task: [your recovery mandate], Action: [specific interventions — descoping, resource, timeline], Result: [delivery outcome and stakeholder response].",
        },
        {
            "question": "How do you handle resistance from the shop floor or operations teams when implementing a process change?",
            "guidance": "Show people skills alongside engineering methodology — change management is as important as the technical solution.",
            "star_template": "Situation: [change and resistance encountered], Task: [your implementation responsibility], Action: [engagement approach — workshops, pilots, advocates], Result: [adoption rate and sustained performance].",
        },
        {
            "question": "Describe a time you identified a safety risk that wasn't being actively managed. What did you do?",
            "guidance": "Show that safety is your personal responsibility, not just a function of the safety team.",
            "star_template": "Situation: [hazard identified], Task: [your escalation responsibility], Action: [steps taken — report, control measures, stakeholder alignment], Result: [risk mitigated, no injuries].",
        },
        {
            "question": "Walk me through your approach to root cause analysis. Give a specific example.",
            "guidance": "Show methodological discipline — distinguish symptoms from causes, and causes from contributing factors.",
            "star_template": "Situation: [problem], Task: [RCA mandate], Action: [method used, team involved, evidence gathered], Result: [verified root cause and corrective action].",
        },
        {
            "question": "How do you balance quality and throughput when facing production pressure?",
            "guidance": "Show that you never compromise safety or quality, but can communicate trade-offs clearly.",
            "star_template": "Describe your principle, then give a specific example where you maintained quality standards under significant throughput pressure.",
        },
        {
            "question": "Tell me about a time you had to manage multiple contractor or vendor relationships simultaneously.",
            "guidance": "Show contract management discipline, clear scope documentation, and supplier performance tracking.",
            "star_template": "Situation: [project scope and vendor landscape], Task: [your oversight responsibility], Action: [governance, performance reviews, issue escalation], Result: [on-time delivery and relationship outcomes].",
        },
        {
            "question": "Describe your experience with capital project planning. How did you manage scope creep?",
            "guidance": "Show structured scope management, change control processes, and stakeholder communication.",
            "star_template": "Situation: [capex project], Task: [your planning role], Action: [scope definition, change control approach], Result: [delivery within budget and schedule].",
        },
        {
            "question": "How do you use data and KPIs to drive operational decisions rather than just reporting them?",
            "guidance": "Show that metrics drive action — not just reports. Describe your cadence and how you build accountability.",
            "star_template": "Describe your KPI governance approach, then give a specific example where a data insight triggered a significant operational change and the measured result.",
        },
    ],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_interview_prep(
    job_title: str,
    company: str,
    sector: str,
    job_description: Optional[str] = None,
    num_questions: int = 8,
) -> dict:
    """
    Generates a full interview prep package:
      - company_brief: 4-sentence contextual summary
      - key_challenges: 3 specific challenges relevant to this company/sector
      - culture_signals: 3 cultural attributes inferred from sector norms
      - mock_questions: num_questions Q&A sets with STAR templates
    """
    challenges = _SECTOR_CHALLENGES.get(sector, _SECTOR_CHALLENGES["Tech & Software"])
    selected_challenges = random.sample(challenges, min(3, len(challenges)))

    culture = _SECTOR_CULTURE_SIGNALS.get(sector, _SECTOR_CULTURE_SIGNALS["Tech & Software"])
    selected_culture = random.sample(culture, min(3, len(culture)))

    questions_pool = _MOCK_QUESTIONS.get(sector, _MOCK_QUESTIONS["Tech & Software"])
    selected_questions = random.sample(questions_pool, min(num_questions, len(questions_pool)))

    company_brief = _build_company_brief(job_title, company, sector, job_description)

    return {
        "job_title": job_title,
        "company": company,
        "sector": sector,
        "company_brief": company_brief,
        "key_challenges": selected_challenges,
        "culture_signals": selected_culture,
        "mock_questions": selected_questions,
    }


def _build_company_brief(
    job_title: str,
    company: str,
    sector: str,
    job_description: Optional[str],
) -> str:
    sector_context = {
        "Tech & Software": (
            f"{company} operates in the technology sector, competing for engineering talent in a market "
            f"where product velocity and platform reliability are core differentiators. "
        ),
        "Finance & Banking": (
            f"{company} is a financial services organisation navigating evolving regulatory requirements "
            f"while competing on analytical capability and client relationships. "
        ),
        "Healthcare & Medical": (
            f"{company} operates in healthcare, where patient outcomes, clinical safety, and regulatory "
            f"compliance are the non-negotiable foundations of every decision. "
        ),
        "Marketing & Creative": (
            f"{company} is a brand or agency competing for attention in a fragmented media landscape, "
            f"where creative rigour and measurable outcomes must coexist. "
        ),
        "Engineering & Operations": (
            f"{company} is an industrial or operational organisation where process efficiency, safety culture, "
            f"and supply chain reliability define competitive advantage. "
        ),
    }

    base = sector_context.get(sector, sector_context["Tech & Software"])

    closing = (
        f"The {job_title} role sits at the intersection of technical execution and business impact. "
        f"Interviewers will be looking for evidence of structured thinking, clear ownership, and the "
        f"ability to operate effectively within {company}'s working environment."
    )

    return base + closing
