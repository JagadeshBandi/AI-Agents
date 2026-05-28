"""
Zero-storage transience layer.

All uploaded CV files and intermediate artefacts are written to a temporary
location and scheduled for deletion the moment the submission loop closes or
the TTL expires. Nothing user-identifiable persists on disk beyond the DB row.
"""

import os
import asyncio
import tempfile
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional


_registry: Dict[str, dict] = {}
_lock = threading.Lock()


def register_temp_file(path: str, ttl_seconds: int = 300) -> None:
    """Track a temporary file for scheduled deletion."""
    with _lock:
        _registry[path] = {
            "path": path,
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        }


def release_file(path: str) -> None:
    """Immediately delete a file and remove it from the registry."""
    with _lock:
        _registry.pop(path, None)
    _safe_delete(path)


def _safe_delete(path: str) -> None:
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass


async def reap_expired_files() -> None:
    """
    Background coroutine — runs every 60 seconds and deletes any registered
    files whose TTL has elapsed. Called once from app startup.
    """
    while True:
        now = datetime.utcnow()
        expired = []
        with _lock:
            for path, meta in list(_registry.items()):
                if now >= meta["expires_at"]:
                    expired.append(path)
            for path in expired:
                del _registry[path]

        for path in expired:
            _safe_delete(path)

        await asyncio.sleep(60)


def make_temp_file(suffix: str, ttl_seconds: int = 300) -> str:
    """
    Create a named temporary file and register it for automatic deletion.
    Returns the file path; the caller is responsible for writing and closing it.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    register_temp_file(tmp.name, ttl_seconds)
    return tmp.name
