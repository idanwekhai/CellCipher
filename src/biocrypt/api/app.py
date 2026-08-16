"""FastAPI application: JSON API under /api plus the static web interface.

Run with: `uv run main.py`, or directly: `uv run uvicorn biocrypt.api.app:app --reload`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from biocrypt.api.routes import router

app = FastAPI(
    title="biocrypt",
    description=(
        "A text <-> DNA (A/C/G/T) encoding/storage codec. This is an encoding "
        "format, not encryption: DNA produced here is reversible by anyone who "
        "knows the (published) packet format, with no secret key involved."
    ),
    version="0.1.0",
)

# MVP-only: wide open so the static frontend can be served from anywhere
# (a different port, `file://`, etc.) during development. Tighten before any
# real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.middleware("http")
async def no_store_static(request: Request, call_next):
    """Serve the frontend uncached.

    StaticFiles sends ETag/Last-Modified, and browsers cache ES modules hard
    enough that an edited .js keeps running the previous build after a normal
    reload -- the UI then looks broken when the code is actually correct.
    Development convenience only; a deployment would want real cache headers
    with fingerprinted filenames.
    """
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
    return response


@app.get("/api/health", tags=["codec"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Repo layout: <root>/src/biocrypt/api/app.py and <root>/interface/ (frontend).
_INTERFACE_DIR = Path(__file__).resolve().parents[3] / "interface"
if _INTERFACE_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_INTERFACE_DIR, html=True), name="interface")
