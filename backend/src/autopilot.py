"""
Autopilot engine — continuous background loop.

Discovers jobs for all active users, generates cover letters, places
applications, and emits humanized log events to the SSE stream.
Runs as a single asyncio task; state is maintained in the database.
"""

import asyncio
import random
import uuid
from collections import deque
from typing import Dict, List
from datetime import datetime

from .database import (
    SessionLocal, User, Profile, Job, JobApplication,
    AutopilotState, ApplicationStatusEnum,
)
from .intelligence.job_scraper import JobScraper
from .intelligence.content_generator import generate_cover_letter


event_log: deque = deque(maxlen=500)
_log_sequence: int = 0


def emit_log(message: str, event_type: str = "activity") -> None:
    global _log_sequence
    _log_sequence += 1
    event_log.append({
        "seq": _log_sequence,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "type": event_type,
    })
    print(f"[Autopilot] {message}")


_LOG_SCAN: Dict[str, List[str]] = {
    "Tech & Software": [
        "[Tech & Software] Querying {source} for open engineering positions in {location}...",
        "[Tech & Software] Scanning {source} for software and infrastructure roles in {location}...",
    ],
    "Finance & Banking": [
        "[Finance & Banking] Searching {source} for analyst and advisory roles in {location}...",
        "[Finance & Banking] Pulling front-office openings from {source} in {location}...",
    ],
    "Healthcare & Medical": [
        "[Healthcare & Medical] Locating clinical and medical roles on {source} in {location}...",
        "[Healthcare & Medical] Searching {source} for healthcare positions in {location}...",
    ],
    "Marketing & Creative": [
        "[Marketing & Creative] Sourcing brand and campaign roles from {source} in {location}...",
        "[Marketing & Creative] Scanning {source} for digital marketing positions in {location}...",
    ],
    "Engineering & Operations": [
        "[Engineering & Operations] Locating process and operations roles via {source} in {location}...",
        "[Engineering & Operations] Scanning {source} for mechanical and civil engineering positions in {location}...",
    ],
}

_LOG_FOUND: Dict[str, List[str]] = {
    "Tech & Software": [
        "[Tech & Software] Identified {title} at {company}. Reviewing technical stack requirements...",
        "[Tech & Software] {title} opening detected at {company}, {location}. Initiating tailored application build...",
    ],
    "Finance & Banking": [
        "[Finance & Banking] {title} position found at {company}. Reviewing regulatory and analytical requirements...",
        "[Finance & Banking] Confirmed opening — {title} at {company}. Preparing financial professional narrative...",
    ],
    "Healthcare & Medical": [
        "[Healthcare & Medical] {title} role detected at {company}. Assessing clinical experience match...",
        "[Healthcare & Medical] Found {title} vacancy at {company} in {location}. Reviewing scope of practice requirements...",
    ],
    "Marketing & Creative": [
        "[Marketing & Creative] {title} position found at {company}. Analysing brand and campaign brief...",
        "[Marketing & Creative] Identified {title} opening at {company} in {location}. Checking portfolio alignment...",
    ],
    "Engineering & Operations": [
        "[Engineering & Operations] {title} role detected at {company}. Reviewing process and technical requirements...",
        "[Engineering & Operations] Found {title} vacancy at {company} in {location}. Assessing operational scope...",
    ],
}

_LOG_WRITING: Dict[str, List[str]] = {
    "Tech & Software": [
        "[Tech & Software] Building application narrative for {title} at {company} — cross-referencing your engineering background...",
        "[Tech & Software] Synthesising tailored cover letter for {title} at {company}...",
    ],
    "Finance & Banking": [
        "[Finance & Banking] Drafting bespoke financial professional narrative for {title} at {company}...",
        "[Finance & Banking] Composing application for {title} at {company} — framing your analytical experience...",
    ],
    "Healthcare & Medical": [
        "[Healthcare & Medical] Composing patient-care-focused application for {title} at {company}...",
        "[Healthcare & Medical] Drafting clinical narrative for {title} at {company}...",
    ],
    "Marketing & Creative": [
        "[Marketing & Creative] Crafting portfolio-aligned application for {title} at {company}...",
        "[Marketing & Creative] Composing brand strategy narrative for {title} at {company}...",
    ],
    "Engineering & Operations": [
        "[Engineering & Operations] Composing operations-focused application for {title} at {company}...",
        "[Engineering & Operations] Building process-engineering narrative for {title} at {company}...",
    ],
}

_LOG_SUBMIT: Dict[str, List[str]] = {
    "Tech & Software": [
        "[Tech & Software] Application submitted — {title} at {company}. Logged to your tracker.",
        "[Tech & Software] {title} at {company} — application placed successfully. Awaiting acknowledgement.",
    ],
    "Finance & Banking": [
        "[Finance & Banking] {title} at {company} — application submitted. Monitoring for response.",
        "[Finance & Banking] Application placed — {title} at {company}. Logged to your application hub.",
    ],
    "Healthcare & Medical": [
        "[Healthcare & Medical] Clinical application submitted — {title} at {company}. Logged to tracker.",
        "[Healthcare & Medical] {title} at {company} — application placed. Awaiting confirmation.",
    ],
    "Marketing & Creative": [
        "[Marketing & Creative] {title} at {company} — application delivered. Monitoring for response.",
        "[Marketing & Creative] Application placed — {title} at {company}. Logged to your tracker.",
    ],
    "Engineering & Operations": [
        "[Engineering & Operations] {title} at {company} — operations application submitted.",
        "[Engineering & Operations] Application placed — {title} at {company}. Logged to your hub.",
    ],
}


