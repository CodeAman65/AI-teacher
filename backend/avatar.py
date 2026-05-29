# import os
# import time
# import base64
# import warnings
# import logging
# import requests
# from pathlib import Path
# from dotenv import load_dotenv

# # Suppress warnings
# warnings.filterwarnings("ignore")
# logging.getLogger("requests").setLevel(logging.ERROR)
# logging.getLogger("urllib3").setLevel(logging.ERROR)

# # Load environment variables
# load_dotenv()

# # ─────────────────────────────────────────────────────────────
# # D-ID Configuration
# # ─────────────────────────────────────────────────────────────
# DID_API_KEY        = os.getenv("DID_API_KEY")
# DID_BASE_URL       = "https://api.d-id.com"
# POLL_INTERVAL_SEC  = 5       # Check status every 5 seconds
# POLL_TIMEOUT_SEC   = 120     # Give up after 120 seconds

# # ─────────────────────────────────────────────────────────────
# # Teacher image — D-ID needs a publicly accessible URL
# # Replace this with your actual hosted image URL after
# # uploading teacher.jpg to imgbb.com or cloudinary.com (free)
# # ─────────────────────────────────────────────────────────────
# TEACHER_IMAGE_URL = os.getenv(
#     "TEACHER_IMAGE_URL",
#     "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/800px-Gatto_europeo4.jpg"
#     # ↑ placeholder only — replace with your teacher.jpg URL
# )


# def get_did_headers() -> dict:
#     """
#     Builds D-ID authorization headers.
#     D-ID uses Basic auth with base64 encoded API key.
#     """
#     if not DID_API_KEY:
#         raise ValueError(
#             "DID_API_KEY not found in .env file. "
#             "Get your key from studio.d-id.com → API"
#         )

#     # D-ID expects: Basic base64(api_key)
#     encoded_key = base64.b64encode(DID_API_KEY.encode()).decode()

#     return {
#         "Authorization": f"Basic {encoded_key}",
#         "Content-Type": "application/json",
#         "accept": "application/json"
#     }


# def upload_audio_to_did(audio_bytes: bytes) -> str:
#     """
#     Step 1 — Upload audio + teacher image to D-ID to create a talk.

#     D-ID takes:
#       - source_url: publicly accessible teacher image URL
#       - audio: base64 encoded WAV audio

#     Args:
#         audio_bytes: WAV audio bytes from tts.py generate_voice()

#     Returns:
#         talk_id: D-ID job ID to poll for completion

#     Raises:
#         Exception with clear message if upload fails
#     """
#     # Encode audio as base64 for D-ID
#     audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

#     payload = {
#         "source_url": TEACHER_IMAGE_URL,
#         "script": {
#             "type": "audio",
#             "audio_url": audio_url
#         },
#         "config": {
#             "fluent": True,           # Smoother lip movement transitions
#             "pad_audio": 0.0,         # No silence padding
#             "stitch": True            # Blend face naturally into image
#         },
#         "presenter_config": {
#             "crop": {
#                 "type": "rectangle"   # Keep full face visible
#             }
#         }
#     }

#     print(f"  - Uploading to D-ID (image + audio)...")

#     response = requests.post(
#         f"{DID_BASE_URL}/talks",
#         headers=get_did_headers(),
#         json=payload,
#         timeout=30
#     )

#     # Handle errors clearly
#     if response.status_code == 401:
#         raise Exception(
#             "D-ID API key invalid. "
#             "Check DID_API_KEY in your .env file. "
#             "Make sure it's your full API key from studio.d-id.com"
#         )
#     elif response.status_code == 402:
#         raise Exception(
#             "D-ID free credits exhausted. "
#             "You have used all 20 free videos. "
#             "Check studio.d-id.com for your credit balance."
#         )
#     elif response.status_code == 400:
#         raise Exception(
#             f"D-ID bad request: {response.text}\n"
#             "Most likely cause: TEACHER_IMAGE_URL is not publicly accessible. "
#             "Upload teacher.jpg to imgbb.com and update TEACHER_IMAGE_URL in .env"
#         )
#     elif response.status_code not in [200, 201]:
#         raise Exception(
#             f"D-ID API error {response.status_code}: {response.text}"
#         )

#     response_data = response.json()
#     talk_id = response_data.get("id")

#     if not talk_id:
#         raise Exception(
#             f"D-ID did not return a talk ID. Response: {response_data}"
#         )

#     print(f"  ✓ Talk created. ID: {talk_id}")
#     return talk_id


