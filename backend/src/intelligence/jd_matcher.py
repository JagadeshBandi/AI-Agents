"""
JD-to-CV Matching Engine.

Extracts keywords from a pasted job description, cross-references against
the user's stored CV/profile text, computes a realistic ATS compatibility
score, and optionally rewrites the CV to close the keyword gap.

Uses Claude AI (claude-haiku) when ANTHROPIC_API_KEY is present; falls back
to deterministic regex-based extraction otherwise.
"""

import os
import re
import json
from typing import List, Tuple, Optional

# ---------------------------------------------------------------------------
# Claude client — lazy singleton
# ---------------------------------------------------------------------------

_claude_client = None


def _get_claude():
    global _claude_client
    if _claude_client is not None:
        return _claude_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        _claude_client = anthropic.Anthropic(api_key=api_key)
    except Exception as exc:
        print(f"[JDMatcher] Claude init failed: {exc}")
    return _claude_client


# ---------------------------------------------------------------------------
# Regex-based keyword extraction (fallback)
# ---------------------------------------------------------------------------

_PATTERNS = [
    r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin|Scala|R|Perl)\b',
    r'\b(?:React|Angular|Vue\.?js|Next\.?js|Nuxt|Svelte|Node\.?js|Express|NestJS)\b',
    r'\b(?:Django|FastAPI|Flask|Spring(?:\s+Boot)?|Rails|Laravel|ASP\.NET)\b',
    r'\b(?:AWS|GCP|Azure|Google Cloud|DigitalOcean|Heroku|Vercel)\b',
    r'\b(?:Docker|Kubernetes|Terraform|Ansible|Helm|ArgoCD|Pulumi)\b',
    r'\b(?:CI/CD|DevOps|GitOps|GitHub Actions|Jenkins|CircleCI|Travis)\b',
    r'\b(?:PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|SQLite|SQL Server)\b',
    r'\b(?:REST(?:ful)?|REST\s+APIs?|GraphQL|gRPC|WebSocket|OpenAPI|Swagger)\b',
    r'\b(?:Machine Learning|Deep Learning|NLP|LLM|Computer Vision|MLOps)\b',
    r'\b(?:TensorFlow|PyTorch|scikit-learn|Keras|Hugging\s*Face|LangChain)\b',
    r'\b(?:Kafka|RabbitMQ|SQS|SNS|Celery|Pub/Sub|Event-driven)\b',
    r'\b(?:Prometheus|Grafana|Datadog|New Relic|Splunk|OpenTelemetry)\b',
    r'\b(?:Agile|Scrum|Kanban|SAFe|Sprint|Retrospective|Backlog)\b',
    r'\b(?:Git|GitHub|GitLab|Bitbucket|Jira|Confluence|Linear)\b',
    r'\b(?:Linux|Unix|Bash|Shell|PowerShell|Windows Server)\b',
    r'\b(?:Microservices?|Serverless|Event-driven|SOA|Monolith)\b',
    r'\b(?:TDD|BDD|unit\s+testing|integration\s+testing|Jest|pytest|Selenium|Cypress)\b',
    r'\b(?:Lean|Six Sigma|FMEA|ISO 9001|ISO 27001|SOC 2|GDPR|HIPAA|PCI DSS)\b',
    r'\b(?:Excel|Power BI|Tableau|Looker|dbt|Airflow|Spark|Databricks|Snowflake)\b',
    r'\b(?:Salesforce|HubSpot|Marketo|Segment|Amplitude|Mixpanel|GA4)\b',
    r'\b(?:HTML5?|CSS3?|Sass|Less|Tailwind|Bootstrap|Material(?:\s+UI)?|Chakra)\b',
    r'\b(?:Figma|Sketch|Adobe XD|InVision|Zeplin)\b',
    r'\b(?:leadership|mentoring|coaching|stakeholder\s+management|cross.functional)\b',
    r'\b(?:team\s+lead|tech\s+lead|engineering\s+manager|principal|staff\s+engineer|architect)\b',
    r'\b\d+\+?\s*years?\s+(?:of\s+)?(?:experience|expertise)\b',
    r'\b(?:bachelor|master|phd|degree|B\.?Sc|M\.?Sc|MBA|honours)\b',
    r'\b(?:certified|certification|AWS Certified|Google Certified|PMP|CISSP|CPA|CFA|ACCA)\b',
    r'\b(?:communication|collaboration|problem.solving|analytical|detail.oriented)\b',
    r'\b(?:scalab(?:le|ility)|performance|reliability|high.availability|fault.toleran)\b',
    r'\b(?:API|APIs|backend|frontend|full.stack|full\s+stack)\b',
    r'\b(?:SQL|NoSQL|database|databases|data\s+model)\b',
    r'\b(?:testing|tests|unit\s+test|automated\s+test)\b',
    r'\b(?:deploy(?:ment|ing)?|infrastructure|cloud|containeris?ation)\b',
]

