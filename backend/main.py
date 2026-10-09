import os
import uuid
import asyncio
import warnings
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import live
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import all pipeline modules
from rag    import normalize_query, get_context
from llm    import generate_script
from tts    import generate_voice
from avatar import generate_avatar_video
from cache  import get_cached_video, cache_video, get_cache_stats

warnings.filterwarnings("ignore")
logging.getLogger("uvicorn").setLevel(logging.INFO)

load_dotenv()

# ─────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Teacher API",
    description="Priya ma'am — AI Science Teacher for Class 10",
    version="1.0.0"
)

app.include_router(live.router)

# CORS — allow React frontend on any port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Videos folder — create if not exists
VIDEOS_DIR = Path(__file__).parent / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

# Serve videos as static files
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

# In-memory job tracker for async progress updates
# { job_id: { status, step, video_url, script, error } }
jobs: dict = {}


# ─────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────
class TeachRequest(BaseModel):
    topic:      str
    student_id: str = "anonymous"


class ExplainAgainRequest(BaseModel):
    topic:   str
    attempt: int = 2


class TeachResponse(BaseModel):
    video_url: str
    script:    str = ""
    source:    str  # "cache" or "generated"
    job_id:    str = ""


# ─────────────────────────────────────────────────────────────
# Helper — full generation pipeline
# ─────────────────────────────────────────────────────────────
def run_full_pipeline(
    topic:   str,
    attempt: int = 1,
    job_id:  str = ""
) -> dict:
    """
    Runs the complete pipeline:
    normalize → RAG → LLM → TTS → Avatar → save video

    Updates job status at each step if job_id provided.
    Returns dict with video_url and script.
    """

    def update_job(step: str):
        if job_id and job_id in jobs:
            jobs[job_id]["step"] = step
            print(f"  [{job_id[:8]}] {step}")

    # Step 1: Normalize messy student input
    update_job("NCERT books search ho rahi hain...")
    clean_topic = normalize_query(topic)
    print(f"  Normalized: '{topic}' → '{clean_topic}'")

    # Step 2: Get NCERT context from Pinecone
    update_job("Relevant content mil raha hai...")
    context = get_context(clean_topic)

    # Step 3: Generate teacher script via Groq
    update_job("Priya ma'am explanation prepare kar rahi hain...")
    script = generate_script(clean_topic, context, attempt=attempt)
    print(f"  Script: {script['word_count']} words | {script['emotions']}")

    # Step 4: Convert script to voice via Sarvam AI
    update_job("Awaaz record ho rahi hai...")
    audio = generate_voice(script["clean_text"])

    # Step 5: Generate avatar video via D-ID (BYPASSED due to credit limits)
    update_job("Voice upload ho rahi hai...")
    from avatar import upload_audio_to_cloudinary
    # We just upload the audio to Cloudinary and use that URL as the video URL
    video_url = upload_audio_to_cloudinary(audio)

    print(f"  [OK] Audio hosted at Cloudinary: {video_url}")

    return {
        "video_url":   video_url,
        "script":      script["full_script"],
        "clean_topic": clean_topic
    }


# ─────────────────────────────────────────────────────────────
# Background task for async /teach endpoint
# ─────────────────────────────────────────────────────────────
async def generate_in_background(job_id: str, topic: str):
    """Runs pipeline in background and updates job status."""
    try:
        jobs[job_id]["status"] = "processing"

        # Run blocking pipeline in thread pool
        loop   = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: run_full_pipeline(topic, attempt=1, job_id=job_id)
        )

        # Cache the result
        cache_video(result["clean_topic"], result["video_url"])

        jobs[job_id]["status"]    = "done"
        jobs[job_id]["video_url"] = result["video_url"]
        jobs[job_id]["script"]    = result["script"]
        jobs[job_id]["step"]      = "Video taiyaar hai!"

    except Exception as e:
        print(f"  ✗ Pipeline error for job {job_id}: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"]  = str(e)
        jobs[job_id]["step"]   = "Kuch problem aa gayi. Dobara try karein."


