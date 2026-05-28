"""
ATS Profile Builder — Path B onboarding.

Takes structured manual intake form data and produces a clean, ATS-optimized
plain-text CV with region-specific spelling, sector keyword injection, and
natural professional prose. No LLM required; entirely deterministic.
"""

import re
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# UK/EU vs US/CA spelling variants applied to the summary block
# ---------------------------------------------------------------------------

_UK_SPELLINGS = {
    "organize": "organise",
    "organized": "organised",
    "organizing": "organising",
    "organization": "organisation",
    "recognize": "recognise",
    "recognized": "recognised",
    "analyze": "analyse",
    "analyzed": "analysed",
    "analyzing": "analysing",
    "utilize": "utilise",
    "utilized": "utilised",
    "utilizing": "utilising",
    "behavior": "behaviour",
    "behavioral": "behavioural",
    "color": "colour",
    "favor": "favour",
    "honor": "honour",
    "labor": "labour",
    "neighbor": "neighbour",
    "program": "programme",  # non-software context
    "center": "centre",
    "defense": "defence",
    "license": "licence",
    "practice": "practise",   # verb form
    "traveled": "travelled",
    "traveling": "travelling",
    "fulfil": "fulfil",
    "skillset": "skill set",
    "skillsets": "skill sets",
}

_UK_REGIONS = {
    "UK", "IRELAND", "AUSTRALIA", "NEW_ZEALAND",
    "GERMANY", "FRANCE", "NETHERLANDS", "SPAIN",
}


def _apply_regional_spelling(text: str, country: str) -> str:
    if country not in _UK_REGIONS:
        return text
    for us, uk in _UK_SPELLINGS.items():
        text = re.sub(rf"\b{us}\b", uk, text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# ATS keyword banks per sector — injected into Skills section
# ---------------------------------------------------------------------------

_SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "Tech & Software": [
        "Agile", "Scrum", "CI/CD", "DevOps", "REST APIs", "Microservices",
        "Cloud Infrastructure", "System Design", "Code Review", "TDD",
        "Version Control", "Distributed Systems", "Data Pipelines",
    ],
    "Finance & Banking": [
        "Financial Modelling", "Risk Management", "Portfolio Analysis",
        "Regulatory Compliance", "Basel III", "IFRS", "P&L Management",
        "Due Diligence", "Capital Markets", "Derivatives", "Asset Allocation",
        "Anti-Money Laundering", "KYC", "CFA",
    ],
    "Healthcare & Medical": [
        "Clinical Research", "Patient Safety", "GCP", "ICH Guidelines",
        "Regulatory Affairs", "Pharmacovigilance", "Electronic Health Records",
        "Clinical Trial Management", "Medical Writing", "CDISC",
        "NHS", "CQC", "MHRA", "HIPAA",
    ],
    "Marketing & Creative": [
        "Brand Strategy", "Campaign Management", "SEO/SEM", "Content Strategy",
        "Marketing Automation", "CRM", "A/B Testing", "Paid Media",
        "Conversion Optimisation", "Market Research", "Google Analytics",
        "Social Media Strategy", "HubSpot", "Salesforce",
    ],
    "Engineering & Operations": [
        "Process Improvement", "Lean Manufacturing", "Six Sigma",
        "Project Management", "Supply Chain Management", "Root Cause Analysis",
        "FMEA", "ISO 9001", "CAD/CAM", "ERP Systems", "KPI Reporting",
        "Continuous Improvement", "Quality Assurance", "Health & Safety",
    ],
}

_LEVEL_LABELS = {
    "junior": "Graduate / Junior",
    "mid": "Mid-Level Professional",
    "senior": "Senior Professional",
    "executive": "Senior Executive / Director",
}


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _divider() -> str:
    return "─" * 56