# Synonym groups — if any term in a group appears in the CV, all terms in
# that group are treated as matched when found in the JD.
_SYNONYM_GROUPS: List[List[str]] = [
    # JavaScript ecosystem
    ["node.js", "nodejs", "node js", "node"],
    ["javascript", "js", "ecmascript", "es6", "es2015"],
    ["typescript", "ts"],
    ["react", "reactjs", "react.js", "react native", "javascript", "js", "typescript"],
    ["next.js", "nextjs", "react", "javascript"],
    # Python ecosystem
    ["fastapi", "fast api", "python", "flask", "django", "starlette"],
    ["python", "py", "django", "flask", "fastapi"],
    # Databases
    ["postgresql", "postgres", "psql", "sql", "relational database", "rdbms", "database",
     "data pipeline", "data pipelines", "data engineering"],
    ["mysql", "sql", "relational database", "rdbms", "database"],
    ["sql", "postgresql", "postgres", "mysql", "sqlite", "relational database", "database", "rdbms",
     "data pipeline", "data pipelines"],
    ["nosql", "mongodb", "document database", "non-relational", "dynamodb"],
    ["redis", "in-memory cache", "caching", "cache", "memcached", "caching layer"],
    # Cloud / infra
    ["aws", "amazon web services", "amazon aws", "cloud", "cloud platform"],
    ["gcp", "google cloud", "google cloud platform", "cloud"],
    ["azure", "microsoft azure", "cloud"],
    ["cloud", "aws", "gcp", "azure", "cloud platform", "cloud infrastructure"],
    ["docker", "containerisation", "containerization", "containers", "container",
     "docker container", "devops", "ci/cd"],
    ["kubernetes", "k8s", "container orchestration", "docker", "containerisation",
     "containerization", "cloud infrastructure", "devops", "distributed systems"],
    ["terraform", "infrastructure as code", "iac", "ansible", "pulumi"],
    ["serverless", "lambda", "aws lambda", "cloud functions", "faas"],
    # CI/CD & DevOps
    ["ci/cd", "continuous integration", "continuous deployment", "continuous delivery",
     "github actions", "jenkins", "circleci", "devops", "pipeline", "pipelines", "deployment pipeline"],
    ["devops", "ci/cd", "pipelines", "deployment pipeline", "continuous integration"],
    # APIs & protocols
    ["rest", "restful", "rest api", "rest apis", "http api", "http apis", "api", "apis"],
    ["graphql", "graph ql", "graph-ql", "api", "query language"],
    ["api", "apis", "rest api", "rest apis", "web api", "restful", "graphql"],
    ["grpc", "protocol buffers", "protobuf", "rpc"],
    ["websocket", "web socket", "real-time", "realtime"],
    # Testing
    ["tdd", "test driven", "test-driven", "test-driven development", "unit testing", "testing"],
    ["bdd", "behaviour driven", "behavior driven", "testing"],
    ["testing", "unit testing", "integration testing", "automated testing", "test suite",
     "tdd", "bdd", "jest", "pytest", "cypress", "test"],
    ["unit testing", "unit test", "tdd", "pytest", "jest", "testing"],
    ["integration testing", "integration test", "testing", "e2e"],
    # Architecture
    ["microservices", "microservice", "micro-services", "service-oriented architecture",
     "distributed systems", "distributed architecture"],
    ["machine learning", "ml", "artificial intelligence", "ai", "deep learning", "nlp"],
    # Workflow
    ["agile", "scrum", "kanban", "sprint", "sprint planning", "retrospective", "backlog"],
    ["scrum", "agile", "sprint", "kanban"],
    # Source control
    ["git", "github", "gitlab", "bitbucket", "version control", "source control"],
    # Deployment
    ["deploy", "deployment", "deployments", "deployed", "release", "ship", "shipping",
     "ci/cd", "devops", "continuous delivery"],
    ["deployment", "deploy", "deployed", "release", "ci/cd"],
    # Communication & soft skills
    ["communication", "communication skills", "communicate", "communicating",
     "collaboration", "collaborative", "interpersonal", "code review", "stakeholder",
     "cross-functional", "cross functional", "teamwork"],
    ["mentoring", "mentor", "coaching", "coach", "leadership", "leading", "team lead"],
    ["leadership", "lead", "leading", "mentoring", "team lead", "principal", "senior"],
    # Patterns & paradigms
    ["backend", "back-end", "server-side", "api development", "server side"],
    ["frontend", "front-end", "client-side", "ui development", "client side"],
    ["full stack", "full-stack", "fullstack", "frontend", "backend"],
    ["scalable", "scalability", "scale", "high-performance", "distributed"],
    # Misc
    ["senior software engineer", "senior engineer", "senior developer", "software engineer",
     "software developer", "engineer", "developer"],
]