# def poll_video_status(talk_id: str) -> str:
#     """
#     Step 2 — Poll D-ID every 5 seconds until video is ready.

#     D-ID video generation takes 30-90 seconds typically.
#     Statuses: created → started → done (or error)

#     Args:
#         talk_id: ID returned from upload_audio_to_did()

#     Returns:
#         result_url: Direct URL to the generated MP4 video

#     Raises:
#         Exception if video fails or timeout exceeded
#     """
#     url = f"{DID_BASE_URL}/talks/{talk_id}"
#     headers = get_did_headers()

#     elapsed = 0
#     last_status = ""

#     print(f"  - Waiting for D-ID to generate video...")

#     while elapsed < POLL_TIMEOUT_SEC:
#         response = requests.get(url, headers=headers, timeout=15)

#         if response.status_code != 200:
#             raise Exception(
#                 f"D-ID status check failed {response.status_code}: {response.text}"
#             )

#         data = response.json()
#         status = data.get("status", "unknown")

#         # Print status only when it changes
#         if status != last_status:
#             print(f"  - Status: {status} ({elapsed}s elapsed)")
#             last_status = status

#         if status == "done":
#             result_url = data.get("result_url")
#             if not result_url:
#                 raise Exception(
#                     "D-ID returned done but no result_url found. "
#                     f"Full response: {data}"
#                 )
#             print(f"  ✓ Video ready! URL: {result_url}")
#             return result_url

#         elif status == "error":
#             error_details = data.get("error", {})
#             raise Exception(
#                 f"D-ID video generation failed. "
#                 f"Error: {error_details}. "
#                 "Common causes: bad image URL, audio too long, "
#                 "or face not detected in image."
#             )

#         elif status == "rejected":
#             raise Exception(
#                 "D-ID rejected the request. "
#                 "Check that teacher image shows a clear human face."
#             )

#         # Wait before next poll
#         time.sleep(POLL_INTERVAL_SEC)
#         elapsed += POLL_INTERVAL_SEC

#     # Timeout reached
#     raise Exception(
#         f"D-ID video generation timed out after {POLL_TIMEOUT_SEC} seconds. "
#         "The video may still be processing — check studio.d-id.com. "
#         "Try increasing POLL_TIMEOUT_SEC if this happens often."
#     )


# def download_video(video_url: str) -> bytes:
#     """
#     Step 3 — Download the generated MP4 video from D-ID's CDN.

#     Args:
#         video_url: result_url from poll_video_status()

#     Returns:
#         MP4 video as bytes
#     """
#     print(f"  - Downloading video...")

#     response = requests.get(video_url, timeout=60, stream=True)

#     if response.status_code != 200:
#         raise Exception(
#             f"Failed to download video: HTTP {response.status_code}"
#         )

#     video_bytes = response.content
#     size_kb = len(video_bytes) / 1024

#     print(f"  ✓ Video downloaded ({size_kb:.1f} KB)")
#     return video_bytes


# def save_video(video_bytes: bytes, filename: str) -> str:
#     """
#     Saves video bytes to an MP4 file.

#     Args:
#         video_bytes: MP4 bytes from download_video()
#         filename:    Path to save e.g. "test_outputs/lesson.mp4"

#     Returns:
#         Absolute path of saved file
#     """
#     filepath = Path(filename)
#     filepath.parent.mkdir(parents=True, exist_ok=True)

#     with open(filepath, "wb") as f:
#         f.write(video_bytes)

#     abs_path = str(filepath.resolve())
#     print(f"  ✓ Video saved: {abs_path}")
#     return abs_path


# def generate_avatar_video(audio_bytes: bytes) -> bytes:
#     """
#     Main function — Full D-ID pipeline in one call.

#     Takes audio → uploads to D-ID → polls until ready →
#     downloads MP4 → returns video bytes.

#     Args:
#         audio_bytes: WAV audio from tts.py generate_voice()

#     Returns:
#         MP4 video bytes of teacher avatar speaking
#     """
#     print(f"\n  Starting D-ID avatar generation...")
#     start_time = time.time()

#     # Step 1: Upload audio + image to D-ID
#     talk_id = upload_audio_to_did(audio_bytes)

#     # Step 2: Wait for video to be ready
#     result_url = poll_video_status(talk_id)

#     # Step 3: Download the MP4
#     video_bytes = download_video(result_url)

#     elapsed = round(time.time() - start_time, 1)
#     print(f"  ✓ Avatar video ready in {elapsed}s")

#     return video_bytes


