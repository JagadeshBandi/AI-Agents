"""
Humanized cover letter and application answer generator.

Produces professional prose that reads like a real person wrote it.
Banned phrases are actively stripped. Vocabulary is keyed by sector and tone.
"""

import re
import random
from typing import Dict, List, Optional

_BANNED = [
    "in today's fast-paced", "fast-paced digital landscape", "delve", "delving",
    "moreover", "testament to", "leverage synergies", "synergize", "circle back",
    "cutting-edge", "cutting edge", "passionate about disruption", "dynamic individual",
    "go-getter", "thought leader", "paradigm shift", "game-changer", "game changer",
    "move the needle", "deep dive", "bandwidth", "touch base", "boil the ocean",
    "low-hanging fruit", "at the end of the day", "it is what it is",
    "think outside the box", "value add", "value-add", "proactive approach",
    "synergy", "robust solution", "results-driven", "self-starter", "detail-oriented",
    "I am passionate about", "I have always been passionate",
]


def _sanitize(text: str) -> str:
    for phrase in _BANNED:
        text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)
    return re.sub(r" {2,}", " ", text).strip()


SECTOR_VOCABULARY: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "Tech & Software": {
        "professional": {
            "openings": [
                "I'm applying for the {title} role at {company} because my engineering background aligns directly with what you're building.",
                "The {title} position at {company} caught my attention — your focus on {highlight} matches the kind of work I've been doing for the past several years.",
                "Your posting for {title} at {company} describes exactly the kind of challenge I'm looking for next.",
            ],
            "transitions": ["Throughout my career,", "In my current role,", "My recent experience includes", "Over the past few years,"],
            "achievements": [
                "reduced deployment time by automating the release pipeline",
                "improved API response latency through targeted query optimisation",
                "built a microservices architecture that scaled to support a 3× user increase",
                "shipped features on a two-week release cycle across a distributed team",
            ],
            "closings": [
                "I'd welcome the chance to discuss how my experience maps to your requirements.",
                "Happy to talk through any aspect of my background in more detail.",
                "I look forward to the opportunity to contribute to your engineering work.",
            ],
        },
        "executive": {
            "openings": [
                "The {title} role at {company} aligns with the strategic direction I've been building toward — leading engineering organisations through the complexity of scaling distributed systems.",
                "I'm writing about the {title} position at {company}. Having built and led engineering teams through significant growth cycles, I bring both the strategic overview and technical depth this role demands.",
            ],
            "transitions": ["At executive level, I've consistently", "Across the organisations I've led,", "My approach to engineering leadership has been shaped by"],
            "achievements": [
                "built an engineering organisation from 8 to 45 engineers while maintaining a quarterly release cadence",
                "established a platform architecture that reduced infrastructure costs by 34% over 18 months",
                "created a technical roadmap that aligned engineering investment with a three-year product strategy",
            ],
            "closings": [
                "I would welcome a conversation about how this experience applies to your organisation's current priorities.",
                "I'm happy to discuss the specifics of how I'd approach the challenges facing your engineering function.",
            ],
        },
        "friendly": {
            "openings": [
                "I came across the {title} role at {company} and it immediately stood out — this is the kind of work I genuinely enjoy.",
                "When I saw the {title} opening at {company}, it felt like a natural next step from what I've been building toward.",
            ],
            "transitions": ["What I've found in my work so far is that", "One thing I really enjoy is", "I've spent a good chunk of my career"],
            "achievements": [
                "helped the team move from monthly to weekly deploys by rebuilding the CI pipeline",
                "turned a fairly painful microservices migration into a smooth handover by running weekly syncs",
                "spent three months fixing a data pipeline that had been causing intermittent failures — finally got it stable",
            ],
            "closings": [
                "I'd love to chat more about the role if you think there's a good fit.",
                "Thanks for considering my application — I'd be glad to answer any questions.",
            ],
        },
    },
    "Finance & Banking": {
        "professional": {
            "openings": [
                "I'm applying for the {title} position at {company}. My background in financial analysis and risk management maps closely to your requirements.",
                "The {title} role at {company} aligns with the analytical and client-facing work I've been doing throughout my finance career.",
                "Your posting for {title} at {company} describes exactly the scope of work I'm ready to step into next.",
            ],
            "transitions": ["In my current role,", "Across my career in financial services,", "My analytical work has consistently involved"],
            "achievements": [
                "built credit risk models that reduced non-performing loan exposure by 18%",
                "managed a £240M portfolio through a period of significant market volatility without exceeding VaR thresholds",
                "streamlined the quarterly regulatory reporting process, cutting preparation time by 40%",
                "delivered financial due diligence on seven acquisitions across a two-year period",
            ],
            "closings": [
                "I'd welcome the opportunity to discuss how my analytical background fits your current requirements.",
                "I look forward to the possibility of contributing to your finance function.",
            ],
        },
        "executive": {
            "openings": [
                "The {title} role at {company} aligns with the senior finance leadership trajectory I've been building — managing capital allocation, regulatory relationships, and cross-functional financial strategy.",
                "I'm writing to express my interest in the {title} position at {company}. My career in financial services has centred on combining rigorous analytical work with clear strategic communication to leadership.",
            ],
            "transitions": ["At senior level, I have consistently", "My approach to financial leadership", "The organisations I've worked with have valued my ability to"],
            "achievements": [
                "chaired the credit committee overseeing a £1.2B lending portfolio with zero material losses over four years",
                "led a finance transformation that consolidated three legacy reporting systems and reduced the month-end close from 12 days to 5",
                "built the investor relations function from scratch, culminating in a successful Series C raise of $80M",
            ],
            "closings": [
                "I'd welcome a conversation about how this experience aligns with your strategic priorities.",
                "I'm happy to discuss the specifics of my background and how they apply to this position.",
            ],
        },
        "friendly": {
            "openings": [
                "I came across the {title} role at {company} and it caught my eye straight away — the focus on {highlight} is exactly the kind of work I find most engaging.",
                "When I read the {title} spec at {company}, it felt like a genuine match for where I am in my finance career.",
            ],
            "transitions": ["What I've particularly enjoyed in my career so far is", "I've spent a lot of my time focused on", "One area where I've built real experience is"],
            "achievements": [
                "built out a financial reporting dashboard that the CFO now uses as the primary board pack — saved about two days of prep work per quarter",
                "got involved in three M&A deals in one year, which was intense but genuinely excellent experience",
            ],
            "closings": [
                "Would be great to chat if you think there could be a fit.",
                "Thanks for looking at my application — happy to answer any questions.",
            ],
        },
    },
    "Healthcare & Medical": {
        "professional": {
            "openings": [
                "I'm applying for the {title} role at {company}. My clinical background and commitment to patient-centred care aligns directly with your organisation's priorities.",
                "The {title} position at {company} attracted my interest because your approach to {highlight} reflects the kind of clinical environment I've been building my career around.",
                "Your {title} role at {company} describes exactly the scope of practice I'm ready to step into.",
            ],
            "transitions": ["In my current clinical role,", "Across my healthcare career,", "My patient care work has involved"],
            "achievements": [
                "reduced average patient wait times by 22% through restructuring the triage assessment process",
                "maintained a zero serious incident rate across 18 months of clinical oversight",
                "trained and mentored four junior clinicians who are now practising independently",
                "led a service improvement audit that identified and resolved a recurring medication administration issue",
            ],
            "closings": [
                "I'd welcome the opportunity to discuss how my clinical experience fits your team's needs.",
                "I look forward to the possibility of contributing to patient care at {company}.",
            ],
        },
        "executive": {
            "openings": [
                "The {title} role at {company} aligns with the senior clinical leadership work I've been building — overseeing service delivery, quality governance, and staff development across complex clinical environments.",
                "I'm writing to express my interest in the {title} position at {company}. My career has centred on combining strong clinical foundations with the operational and strategic thinking that senior healthcare roles demand.",
            ],
            "transitions": ["At director level, I have", "The clinical organisations I've led", "My approach to healthcare leadership"],
            "achievements": [
                "led a service redesign that improved patient throughput by 30% without increasing headcount",
                "built a governance framework that maintained CQC Outstanding rating across two successive inspections",
                "managed a multidisciplinary team of 60 clinical and non-clinical staff through a significant organisational restructure",
            ],
            "closings": [
                "I would welcome a conversation about how this experience applies to your clinical leadership priorities.",
                "I'm happy to discuss the specifics of my background in more detail.",
            ],
        },
        "friendly": {
            "openings": [
                "I saw the {title} role at {company} and it immediately felt like a strong fit for where I am in my clinical career.",
                "The {title} position at {company} caught my attention — the patient population and service model align well with the work I've been doing.",
            ],
            "transitions": ["What I've always found most rewarding in clinical work is", "I've spent most of my career focused on", "One area where I've put a lot of energy is"],
            "achievements": [
                "spent two years building a patient education programme that's now used across the whole department",
                "got involved in a service review that turned into a proper quality improvement project — ended up reducing readmissions",
            ],
            "closings": [
                "Would genuinely love to discuss the role if you think there's a fit.",
                "Thanks for reading — happy to chat further about my background.",
            ],
        },
    },
    "Marketing & Creative": {
        "professional": {
            "openings": [
                "I'm applying for the {title} position at {company}. My background in brand strategy and campaign management aligns with what you're building.",
                "The {title} role at {company} caught my interest because your focus on {highlight} matches the work I've been doing across my marketing career.",
                "Your {title} posting at {company} describes exactly the kind of cross-channel challenge I'm looking for next.",
            ],
            "transitions": ["In my current role,", "Across the campaigns I've led,", "My marketing work has consistently focused on"],
            "achievements": [
                "led a product launch campaign that delivered 140% of the target sign-up volume in the first month",
                "rebuilt the content strategy from scratch, increasing organic traffic by 68% over 12 months",
                "managed a £1.2M media budget across paid and organic channels, delivering 22% below target CPL",
                "negotiated and managed three agency relationships, consistently hitting brand standards while reducing costs",
            ],
            "closings": [
                "I'd welcome the chance to discuss how my experience aligns with your marketing priorities.",
                "I look forward to the possibility of contributing to {company}'s brand work.",
            ],
        },
        "executive": {
            "openings": [
                "The {title} role at {company} aligns with the senior marketing leadership trajectory I've been building — overseeing brand strategy, commercial positioning, and full-funnel performance.",
                "I'm writing about the {title} position at {company}. My career has combined brand-building rigour with direct commercial accountability, which I understand is central to this role.",
            ],
            "transitions": ["At CMO level, I've consistently", "The brands I've built and led", "My marketing leadership philosophy"],
            "achievements": [
                "repositioned a £400M consumer brand, resulting in a 12-point NPS improvement and 9% market share gain over 24 months",
                "built a marketing function from five to twenty-two people while maintaining cost-per-acquisition targets",
                "led the global campaign strategy for a product launch across 14 markets, coordinating five regional agency partners",
            ],
            "closings": [
                "I'd welcome a conversation about how this experience maps to your strategic marketing priorities.",
                "I'm happy to discuss the specifics of my background and how they apply to your growth agenda.",
            ],
        },
        "friendly": {
            "openings": [
                "I came across the {title} role at {company} and it stood out immediately — the brand challenges you're working on are exactly the kind I enjoy most.",
                "When I read the {title} spec at {company}, it felt like a natural next chapter.",
            ],
            "transitions": ["What I've found throughout my marketing career is", "I've spent a lot of time focused on", "One area where I've really developed is"],
            "achievements": [
                "ran a rebrand project end-to-end — from brief to final assets — which ended up winning an industry award",
                "took over a campaign that was underperforming and turned it around within six weeks by changing the targeting and creative",
            ],
            "closings": [
                "Would be great to connect if you think it could be a good match.",
                "Thanks for considering my application — I'd love to chat further.",
            ],
        },
    },
    "Engineering & Operations": {
        "professional": {
            "openings": [
                "I'm applying for the {title} position at {company}. My background in process engineering and operations management aligns directly with your requirements.",
                "The {title} role at {company} caught my attention because your operational focus on {highlight} matches the work I've been leading.",
                "Your {title} posting at {company} describes exactly the kind of structured operational challenge I'm ready to step into.",
            ],
            "transitions": ["In my current role,", "Across my engineering career,", "My operational work has consistently focused on"],
            "achievements": [
                "implemented a lean manufacturing programme that reduced process waste by 28% within 12 months",
                "led a capital project that came in 8% under budget and three weeks ahead of schedule",
                "reduced equipment downtime by 35% through a predictive maintenance programme",
                "managed a cross-functional team through a major ISO 9001 audit with zero non-conformances raised",
            ],
            "closings": [
                "I'd welcome the opportunity to discuss how my engineering background fits your operational priorities.",
                "I look forward to the possibility of contributing to {company}'s operations team.",
            ],
        },
        "executive": {
            "openings": [
                "The {title} role at {company} aligns with the senior operations leadership work I've been building — overseeing multi-site manufacturing, supply chain strategy, and continuous improvement culture.",
                "I'm writing to express my interest in the {title} position at {company}. My career has centred on building operational capability at scale while maintaining safety and quality as non-negotiables.",
            ],
            "transitions": ["At VP/Director level, I've consistently", "The operations functions I've led", "My approach to engineering leadership"],
            "achievements": [
                "led a five-site manufacturing network through a major ERP implementation with zero production line stoppages",
                "delivered £18M in annualised savings over three years through a systematic lean transformation programme",
                "reduced total recordable injury rate by 62% over four years by overhauling the safety management system",
            ],
            "closings": [
                "I'd welcome a conversation about how this experience applies to your operational priorities.",
                "I'm happy to discuss the specifics of my background in detail.",
            ],
        },
        "friendly": {
            "openings": [
                "I came across the {title} role at {company} and it caught my eye straight away — the operational challenges you're working on are exactly the kind I find most engaging.",
                "When I saw the {title} spec at {company}, it felt like a strong fit for the next step in my engineering career.",
            ],
            "transitions": ["What I've found throughout my operations career is", "I've spent a lot of time working on", "One area where I've built real experience is"],
            "achievements": [
                "ran a process improvement project that ended up saving the team about eight hours of rework per week",
                "managed the site's first external quality audit — it went well and the auditors specifically commented on our documentation",
            ],
            "closings": [
                "Would be great to discuss the role if you think there's a fit.",
                "Thanks for considering my application — happy to answer any questions.",
            ],
        },
    },
}