def _build_header(data: dict, country: str) -> str:
    lines = [data.get("full_name", "").upper()]
    if data.get("target_role"):
        lines.append(data["target_role"])

    contact_parts = []
    if data.get("location"):
        contact_parts.append(data["location"])
    if data.get("email"):
        contact_parts.append(data["email"])
    if data.get("phone"):
        contact_parts.append(data["phone"])
    if data.get("linkedin_url"):
        contact_parts.append(data["linkedin_url"].replace("https://", ""))
    if data.get("github_url"):
        contact_parts.append(data["github_url"].replace("https://", ""))

    if contact_parts:
        lines.append("  |  ".join(contact_parts))

    return "\n".join(lines)


def _build_summary(data: dict, sector: str, country: str) -> str:
    summary = data.get("professional_summary", "")
    if not summary:
        level_label = _LEVEL_LABELS.get(data.get("target_level", "mid"), "Mid-Level Professional")
        role = data.get("target_role", "professional")
        summary = (
            f"{level_label} with experience in {sector}. "
            f"Seeking a {role} role where I can apply my background to deliver measurable results."
        )
    summary = _apply_regional_spelling(summary, country)
    return f"PROFESSIONAL SUMMARY\n{_divider()}\n{summary}"


def _build_experience(entries: List[dict], country: str) -> str:
    if not entries:
        return ""
    lines = [f"PROFESSIONAL EXPERIENCE\n{_divider()}"]
    for exp in entries:
        title = exp.get("title", "")
        company = exp.get("company", "")
        location = exp.get("location", "")
        start = exp.get("start", "")
        end = exp.get("end", "Present")
        period = f"{start} – {end}" if start else end

        header_parts = [p for p in [title, company, location, period] if p]
        lines.append("\n" + "  |  ".join(header_parts))

        bullets = exp.get("bullets", [])
        if isinstance(bullets, str):
            bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
        for bullet in bullets:
            bullet = _apply_regional_spelling(bullet, country)
            lines.append(f"  •  {bullet}")

    return "\n".join(lines)


def _build_education(entries: List[dict]) -> str:
    if not entries:
        return ""
    lines = [f"EDUCATION\n{_divider()}"]
    for edu in entries:
        degree = edu.get("degree", "")
        institution = edu.get("institution", "")
        year = edu.get("year", "")
        honours = edu.get("honours", "")

        parts = [p for p in [degree, institution, year] if p]
        line = "  |  ".join(parts)
        if honours:
            line += f"  ({honours})"
        lines.append(line)
    return "\n".join(lines)


def _build_skills(
    technical: List[str],
    soft: List[str],
    sector: str,
    certifications: List[str],
) -> str:
    injected_keywords = _SECTOR_KEYWORDS.get(sector, [])
    all_technical = list(dict.fromkeys(technical + injected_keywords))  # deduplicate, preserve order

    lines = [f"SKILLS & COMPETENCIES\n{_divider()}"]
    if all_technical:
        lines.append("Technical: " + "  •  ".join(all_technical))
    if soft:
        lines.append("Professional: " + "  •  ".join(soft))
    if certifications:
        lines.append(f"\nCERTIFICATIONS\n{_divider()}")
        for cert in certifications:
            lines.append(f"  •  {cert}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_ats_cv(
    manual_data: dict,
    country: str,
    sector: str,
) -> str:
    """
    Produces a clean, ATS-optimized plain-text CV from manual profile data.

    Args:
        manual_data: dict matching the ManualProfile model fields
        country:     CountryEnum value string, e.g. "UK"
        sector:      SectorEnum value string, e.g. "Finance & Banking"

    Returns:
        Formatted plain-text CV string ready for storage and display
    """
    sections = []

    sections.append(_build_header(manual_data, country))
    sections.append("")
    sections.append(_build_summary(manual_data, sector, country))
    sections.append("")

    experience = manual_data.get("experience_entries") or []
    exp_block = _build_experience(experience, country)
    if exp_block:
        sections.append(exp_block)
        sections.append("")

    skills_block = _build_skills(
        manual_data.get("skills_technical") or [],
        manual_data.get("skills_soft") or [],
        sector,
        manual_data.get("certifications") or [],
    )
    sections.append(skills_block)
    sections.append("")

    education = manual_data.get("education_entries") or []
    edu_block = _build_education(education)
    if edu_block:
        sections.append(edu_block)

    return "\n".join(sections).strip()