# def check_did_credits() -> None:
#     """
#     Utility — Check how many D-ID credits you have remaining.
#     Run this anytime to see your balance.
#     """
#     response = requests.get(
#         f"{DID_BASE_URL}/credits",
#         headers=get_did_headers(),
#         timeout=10
#     )

#     if response.status_code == 200:
#         data = response.json()
#         print(f"\nD-ID Credits:")
#         print(f"  Remaining : {data.get('remaining', 'unknown')}")
#         print(f"  Total     : {data.get('total', 'unknown')}")
#         print(f"  Used      : {data.get('used', 'unknown')}")
#     else:
#         print(f"Could not fetch credits: {response.status_code}")


# if __name__ == "__main__":
#     from rag import get_context
#     from llm import generate_script
#     from tts import generate_voice

#     print("=" * 60)
#     print("Testing Avatar Pipeline")
#     print("=" * 60)

#     # ── Check credits first ──────────────────────────────────
#     print("\n[PRE-CHECK] D-ID Credit Balance")
#     print("-" * 60)
#     check_did_credits()

#     # ── Check image URL is set ───────────────────────────────
#     print(f"\n[PRE-CHECK] Teacher Image URL")
#     print("-" * 60)
#     if "wikimedia" in TEACHER_IMAGE_URL:
#         print("⚠️  WARNING: You are using the placeholder image URL.")
#         print("   This will generate a video but NOT with Priya ma'am's face.")
#         print("   To use your teacher image:")
#         print("   1. Go to imgbb.com (free)")
#         print("   2. Upload your teacher.jpg")
#         print("   3. Copy the direct image URL")
#         print("   4. Add to .env: TEACHER_IMAGE_URL=https://your-url-here.jpg")
#     else:
#         print(f"✓ Using teacher image: {TEACHER_IMAGE_URL}")

#     # ── Test: Full pipeline ──────────────────────────────────
#     print("\n[TEST] Full pipeline — topic to avatar video")
#     print("-" * 60)
#     print("NOTE: This uses 1 D-ID credit. You have 20 free.")
#     print("Proceeding in 3 seconds... (Ctrl+C to cancel)")
#     time.sleep(3)

#     try:
#         topic = "Osmosis"
#         print(f"\nTopic: {topic}")

#         print("Step 1: Getting NCERT context...")
#         context = get_context(topic)
#         print(f"  ✓ {len(context)} chars retrieved")

#         print("Step 2: Generating teacher script...")
#         script = generate_script(topic, context, attempt=1)
#         print(f"  ✓ {script['word_count']} words")
#         print(f"  ✓ Emotions: {script['emotions']}")

#         print("Step 3: Generating voice (Sarvam AI)...")
#         audio = generate_voice(script["clean_text"])
#         print(f"  ✓ Audio: {len(audio)} bytes")

#         # Save audio for reference
#         from tts import save_audio
#         save_audio(audio, "test_outputs/avatar_test_audio.wav")

#         print("Step 4: Generating avatar video (D-ID)...")
#         video = generate_avatar_video(audio)

#         save_video(video, "test_outputs/avatar_test_video.mp4")

#         print("\n" + "=" * 60)
#         print("✓ Avatar pipeline working!")
#         print("  Open test_outputs/avatar_test_video.mp4")
#         print("  You should see a talking teacher avatar")
#         print("  explaining Osmosis in Hinglish")
#         print("=" * 60)

#     except KeyboardInterrupt:
#         print("\nTest cancelled.")
#     except Exception as e:
#         print(f"\n✗ Error: {e}")
#         print("\nCommon fixes:")
#         print("  - 'invalid API key' → check DID_API_KEY in .env")
#         print("  - 'image URL' error → upload teacher.jpg to imgbb.com")
#         print("  - 'credits' error  → check studio.d-id.com balance")

import os
import time
import base64
import tempfile
import warnings
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore")
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
DID_API_KEY       = os.getenv("DID_API_KEY")
DID_BASE_URL      = "https://api.d-id.com"
POLL_INTERVAL_SEC = 5
POLL_TIMEOUT_SEC  = 180     # increased to 3 minutes

TEACHER_IMAGE_URL = os.getenv(
    "TEACHER_IMAGE_URL",
    "https://i.ibb.co/hR8LmCXj/teacher.jpg"
)

CLOUDINARY_CLOUD_NAME  = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY     = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET  = os.getenv("CLOUDINARY_API_SECRET")