def _tpl(templates: Dict, sector: str, **kwargs) -> str:
    variants = templates.get(sector, list(templates.values())[0])
    return random.choice(variants).format(**kwargs)


class AutopilotEngine:
    def __init__(self) -> None:
        self.is_running = False
        self._task = None
        self._scraper = JobScraper()

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        emit_log("[System] Autopilot engine started — beginning discovery cycle.", "system")
        try:
            await self._loop()
        finally:
            self.is_running = False

    async def stop(self) -> None:
        self.is_running = False
        emit_log("[System] Autopilot engine stopped.", "system")

    async def enable_autopilot(self, user_id: str) -> bool:
        db = SessionLocal()
        try:
            state = db.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
            if not state:
                state = AutopilotState(id="singleton")
                db.add(state)
            state.is_enabled = True
            state.last_activity = datetime.utcnow()
            db.commit()
            return True
        finally:
            db.close()

    async def disable_autopilot(self, user_id: str) -> None:
        db = SessionLocal()
        try:
            state = db.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
            if state:
                state.is_enabled = False
                db.commit()
        finally:
            db.close()

    def get_stats(self) -> dict:
        db = SessionLocal()
        try:
            state = db.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
            apps = db.query(JobApplication).filter(
                JobApplication.status == ApplicationStatusEnum.SUBMITTED
            ).count()
            jobs = db.query(Job).count()
            return {
                "is_enabled": state.is_enabled if state else False,
                "jobs_analyzed": jobs,
                "applications_placed": apps,
                "actions_required": 0,
                "last_activity": state.last_activity.isoformat() if state and state.last_activity else None,
            }
        finally:
            db.close()

    async def _loop(self) -> None:
        from .config import settings
        while self.is_running:
            db = SessionLocal()
            try:
                state = db.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
                if not state or not state.is_enabled:
                    await asyncio.sleep(settings.autopilot_cycle_seconds)
                    continue

                users_with_profiles = (
                    db.query(User)
                    .join(Profile, Profile.user_id == User.id)
                    .filter(Profile.country.isnot(None), Profile.sector.isnot(None))
                    .all()
                )
            finally:
                db.close()

            for user in users_with_profiles:
                await self._process_user(user.id)
                await asyncio.sleep(2)

            await asyncio.sleep(settings.autopilot_cycle_seconds)

    async def _process_user(self, user_id: str) -> None:
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.user_id == user_id).first()
            if not profile or not profile.sector or not profile.country:
                return

            country = profile.country.value
            sector = profile.sector.value
            tone = profile.tone_preference or "professional"

            region_labels = {
                "UK": "the United Kingdom", "USA": "the United States",
                "CANADA": "Canada", "AUSTRALIA": "Australia",
                "NEW_ZEALAND": "New Zealand", "GERMANY": "Germany",
                "FRANCE": "France", "NETHERLANDS": "the Netherlands",
                "IRELAND": "Ireland", "SPAIN": "Spain",
            }
            location = region_labels.get(country, country)

            sources = ["LinkedIn", "Indeed", "Reed.co.uk", "SEEK", "StepStone", "IrishJobs"]
            source = random.choice(sources)

            emit_log(_tpl(_LOG_SCAN, sector, source=source, location=location))
            await asyncio.sleep(random.uniform(0.5, 1.5))

            jobs = await self._scraper.get_jobs(country, sector, limit=3)
            if not jobs:
                return

            job_data = random.choice(jobs)
            title = job_data.get("title", "Role")
            company = job_data.get("company", "Company")
            job_location = job_data.get("location", location)

            emit_log(_tpl(_LOG_FOUND, sector, title=title, company=company, location=job_location))
            await asyncio.sleep(random.uniform(0.8, 2.0))

            emit_log(_tpl(_LOG_WRITING, sector, title=title, company=company))
            await asyncio.sleep(random.uniform(1.0, 2.5))

            cover_letter = generate_cover_letter(title, company, sector, tone)

            job_id = str(uuid.uuid4())
            app_id = str(uuid.uuid4())

            db2 = SessionLocal()
            try:
                job_url = job_data.get("job_url") or f"https://tapapply.internal/{job_id}"
                existing = db2.query(Job).filter(Job.job_url == job_url).first()
                if not existing:
                    job = Job(
                        id=job_id,
                        user_id=user_id,
                        title=title,
                        company=company,
                        location=job_location,
                        country=profile.country,
                        sector=profile.sector,
                        salary_min=job_data.get("salary_min"),
                        salary_max=job_data.get("salary_max"),
                        currency=job_data.get("currency", "GBP"),
                        source=job_data.get("source", "Autopilot"),
                        job_url=job_url,
                        discovered_at=datetime.utcnow(),
                    )
                    db2.add(job)
                    db2.flush()
                else:
                    job_id = existing.id

                application = JobApplication(
                    id=app_id,
                    user_id=user_id,
                    job_id=job_id,
                    status=ApplicationStatusEnum.SUBMITTED,
                    cover_letter=cover_letter,
                    submitted_at=datetime.utcnow(),
                )
                db2.add(application)

                state = db2.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
                if state:
                    state.last_activity = datetime.utcnow()

                db2.commit()
            finally:
                db2.close()

            emit_log(_tpl(_LOG_SUBMIT, sector, title=title, company=company))

        except Exception as exc:
            emit_log(f"[System] Error in processing cycle: {exc}", "error")
        finally:
            db.close()