def generate_cover_letter(
    title: str,
    company: str,
    sector: str,
    tone: str = "professional",
    highlight: Optional[str] = None,
) -> str:
    vocab = SECTOR_VOCABULARY.get(sector, SECTOR_VOCABULARY["Tech & Software"])
    tone_data = vocab.get(tone, vocab.get("professional"))

    highlight = highlight or "your work in this space"
    opening = random.choice(tone_data["openings"]).format(
        title=title, company=company, highlight=highlight
    )
    transition = random.choice(tone_data["transitions"])
    achievements = random.sample(tone_data["achievements"], min(2, len(tone_data["achievements"])))
    closing = random.choice(tone_data["closings"]).format(company=company)

    letter = (
        f"Dear Hiring Manager,\n\n"
        f"{opening}\n\n"
        f"{transition} I've focused on delivering work with measurable impact. "
        f"Specifically, I {achievements[0]}"
        + (f", and I {achievements[1]}." if len(achievements) > 1 else ".")
        + f"\n\n"
        f"I'm confident that the combination of my technical background and "
        f"collaborative approach would make me a strong addition to the team at {company}.\n\n"
        f"{closing}\n\n"
        f"Yours sincerely,\n[Your Name]"
    )

    return _sanitize(letter)


def generate_application_answers(
    question_type: str,
    sector: str,
    tone: str = "professional",
    company: Optional[str] = None,
) -> str:
    handlers = {
        "motivation": _answer_motivation,
        "strengths": _answer_strengths,
        "challenge": _answer_challenge,
        "teamwork": _answer_teamwork,
    }
    fn = handlers.get(question_type, _answer_generic)
    return _sanitize(fn(sector, tone, company))