def get_did_headers() -> dict:
    """D-ID uses Basic auth with base64 encoded API key."""
    if not DID_API_KEY:
        raise ValueError(
            "DID_API_KEY not found in .env file. "
            "Get your key from studio.d-id.com → API"
        )
    encoded_key = base64.b64encode(DID_API_KEY.encode()).decode()
    return {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }


def upload_audio_to_cloudinary(audio_bytes: bytes) -> str:
    """
    Uploads WAV audio bytes to Cloudinary and returns a public URL.
    Cloudinary free tier: 25GB storage, unlimited uploads.

    Args:
        audio_bytes: WAV audio from tts.py generate_voice()

    Returns:
        Public URL to the audio file D-ID can access
    """
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        raise ValueError(
            "Cloudinary credentials missing in .env.\n"
            "Add: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET\n"
            "Get them free at cloudinary.com"
        )

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )

    # Save bytes to a temp file then upload
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        print("  - Uploading audio to Cloudinary...")
        result = cloudinary.uploader.upload(
            tmp_path,
            resource_type="video",       # Cloudinary uses "video" for audio files
            folder="ai_teacher_audio",
            overwrite=True,
            format="wav"
        )
        audio_url = result["secure_url"]
        print(f"  ✓ Audio hosted at: {audio_url}")
        return audio_url

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


def upload_audio_to_did(audio_bytes: bytes) -> str:
    """
    Step 1 — Upload teacher image + audio URL to D-ID.
    Audio is first hosted on Cloudinary so D-ID can access it.

    Args:
        audio_bytes: WAV audio bytes from tts.py

    Returns:
        talk_id: D-ID job ID to poll for completion
    """
    # First host audio publicly on Cloudinary
    audio_url = upload_audio_to_cloudinary(audio_bytes)

    payload = {
        "source_url": TEACHER_IMAGE_URL,
        "script": {
            "type": "audio",
            "audio_url": audio_url          # ← public URL, not base64
        },
        "config": {
            "fluent": True,
            "pad_audio": 0.0,
            "stitch": True
        }
    }

    print("  - Creating D-ID talk...")

    response = requests.post(
        f"{DID_BASE_URL}/talks",
        headers=get_did_headers(),
        json=payload,
        timeout=30
    )

    # Handle all error cases clearly
    if response.status_code == 401:
        raise Exception(
            "D-ID API key invalid or expired.\n"
            "Fix: Go to studio.d-id.com → API → create new key → update .env"
        )
    elif response.status_code == 402:
        raise Exception(
            "D-ID free credits exhausted (20 videos used).\n"
            "Check your balance at studio.d-id.com"
        )
    elif response.status_code == 400:
        raise Exception(
            f"D-ID bad request: {response.text}\n"
            "Fix: Make sure TEACHER_IMAGE_URL is a direct .jpg link\n"
            "and the image shows a clear front-facing human face."
        )
    elif response.status_code == 500:
        raise Exception(
            f"D-ID server error 500.\n"
            "This is usually caused by:\n"
            "1. Audio URL not accessible by D-ID — check Cloudinary URL is public\n"
            "2. Image URL blocked — try re-uploading teacher.jpg to imgbb.com\n"
            "3. D-ID servers temporarily down — wait 2 minutes and retry\n"
            f"Raw response: {response.text}"
        )
    elif response.status_code not in [200, 201]:
        raise Exception(
            f"D-ID API error {response.status_code}: {response.text}"
        )

    response_data = response.json()
    talk_id = response_data.get("id")

    if not talk_id:
        raise Exception(f"D-ID returned no talk ID. Response: {response_data}")

    print(f"  ✓ Talk created. ID: {talk_id}")
    return talk_id


def poll_video_status(talk_id: str) -> str:
    """
    Step 2 — Poll D-ID every 5 seconds until video is ready.

    Args:
        talk_id: ID from upload_audio_to_did()

    Returns:
        result_url: Direct MP4 video URL
    """
    url = f"{DID_BASE_URL}/talks/{talk_id}"
    headers = get_did_headers()
    elapsed = 0
    last_status = ""

    print("  - Waiting for D-ID to generate video...")

    while elapsed < POLL_TIMEOUT_SEC:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception(
                f"D-ID status check failed {response.status_code}: {response.text}"
            )

        data = response.json()
        status = data.get("status", "unknown")

        if status != last_status:
            print(f"  - Status: {status} ({elapsed}s elapsed)")
            last_status = status

        if status == "done":
            result_url = data.get("result_url")
            if not result_url:
                raise Exception(f"No result_url in response: {data}")
            print(f"  ✓ Video ready!")
            return result_url

        elif status == "error":
            error_details = data.get("error", {})
            raise Exception(
                f"D-ID generation failed: {error_details}\n"
                "Common cause: face not clearly detected in teacher image.\n"
                "Fix: Use a clearer front-facing photo with good lighting."
            )

        elif status == "rejected":
            raise Exception(
                "D-ID rejected the request.\n"
                "Make sure teacher image shows a clear human face."
            )

        time.sleep(POLL_INTERVAL_SEC)
        elapsed += POLL_INTERVAL_SEC

    raise Exception(
        f"D-ID timed out after {POLL_TIMEOUT_SEC}s.\n"
        "Check studio.d-id.com — video may still be processing."
    )


