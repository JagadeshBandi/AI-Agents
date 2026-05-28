"""
TapApply Compliance Firewall — Platform Interaction Policy.

This module defines and enforces the legal data-interaction boundaries for
all automated platform interactions. It is the single source of truth for
what TapApply is and is not permitted to do when automating job applications.

Legal framework:
  - UK Computer Misuse Act 1990: prohibits unauthorised access to computer systems.
    TapApply only accesses public-facing pages, never authenticated areas it has
    not been explicitly granted access to.
  - GDPR / UK GDPR (2018): candidate PII is processed in-memory only during the
    submission cycle and never persisted beyond the DB row. No behavioural tracking.
  - Platform Terms of Service: automation is restricted to actions a natural person
    could perform using a standard browser (filling visible form fields, clicking
    visible buttons, reading publicly displayed text).
"""

from dataclasses import dataclass, field
from typing import FrozenSet


@dataclass(frozen=True)
class PlatformPolicy:
    """Immutable policy record for a single job platform."""
    name: str
    domain: str

    # What the automation is explicitly permitted to do
    permitted_actions: FrozenSet[str]

    # What is absolutely prohibited
    prohibited_actions: FrozenSet[str]

    # Whether robots.txt is checked before each request (always True here)
    robots_txt_enforced: bool = True

    # Minimum seconds between page requests (on top of robots Crawl-delay)
    min_request_interval_s: float = 2.0

    # PII retention policy
    pii_retention: str = "in-process only — wiped after submission loop"


# ---------------------------------------------------------------------------
# Platform-specific policies
# ---------------------------------------------------------------------------

REED = PlatformPolicy(
    name="Reed.co.uk",
    domain="www.reed.co.uk",
    permitted_actions=frozenset({
        "navigate_public_job_listing_page",
        "read_publicly_displayed_job_title",
        "read_publicly_displayed_company_name",
        "read_publicly_displayed_location",
        "read_publicly_displayed_salary_range",
        "read_publicly_displayed_job_description",
        "click_standard_visible_apply_button",
        "fill_standard_application_form_fields",
        "upload_user_provided_cv_file",
    }),
    prohibited_actions=frozenset({
        "scrape_private_api_endpoints",
        "scrape_internal_graphql",
        "harvest_recruiter_contact_data",
        "harvest_candidate_data",
        "mass_download_job_listings_beyond_result_limit",
        "bypass_rate_limits",
        "store_session_credentials_on_disk",
        "cache_pii_beyond_submission_cycle",
        "create_fake_candidate_accounts",
        "submit_applications_to_disallowed_paths",
    }),
    min_request_interval_s=3.0,
)

TOTALJOBS = PlatformPolicy(
    name="TotalJobs",
    domain="www.totaljobs.com",
    permitted_actions=frozenset({
        "navigate_public_job_listing_page",
        "read_publicly_displayed_job_title",
        "read_publicly_displayed_company_name",
        "read_publicly_displayed_location",
        "read_publicly_displayed_salary_range",
        "read_publicly_displayed_job_description",
        "click_standard_visible_apply_button",
        "fill_standard_application_form_fields",
        "upload_user_provided_cv_file",
    }),
    prohibited_actions=frozenset({
        "scrape_private_api_endpoints",
        "harvest_recruiter_pii",
        "mass_download_listings",
        "bypass_rate_limits",
        "store_session_credentials_on_disk",
        "cache_pii_beyond_submission_cycle",
    }),
    min_request_interval_s=3.0,
)

INDEED = PlatformPolicy(
    name="Indeed",
    domain="www.indeed.com",
    permitted_actions=frozenset({
        "navigate_public_job_listing_page",
        "read_publicly_displayed_job_metadata",
        "click_standard_visible_apply_button",
        "fill_standard_application_form_fields",
    }),
    prohibited_actions=frozenset({
        "access_employer_dashboard",
        "harvest_resume_database",
        "scrape_internal_api",
        "bypass_captcha",
        "store_session_credentials_on_disk",
        "mass_application_without_candidate_consent",
    }),
    min_request_interval_s=4.0,
)

LINKEDIN = PlatformPolicy(
    name="LinkedIn",
    domain="www.linkedin.com",
    permitted_actions=frozenset({
        "read_publicly_displayed_job_posting",
        "navigate_to_job_application_page",
        # LinkedIn Easy Apply requires user authentication — automation
        # only proceeds when the user provides their own session credentials
        # and explicitly authorises each application.
        "fill_easy_apply_form_with_user_consent",
    }),
    prohibited_actions=frozenset({
        "scrape_member_profiles_without_consent",
        "harvest_connection_data",
        "access_recruiter_inmail",
        "bypass_authentication",
        "use_linkedin_api_without_official_authorisation",
        "mass_connection_requests",
        "store_user_credentials_on_disk",
        "cache_pii_beyond_submission_cycle",
    }),
    # LinkedIn's robots.txt is highly restrictive — we respect it fully.
    min_request_interval_s=5.0,
)

ALL_POLICIES: dict[str, PlatformPolicy] = {
    "reed": REED,
    "totaljobs": TOTALJOBS,
    "indeed": INDEED,
    "linkedin": LINKEDIN,
}


# ---------------------------------------------------------------------------
# PII transience guarantees
# ---------------------------------------------------------------------------

PII_POLICY = {
    "cv_file": "Stored to OS temp directory only; deleted immediately after text extraction via transience.release_file().",
    "candidate_email": "Held in-process memory during form submission only; never written to disk or logs.",
    "candidate_phone": "Same as email — in-process only.",
    "cover_letter": "Stored in DB (user-owned data); never transmitted to third parties.",
    "session_cookies": "Held in Playwright browser context only; context is destroyed after each submission cycle.",
    "form_answers": "Stored in DB JobApplication.answers (user-owned); never shared externally.",
}


# ---------------------------------------------------------------------------
# Runtime check helper
# ---------------------------------------------------------------------------

def action_is_permitted(platform_key: str, action: str) -> bool:
    """
    Returns True if the given action is permitted for the platform.
    Call this before executing any automation step.
    """
    policy = ALL_POLICIES.get(platform_key.lower())
    if policy is None:
        return False
    if action in policy.prohibited_actions:
        return False
    return action in policy.permitted_actions


def assert_permitted(platform_key: str, action: str) -> None:
    """Raises RuntimeError if the action is not permitted."""
    if not action_is_permitted(platform_key, action):
        raise RuntimeError(
            f"[ComplianceFirewall] Action '{action}' is NOT permitted on {platform_key}. "
            f"Refusing to proceed."
        )