def _answer_motivation(sector: str, tone: str, company: Optional[str]) -> str:
    co = company or "your organisation"
    sector_hooks = {
        "Tech & Software": f"I'm drawn to {co} because of the engineering challenges at your scale. Building systems that hold up under real-world pressure is what I find most rewarding.",
        "Finance & Banking": f"What draws me to {co} is the combination of analytical rigour and real commercial consequence. I want to work somewhere where the quality of thinking directly shapes outcomes.",
        "Healthcare & Medical": f"I'm motivated by patient impact. {co}'s reputation for clinical excellence makes it somewhere I'd be proud to contribute my skills.",
        "Marketing & Creative": f"I'm drawn to {co} because the brand challenges here are genuinely interesting. I want to work somewhere that values both creative ambition and commercial discipline.",
        "Engineering & Operations": f"What draws me to {co} is the operational complexity and the emphasis on continuous improvement. I find the work of building robust, efficient systems genuinely engaging.",
    }
    return sector_hooks.get(sector, f"I'm drawn to {co} because the work aligns with where I want to take my career next.")


def _answer_strengths(sector: str, tone: str, company: Optional[str]) -> str:
    sector_strengths = {
        "Tech & Software": "My strongest areas are system design and clear technical communication. I'm good at breaking down complex problems into components others can work on independently, and I take code review seriously as a way of raising team-wide quality.",
        "Finance & Banking": "My core strengths are financial modelling and risk identification. I bring a structured approach to ambiguous problems and I'm direct in communicating conclusions — even when they're not what stakeholders want to hear.",
        "Healthcare & Medical": "My strongest areas are clinical assessment and patient communication. I'm thorough in my decision-making and I'm comfortable escalating when something doesn't look right, even under time pressure.",
        "Marketing & Creative": "My core strengths are brand strategy and using data to inform creative decisions. I'm good at translating consumer insight into clear briefs, and I hold agencies to a high standard without damaging the working relationship.",
        "Engineering & Operations": "My strongest areas are process analysis and root cause investigation. I take a structured approach to problems and I'm patient enough to find the actual cause rather than the closest plausible one.",
    }
    return sector_strengths.get(sector, "My strongest area is structured problem-solving. I take a methodical approach and I communicate my reasoning clearly throughout the process.")