def download_video(video_url: str) -> bytes:
    """
    Step 3 — Download the MP4 video from D-ID CDN.

    Args:
        video_url: result_url from poll_video_status()

    Returns:
        MP4 video bytes
    """
    print("  - Downloading video...")
    response = requests.get(video_url, timeout=60, stream=True)

    if response.status_code != 200:
        raise Exception(f"Video download failed: HTTP {response.status_code}")

    video_bytes = response.content
    print(f"  ✓ Downloaded ({len(video_bytes)/1024:.1f} KB)")
    return video_bytes


def save_video(video_bytes: bytes, filename: str) -> str:
    """Saves MP4 bytes to file, creates directory if needed."""
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(video_bytes)
    abs_path = str(filepath.resolve())
    print(f"  ✓ Video saved: {abs_path}")
    return abs_path


def generate_avatar_video(audio_bytes: bytes) -> bytes:
    """
    Main function — complete pipeline:
    audio bytes → Cloudinary → D-ID → MP4 bytes

    Args:
        audio_bytes: WAV audio from tts.py generate_voice()

    Returns:
        MP4 video bytes of teacher avatar speaking
    """
    print("\n  Starting avatar generation...")
    start_time = time.time()

    talk_id   = upload_audio_to_did(audio_bytes)
    video_url = poll_video_status(talk_id)
    video     = download_video(video_url)

    elapsed = round(time.time() - start_time, 1)
    print(f"  ✓ Avatar ready in {elapsed}s")
    return video


def check_did_credits() -> None:
    """Check remaining D-ID credits."""
    try:
        response = requests.get(
            f"{DID_BASE_URL}/credits",
            headers=get_did_headers(),
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  D-ID Credits — Remaining: {data.get('remaining')} / Total: {data.get('total')}")
        else:
            print(f"  Could not fetch credits: {response.status_code}")
    except Exception as e:
        print(f"  Credits check failed: {e}")


if __name__ == "__main__":
    from rag import get_context
    from llm import generate_script
    from tts import generate_voice, save_audio

    print("=" * 60)
    print("Testing Avatar Pipeline")
    print("=" * 60)

    print("\n[PRE-CHECK] Credentials")
    print("-" * 60)
    check_did_credits()

    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        print("\n✗ Cloudinary credentials missing in .env!")
        print("  Add these 3 lines to your .env file:")
        print("  CLOUDINARY_CLOUD_NAME=your_cloud_name")
        print("  CLOUDINARY_API_KEY=your_api_key")
        print("  CLOUDINARY_API_SECRET=your_api_secret")
        print("  Get them free at cloudinary.com")
        exit(1)

    print(f"  Teacher image: {TEACHER_IMAGE_URL}")
    print(f"  Cloudinary: ✓ configured")

    print("\n[TEST] Full pipeline — Osmosis")
    print("-" * 60)
    print("This uses 1 D-ID credit. Proceeding in 3 seconds...")
    time.sleep(3)

    try:
        print("\nStep 1: NCERT context...")
        context = get_context("Osmosis")
        print(f"  ✓ {len(context)} chars")

        print("Step 2: Teacher script...")
        script = generate_script("Osmosis", context, attempt=1)
        print(f"  ✓ {script['word_count']} words | {script['emotions']}")

        print("Step 3: Voice generation...")
        audio = generate_voice(script["clean_text"])
        save_audio(audio, "test_outputs/avatar_audio.wav")
        print(f"  ✓ {len(audio)} bytes")

        print("Step 4: Avatar video...")
        video = generate_avatar_video(audio)
        save_video(video, "test_outputs/avatar_video.mp4")

        print("\n" + "=" * 60)
        print("✓ Complete! Open test_outputs/avatar_video.mp4")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")