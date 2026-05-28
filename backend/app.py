"""
TapApply FastAPI backend.
REST API + SSE log stream + WebSocket support agent.
"""

import asyncio
import json
import os
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import (
    FastAPI, HTTPException, UploadFile, File,
    BackgroundTasks, WebSocket, WebSocketDisconnect, Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.config import settings
from src.database import (
    init_db, SessionLocal, User, Profile, ManualProfile, Job,
    JobApplication, InterviewSession, AutopilotState,
    CountryEnum, SectorEnum, ApplicationStatusEnum,
)
from src.autopilot import AutopilotEngine, event_log
from src.resume_parser import ResumeExtractor
from src.intelligence.ats_builder import build_ats_cv
from src.intelligence.content_generator import generate_cover_letter
from src.intelligence.interview_prep import generate_interview_prep
from src.compliance.transience import reap_expired_files, make_temp_file, release_file
from src.support.ws_hub import ws_hub
from src.support.agent import support_agent, DISCLAIMER
from src.intelligence.jd_matcher import analyze_jd_match, generate_ats_cv as _generate_ats_cv

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

init_db()

app = FastAPI(title="TapApply API", version="2.0.0")

# ---------------------------------------------------------------------------
# CORS — wildcard origin without credentials (credentials require specific origin)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers — always return JSON, never raw HTML
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    print(f"[Unhandled] {request.method} {request.url} → {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Application singletons
# ---------------------------------------------------------------------------

autopilot_engine = AutopilotEngine()
resume_extractor = ResumeExtractor()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class Step1Request(BaseModel):
    country: CountryEnum
    user_id: Optional[str] = None


class Step2Request(BaseModel):
    user_id: str
    sector: SectorEnum


class ManualProfileRequest(BaseModel):
    user_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    professional_summary: Optional[str] = None
    experience_entries: Optional[list] = None
    education_entries: Optional[list] = None
    skills_technical: Optional[list] = None
    skills_soft: Optional[list] = None
    certifications: Optional[list] = None
    target_role: Optional[str] = None
    target_level: str = "mid"
    tone_preference: str = "professional"


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatusEnum


class MatchRequest(BaseModel):
    user_id: str
    jd_text: str


class GenerateATSRequest(BaseModel):
    user_id: str
    jd_text: str
    missing_keywords: Optional[list] = None


# ---------------------------------------------------------------------------
# Onboarding — Step 1: country
# ---------------------------------------------------------------------------

@app.post("/api/onboarding/step1")
async def onboarding_step1(request: Step1Request):
    db = SessionLocal()
    try:
        user_id = request.user_id or str(uuid.uuid4())
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=f"user_{user_id[:8]}@tapapply.local",
                name="TapApply User",
            )
            db.add(user)
            db.commit()

        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(id=str(uuid.uuid4()), user_id=user_id, country=request.country)
            db.add(profile)
        else:
            profile.country = request.country
        db.commit()

        return {"success": True, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Onboarding — Step 2: sector
# ---------------------------------------------------------------------------

@app.post("/api/onboarding/step2")
async def onboarding_step2(request: Step2Request):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == request.user_id).first()
        if not profile:
            raise HTTPException(404, "Profile not found")
        profile.sector = request.sector
        db.commit()
        return {"success": True, "user_id": request.user_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Onboarding — Step 3A: CV upload (Path A)
# ---------------------------------------------------------------------------

@app.post("/api/onboarding/step3/upload")
async def onboarding_upload_cv(
    user_id: str,
    file: UploadFile = File(...),
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    tone_preference: str = "professional",
):
    db = SessionLocal()
    tmp_path = None
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            raise HTTPException(404, "Profile not found")

        filename = file.filename or "upload.txt"
        ext = Path(filename).suffix.lower()
        if ext not in settings.allowed_resume_formats:
            raise HTTPException(400, f"Unsupported format '{ext}'. Use PDF, DOCX, DOC, or TXT.")

        tmp_path = make_temp_file(ext)
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        try:
            cv_text, metadata = resume_extractor.extract_from_file(tmp_path)
        except RuntimeError as exc:
            raise HTTPException(400, str(exc))

        profile.cv_text = cv_text
        profile.cv_original_filename = filename
        profile.linkedin_url = linkedin_url or profile.linkedin_url
        profile.github_url = github_url or profile.github_url
        profile.tone_preference = tone_preference
        profile.onboarding_path = "cv"
        db.commit()

        return {"success": True, "user_id": user_id, "resume_metadata": metadata}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        if tmp_path:
            release_file(tmp_path)
        db.close()


# ---------------------------------------------------------------------------
# Onboarding — Step 3B: Manual profile (Path B)
# ---------------------------------------------------------------------------

@app.post("/api/onboarding/step3/manual")
async def onboarding_manual_profile(request: ManualProfileRequest):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == request.user_id).first()
        if not profile:
            raise HTTPException(404, "Profile not found — complete Step 1 first.")

        # Extract fields that belong on Profile, not ManualProfile
        tone_preference = request.tone_preference

        # Build data dict for ManualProfile columns only
        data = request.model_dump(exclude={"user_id", "tone_preference"})

        country = profile.country.value if profile.country else "UK"
        sector = profile.sector.value if profile.sector else "Tech & Software"

        generated_cv = build_ats_cv(data, country, sector)
        data["generated_cv_text"] = generated_cv

        existing_mp = db.query(ManualProfile).filter(
            ManualProfile.user_id == request.user_id
        ).first()

        if existing_mp:
            for k, v in data.items():
                if hasattr(ManualProfile, k):
                    setattr(existing_mp, k, v)
            existing_mp.updated_at = datetime.utcnow()
        else:
            # Only pass keys that are actual ManualProfile columns
            mp_columns = {c.key for c in ManualProfile.__table__.columns}
            safe_data = {k: v for k, v in data.items() if k in mp_columns}
            mp = ManualProfile(id=str(uuid.uuid4()), user_id=request.user_id, **safe_data)
            db.add(mp)

        # Update Profile with generated CV and tone
        profile.cv_text = generated_cv
        profile.tone_preference = tone_preference
        profile.onboarding_path = "manual"
        db.commit()

        return {
            "success": True,
            "user_id": request.user_id,
            "generated_cv_preview": generated_cv[:400] + "..." if len(generated_cv) > 400 else generated_cv,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            raise HTTPException(404, "Profile not found")
        return {
            "id": profile.id,
            "user_id": user_id,
            "country": profile.country.value if profile.country else None,
            "sector": profile.sector.value if profile.sector else None,
            "cv_filename": profile.cv_original_filename,
            "tone_preference": profile.tone_preference or "professional",
            "onboarding_path": profile.onboarding_path or "cv",
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

@app.get("/api/jobs/{user_id}")
async def get_jobs(user_id: str):
    db = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .filter(Job.user_id == user_id)
            .order_by(Job.discovered_at.desc())
            .limit(50)
            .all()
        )
        return {
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "location": j.location,
                    "salary_range": (
                        f"{int(j.salary_min):,}–{int(j.salary_max):,} {j.currency}"
                        if j.salary_min and j.salary_max
                        else "Competitive"
                    ),
                    "source": j.source,
                    "discovered_at": j.discovered_at.isoformat(),
                }
                for j in jobs
            ]
        }
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