# ─────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check — confirms server is running."""
    return {"status": "ok", "message": "Priya ma'am ready hai!"}


@app.post("/teach")
async def teach(
    request: TeachRequest,
    background_tasks: BackgroundTasks
):
    """
    Main teaching endpoint.

    Flow:
    1. Check Redis cache — if hit, return instantly
    2. If miss — start background generation, return job_id
    3. Frontend polls /status/{job_id} for progress
    """
    topic      = request.topic.strip()
    student_id = request.student_id

    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    print(f"\n[/teach] Student: {student_id} | Topic: '{topic}'")

    # ── Step 1: Check cache first ────────────────────────────
    try:
        clean_topic  = normalize_query(topic)
        cached_video = get_cached_video(clean_topic)
    except Exception:
        clean_topic  = topic
        cached_video = None

    if cached_video:
        print(f"  [OK] Cache hit — returning instantly")
        return JSONResponse({
            "video_url": cached_video,
            "script":    "",
            "source":    "cache",
            "job_id":    ""
        })

    # ── Step 2: Cache miss — start background job ────────────
    job_id = uuid.uuid4().hex
    jobs[job_id] = {
        "status":    "queued",
        "step":      "Request mil gayi, shuru ho raha hai...",
        "video_url": None,
        "script":    None,
        "error":     None
    }

    background_tasks.add_task(generate_in_background, job_id, topic)

    print(f"  Started background job: {job_id[:8]}")

    return JSONResponse({
        "video_url": None,
        "script":    "",
        "source":    "generating",
        "job_id":    job_id
    })


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Polls job status for async video generation.
    Frontend calls this every 4 seconds.

    Returns:
        status: queued | processing | done | error
        step:   Current step message in Hinglish
        video_url: URL when done, null otherwise
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    response = {
        "status":    job["status"],
        "step":      job["step"],
        "video_url": job.get("video_url"),
        "script":    job.get("script"),
        "error":     job.get("error")
    }

    # Clean up completed/errored jobs after returning
    if job["status"] in ["done", "error"]:
        # Keep for 5 more polls then delete
        job["_poll_count"] = job.get("_poll_count", 0) + 1
        if job["_poll_count"] > 5:
            del jobs[job_id]

    return JSONResponse(response)


@app.post("/explain-again")
async def explain_again(request: ExplainAgainRequest):
    """
    Re-explains a topic with a completely different analogy.
    This is the 'Samjha Nahi' button endpoint.

    NEVER cached — always generates fresh explanation.
    """
    topic   = request.topic.strip()
    attempt = request.attempt

    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    if attempt < 2:
        attempt = 2  # Always at least attempt 2 for re-explanation

    print(f"\n[/explain-again] Topic: '{topic}' | Attempt: {attempt}")

    try:
        result = run_full_pipeline(topic, attempt=attempt)
        # Do NOT cache re-explanations — they should always be fresh
        return JSONResponse({
            "video_url": result["video_url"],
            "script":    result["script"],
            "source":    "generated",
            "attempt":   attempt
        })

    except Exception as e:
        print(f"  ✗ Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@app.get("/cache-stats")
async def cache_stats():
    """Returns how many videos are cached — useful for monitoring."""
    stats = get_cache_stats()
    return JSONResponse(stats)


@app.delete("/cache/{topic}")
async def clear_cache(topic: str):
    """Clears cached video for a specific topic. Useful for updates."""
    from cache import delete_cached_video
    deleted = delete_cached_video(topic)
    return JSONResponse({
        "deleted": deleted,
        "topic":   topic
    })


# ─────────────────────────────────────────────────────────────
# Run the server
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Starting AI Teacher API Server")
    print("=" * 60)
    print(f"Videos folder : {VIDEOS_DIR}")
    print(f"Docs          : http://localhost:8000/docs")
    print(f"Health check  : http://localhost:8000/health")
    print("=" * 60)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,      # Auto-restart on code changes
        log_level="info"
    )