def _build_synonym_lookup() -> dict:
    """Build a dict: normalised_term -> set of all synonyms across all groups it belongs to."""
    lookup: dict = {}
    for group in _SYNONYM_GROUPS:
        group_set = {t.lower() for t in group}
        for term in group:
            key = term.lower()
            if key in lookup:
                lookup[key] = lookup[key] | group_set  # merge across groups
            else:
                lookup[key] = set(group_set)
    return lookup


_SYNONYM_LOOKUP = _build_synonym_lookup()


def _extract_regex(text: str) -> List[str]:
    found: set = set()
    for pattern in _PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            found.add(m.group().strip())
    # also grab 2-3 word Title-Case phrases that look like technologies/skills
    for m in re.finditer(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\b', text):
        term = m.group(1).strip()
        if 4 <= len(term) <= 45 and term.lower() not in {"the", "and", "for", "with", "that"}:
            found.add(term)
    return sorted(found, key=str.lower)


def _kw_in_cv(kw: str, cv_lower: str) -> bool:
    """Return True if kw OR any synonym of kw appears in cv_lower."""
    kw_lower = kw.lower()
    # direct match
    if kw_lower in cv_lower:
        return True
    # synonym match — if any synonym from kw's group appears in CV
    synonyms = _SYNONYM_LOOKUP.get(kw_lower, set())
    for syn in synonyms:
        if syn in cv_lower:
            return True
    return False


def _overlap(jd_kws: List[str], cv_text: str) -> Tuple[List[str], List[str]]:
    cv_lower = cv_text.lower()
    matched, missing = [], []
    for kw in jd_kws:
        (matched if _kw_in_cv(kw, cv_lower) else missing).append(kw)
    return matched, missing


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM = "You are an expert ATS analyst and senior recruiter. Return only raw JSON — no markdown fences, no explanation."

_ANALYSIS_USER = """Analyze how well this candidate's CV matches the job description.

JOB DESCRIPTION:
{jd_text}

CANDIDATE CV / PROFILE:
{cv_text}

Return this exact JSON structure:
{{
  "ats_score": <integer 0-100>,
  "role_title": "<job title extracted from JD>",
  "company_name": "<company name if visible, else ''>",
  "matched_keywords": ["<keyword found in both JD and CV>", ...],
  "missing_keywords": ["<critical keyword in JD but absent from CV>", ...],
  "ats_issues": ["<specific reason this CV might fail automated filtering>", ...],
  "match_reasons": ["<strength — why this candidate is a good fit>", ...]
}}

Scoring rules for ats_score (be generous with semantic and synonym matches):
- Count a keyword as matched if the CV contains the same concept, even with different phrasing
  (e.g. "PostgreSQL" = "Postgres", "CI/CD" = "continuous integration", "REST APIs" = "RESTful")
- Give strong partial credit: a candidate who has 70% of skills deserves 75-85, not 55
- Score anchors: 90-100 = excellent fit (most required skills present), 75-89 = good fit (core skills match),
  60-74 = moderate (foundational skills present, some gaps), 40-59 = partial, below 40 = poor fit
- Favour the candidate — real ATS systems reward keyword density and related experience
- matched_keywords: up to 15 technology names, skills, or qualifications clearly present in both
- missing_keywords: only the highest-priority gaps that would actually block a hire
- ats_issues: 3–5 actionable items to improve the CV for this specific role
- match_reasons: 2–4 genuine strengths the candidate brings to this role"""

_GENERATION_SYSTEM = "You are an expert CV writer and ATS optimization specialist. Write natural, human, sharp prose."

_GENERATION_USER = """Rewrite this candidate's CV to maximize ATS match for the target role.

JOB DESCRIPTION:
{jd_text}

CURRENT CV:
{cv_text}

CRITICAL MISSING KEYWORDS (weave in naturally — do NOT fabricate experience):
{missing_keywords}

Rules:
1. Never invent experience, qualifications, or achievements
2. Integrate missing keywords only where they authentically fit
3. Every bullet: [Action Verb] + [What you did] + [Measurable result]
4. Professional summary: 3–4 sentences max, directly addressing this specific role
5. Tone: sharp, human, professional — no robotic AI language
6. Banned phrases: "passionate about", "results-driven", "dynamic professional",
   "synergy", "leverage", "cutting-edge", "detail-oriented", "go-getter"
7. Format as clean Markdown with ## section headers
8. Open with a ## Professional Summary tailored to this role

Return the complete optimized CV as Markdown only — no preamble."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def analyze_jd_match(jd_text: str, cv_text: str) -> dict:
    """Return structured ATS gap analysis. Claude if available, regex fallback."""
    client = _get_claude()

    if client:
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1600,
                system=_ANALYSIS_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": _ANALYSIS_USER.format(
                        jd_text=jd_text[:5000],
                        cv_text=cv_text[:3500],
                    ),
                }],
            )
            raw = resp.content[0].text.strip()
            # strip accidental markdown fences
            raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
            raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE).strip()
            result = json.loads(raw)
            required = {"ats_score", "matched_keywords", "missing_keywords", "ats_issues"}
            if required.issubset(result):
                return result
        except Exception as exc:
            print(f"[JDMatcher] Claude analysis error: {exc} — falling back to regex")

    # Regex fallback
    jd_kws = _extract_regex(jd_text)
    matched, missing = _overlap(jd_kws, cv_text)
    total = max(len(jd_kws), 1)
    match_ratio = len(matched) / total
    # Scoring: base 25 + up to 72 from match ratio.
    # Real ATS systems reward semantic keyword coverage, not exact literal matches.
    # 80 % coverage → ~83,  90 % → ~90,  100 % → 97.
    score = min(97, max(15, int(25 + match_ratio * 72)))

    return {
        "ats_score": score,
        "role_title": "",
        "company_name": "",
        "matched_keywords": matched[:15],
        "missing_keywords": missing[:15],
        "ats_issues": [
            "Several JD keywords are absent from the current CV.",
            "Professional summary may not be aligned to this specific role.",
            "Bullet points would benefit from stronger action verbs and quantified outcomes.",
        ],
        "match_reasons": [
            f"Profile contains {len(matched)} matching terms from the job description.",
        ],
    }


async def generate_ats_cv(jd_text: str, cv_text: str, missing_keywords: List[str]) -> str:
    """Generate a tailored ATS-optimized CV as Markdown. Claude if available, annotated fallback otherwise."""
    client = _get_claude()

    if client:
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2800,
                system=_GENERATION_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": _GENERATION_USER.format(
                        jd_text=jd_text[:5000],
                        cv_text=cv_text[:3500],
                        missing_keywords=", ".join(missing_keywords[:20]),
                    ),
                }],
            )
            return resp.content[0].text.strip()
        except Exception as exc:
            print(f"[JDMatcher] Claude generation error: {exc} — using annotated fallback")

    kw_list = "\n".join(f"- {kw}" for kw in missing_keywords[:15])
    return (
        "# ATS-Optimised CV\n\n"
        "> **Note:** AI rewriting is unavailable (API key not configured). "
        "Your original CV is shown below with a keyword integration guide.\n\n"
        "---\n\n"
        f"{cv_text}\n\n"
        "---\n\n"
        "## Keywords to Integrate\n\n"
        "The following high-priority terms were identified in the job description "
        "but are absent from your current profile. Add them naturally where they "
        "authentically reflect your experience:\n\n"
        f"{kw_list}\n"
    )