@app.get("/api/applications/{user_id}")
async def get_applications(user_id: str):
    db = SessionLocal()
    try:
        apps = (
            db.query(JobApplication)
            .filter(JobApplication.user_id == user_id)
            .order_by(JobApplication.submitted_at.desc())
            .limit(100)
            .all()
        )
        result = []
        for application in apps:
            job = db.query(Job).filter(Job.id == application.job_id).first()
            result.append({
                "id": application.id,
                "job_title": job.title if job else "Unknown Role",
                "company": job.company if job else "Unknown Company",
                "location": job.location if job else "",
                "status": application.status.value,
                "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
                "has_interview_prep": bool(
                    db.query(InterviewSession)
                    .filter(InterviewSession.application_id == application.id)
                    .first()
                ),
            })
        return {"applications": result}
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@app.patch("/api/applications/{application_id}/status")
async def update_application_status(application_id: str, body: ApplicationStatusUpdate):
    db = SessionLocal()
    try:
        application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not application:
            raise HTTPException(404, "Application not found")
        application.status = body.status
        application.updated_at = datetime.utcnow()
        db.commit()
        return {"success": True, "status": body.status.value}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Interview Prep
# ---------------------------------------------------------------------------

@app.get("/api/interview/{application_id}")
async def get_interview_prep(application_id: str):
    db = SessionLocal()
    try:
        existing = db.query(InterviewSession).filter(
            InterviewSession.application_id == application_id
        ).first()
        if existing:
            return {
                "application_id": application_id,
                "company_brief": existing.company_brief,
                "key_challenges": existing.key_challenges,
                "culture_signals": existing.culture_signals,
                "mock_questions": existing.mock_questions,
                "generated_at": existing.generated_at.isoformat(),
            }

        application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not application:
            raise HTTPException(404, "Application not found")

        job = db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")

        prep = generate_interview_prep(
            job_title=job.title,
            company=job.company,
            sector=job.sector.value if job.sector else "Tech & Software",
            job_description=job.job_description,
            num_questions=8,
        )

        session = InterviewSession(
            id=str(uuid.uuid4()),
            application_id=application_id,
            user_id=application.user_id,
            company_brief=prep["company_brief"],
            key_challenges=prep["key_challenges"],
            culture_signals=prep["culture_signals"],
            mock_questions=prep["mock_questions"],
        )
        db.add(session)
        db.commit()

        return {
            "application_id": application_id,
            "job_title": job.title,
            "company": job.company,
            **prep,
            "generated_at": session.generated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Autopilot control
# ---------------------------------------------------------------------------

@app.post("/api/autopilot/enable")
async def enable_autopilot(user_id: str, background_tasks: BackgroundTasks):
    try:
        await autopilot_engine.enable_autopilot(user_id)
        if not autopilot_engine.is_running:
            background_tasks.add_task(autopilot_engine.start)
        return {"success": True, "message": "Autopilot enabled"}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.post("/api/autopilot/disable")
async def disable_autopilot(user_id: str):
    try:
        await autopilot_engine.disable_autopilot(user_id)
        return {"success": True, "message": "Autopilot disabled"}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/api/autopilot/status")
async def autopilot_status():
    try:
        return autopilot_engine.get_stats()
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ---------------------------------------------------------------------------
# SSE log stream
# ---------------------------------------------------------------------------

async def _sse_generator(user_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    cursor = len(event_log)
    while True:
        try:
            current = list(event_log)
            for entry in current[cursor:]:
                # Emit entry as-is — type is already set correctly by emit_log()
                yield f"data: {json.dumps(entry)}\n\n"
            cursor = len(current)

            stats = autopilot_engine.get_stats()
            yield f"data: {json.dumps({'type': 'stats', 'timestamp': datetime.utcnow().isoformat(), **stats})}\n\n"

            await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[SSE] Error: {exc}")
            await asyncio.sleep(2)


@app.get("/api/logs/stream")
async def stream_logs(user_id: Optional[str] = None):
    return StreamingResponse(
        _sse_generator(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# WebSocket — floating support agent
# ---------------------------------------------------------------------------

@app.websocket("/ws/support/{client_id}")
async def ws_support(websocket: WebSocket, client_id: str):
    await ws_hub.connect(websocket, client_id)
    await ws_hub.send_to(client_id, {"type": "system", "message": DISCLAIMER})
    try:
        while True:
            data = await websocket.receive_json()
            await support_agent.handle(client_id, data, ws_hub)
    except WebSocketDisconnect:
        ws_hub.disconnect(client_id)
    except Exception as exc:
        print(f"[WS] Client {client_id} error: {exc}")
        ws_hub.disconnect(client_id)


# ---------------------------------------------------------------------------
# JD Match Analysis
# ---------------------------------------------------------------------------

@app.post("/api/analyze-match")
async def analyze_match(request: MatchRequest):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == request.user_id).first()
        cv_text = ""
        if profile and profile.cv_text:
            cv_text = profile.cv_text
        else:
            # Build a minimal text from manual profile if CV text not stored
            mp = db.query(ManualProfile).filter(ManualProfile.user_id == request.user_id).first()
            if mp:
                parts = []
                if mp.full_name:
                    parts.append(mp.full_name)
                if mp.professional_summary:
                    parts.append(mp.professional_summary)
                if mp.skills_technical:
                    parts.append(" ".join(mp.skills_technical or []))
                if mp.skills_soft:
                    parts.append(" ".join(mp.skills_soft or []))
                cv_text = "\n".join(parts)

        if not cv_text.strip():
            raise HTTPException(400, "No CV or profile found for this user. Complete onboarding first.")

        result = await analyze_jd_match(request.jd_text, cv_text)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


@app.post("/api/generate-ats-cv")
async def generate_ats_cv_endpoint(request: GenerateATSRequest):
    db = SessionLocal()
    try:
        profile = db.query(Profile).filter(Profile.user_id == request.user_id).first()
        cv_text = ""
        if profile and profile.cv_text:
            cv_text = profile.cv_text
        else:
            mp = db.query(ManualProfile).filter(ManualProfile.user_id == request.user_id).first()
            if mp:
                parts = []
                if mp.full_name:
                    parts.append(mp.full_name)
                if mp.professional_summary:
                    parts.append(mp.professional_summary)
                if mp.skills_technical:
                    parts.append(" ".join(mp.skills_technical or []))
                cv_text = "\n".join(parts)

        if not cv_text.strip():
            raise HTTPException(400, "No CV or profile found for this user. Complete onboarding first.")

        missing = request.missing_keywords or []
        cv_markdown = await _generate_ats_cv(request.jd_text, cv_text, missing)
        return {"cv_markdown": cv_markdown}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "autopilot_running": autopilot_engine.is_running,
        "ws_connections": ws_hub.active_count,
    }


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    print("[Startup] TapApply v2 initialising...")
    asyncio.create_task(reap_expired_files())

    db = SessionLocal()
    try:
        state = db.query(AutopilotState).filter(AutopilotState.id == "singleton").first()
        if state and state.is_enabled:
            asyncio.create_task(autopilot_engine.start())
            print("[Startup] Autopilot resumed from last session state.")
    except Exception as exc:
        print(f"[Startup] Warning: could not read autopilot state: {exc}")
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown():
    if autopilot_engine.is_running:
        await autopilot_engine.stop()