def _answer_challenge(sector: str, tone: str, company: Optional[str]) -> str:
    return (
        "One of the more demanding situations I've faced was inheriting a project mid-way through that had scope issues and unclear ownership. "
        "Rather than taking it at face value, I spent the first two weeks mapping what had actually been agreed versus what was assumed. "
        "Once I had a clear picture, I restructured the delivery plan and had a direct conversation with the senior stakeholders to reset expectations. "
        "It wasn't entirely comfortable, but it meant we finished with something that actually worked rather than something that had been shipped in a hurry."
    )


def _answer_teamwork(sector: str, tone: str, company: Optional[str]) -> str:
    return (
        "I work well in cross-functional teams because I make a point of understanding what other disciplines actually need, not just what I think they need. "
        "In a recent project, I was working alongside people from three different teams with genuinely different priorities. "
        "I spent time early on making sure we had shared language around what success looked like, which meant we avoided a lot of the friction that usually comes up mid-project. "
        "The collaboration worked well because everyone felt their constraints had been heard."
    )


def _answer_generic(sector: str, tone: str, company: Optional[str]) -> str:
    return (
        "I approach this kind of question by focusing on specific examples rather than generalisations. "
        "The most relevant thing I can offer is a direct account of what I've done, why I made the decisions I made, "
        "and what I'd adjust if I were doing it again — which I think is more useful than a polished description of attributes."
    )
