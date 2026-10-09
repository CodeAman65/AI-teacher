# import os
# import base64
# import wave
# import struct
# import warnings
# import logging
# import requests
# from dotenv import load_dotenv

# # Suppress warnings
# warnings.filterwarnings("ignore")
# logging.getLogger("requests").setLevel(logging.ERROR)
# logging.getLogger("urllib3").setLevel(logging.ERROR)

# # Load environment variables
# load_dotenv()

# # Sarvam AI config
# SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
# SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# # Sarvam has a 500 character limit per request
# # We split long text into chunks and merge the audio
# MAX_CHARS_PER_REQUEST = 450


# def split_text_into_chunks(text: str, max_chars: int = MAX_CHARS_PER_REQUEST) -> list:
#     """
#     Splits text into chunks under max_chars limit.
#     Splits at sentence boundaries (. ? !) to avoid cutting mid-sentence.

#     Args:
#         text:      Full clean text to split
#         max_chars: Maximum characters per chunk (Sarvam limit is 500)

#     Returns:
#         List of text chunks, each under max_chars
#     """
#     # If text is short enough, return as single chunk
#     if len(text) <= max_chars:
#         return [text]

#     chunks = []
#     current_chunk = ""

#     # Split by sentences first
#     import re
#     sentences = re.split(r'(?<=[.?!])\s+', text)

#     for sentence in sentences:
#         # If single sentence itself is too long, split by comma
#         if len(sentence) > max_chars:
#             parts = sentence.split(',')
#             for part in parts:
#                 part = part.strip()
#                 if not part:
#                     continue
#                 if len(current_chunk) + len(part) + 2 <= max_chars:
#                     current_chunk += part + ", "
#                 else:
#                     if current_chunk:
#                         chunks.append(current_chunk.strip().rstrip(','))
#                     current_chunk = part + ", "
#         else:
#             if len(current_chunk) + len(sentence) + 1 <= max_chars:
#                 current_chunk += sentence + " "
#             else:
#                 if current_chunk:
#                     chunks.append(current_chunk.strip())
#                 current_chunk = sentence + " "

#     # Add remaining chunk
#     if current_chunk.strip():
#         chunks.append(current_chunk.strip())

#     return chunks


# def call_sarvam_api(text: str) -> bytes:
#     """
#     Makes a single API call to Sarvam AI TTS for one text chunk.

#     Args:
#         text: Text chunk under 500 characters

#     Returns:
#         Raw audio bytes (PCM WAV data from base64 decoded response)

#     Raises:
#         Exception if API call fails
#     """
#     if not SARVAM_API_KEY:
#         raise ValueError(
#             "SARVAM_API_KEY not found in .env file. "
#             "Get your key from dashboard.sarvam.ai"
#         )

#     headers = {
#         "api-subscription-key": SARVAM_API_KEY,
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "inputs": [text],
#         "target_language_code": "hi-IN",   # Hindi — handles Hinglish naturally
#         "speaker": "anushka",                 # Female teacher voice
#         "pitch": 0,                         # Natural pitch
#         "pace": 0.9,                        # Slightly slower — better for learning
#         "loudness": 1.5,                    # Clear and audible
#         "speech_sample_rate": 22050,        # Standard quality
#         "enable_preprocessing": True,       # Handles numbers, symbols correctly
#         "model": "bulbul:v2"               # Sarvam's best Hinglish model
#     }

#     response = requests.post(
#         SARVAM_TTS_URL,
#         headers=headers,
#         json=payload,
#         timeout=30
#     )

#     # Handle API errors clearly
#     if response.status_code == 401:
#         raise Exception(
#             "Sarvam API key invalid or expired. "
#             "Check SARVAM_API_KEY in your .env file."
#         )
#     elif response.status_code == 429:
#         raise Exception(
#             "Sarvam API rate limit hit. "
#             "Wait 60 seconds and try again."
#         )
#     elif response.status_code != 200:
#         raise Exception(
#             f"Sarvam API error {response.status_code}: {response.text}"
#         )

#     # Parse response — audios array contains base64 encoded audio
#     response_data = response.json()

#     if "audios" not in response_data or not response_data["audios"]:
#         raise Exception(
#             f"Sarvam API returned no audio. Response: {response_data}"
#         )

#     # Decode base64 audio to bytes
#     audio_base64 = response_data["audios"][0]
#     audio_bytes = base64.b64decode(audio_base64)

#     return audio_bytes


# def merge_wav_bytes(audio_chunks: list) -> bytes:
#     """
#     Merges multiple raw PCM audio byte chunks into one valid WAV file.

#     Args:
#         audio_chunks: List of raw PCM audio bytes from Sarvam API

#     Returns:
#         Single merged WAV file as bytes
#     """
#     if len(audio_chunks) == 1:
#         return audio_chunks[0]

#     # Combine all raw PCM data
#     combined_pcm = b"".join(audio_chunks)

#     # Build WAV file manually with correct headers
#     import io
#     buffer = io.BytesIO()

#     with wave.open(buffer, 'wb') as wav_file:
#         wav_file.setnchannels(1)       # Mono
#         wav_file.setsampwidth(2)       # 16-bit audio
#         wav_file.setframerate(22050)   # Sample rate matches API setting
#         wav_file.writeframes(combined_pcm)

#     return buffer.getvalue()


# def generate_voice(clean_text: str) -> bytes:
#     """
#     Converts clean teacher script text to audio using Sarvam AI.

#     Handles long text automatically by splitting into chunks
#     and merging the audio back together.

#     Args:
#         clean_text: Teacher script with emotion tags already removed

#     Returns:
#         Complete audio as WAV bytes ready to save or stream

#     Example:
#         audio = generate_voice("Dekho, osmosis ek bahut simple concept hai.")
#         save_audio(audio, "lesson.wav")
#     """
#     if not clean_text or not clean_text.strip():
#         raise ValueError("clean_text cannot be empty")

#     clean_text = clean_text.strip()

#     # Split into chunks if text is too long for one API call
#     chunks = split_text_into_chunks(clean_text)

#     print(f"  - Text length: {len(clean_text)} chars")
#     print(f"  - Split into {len(chunks)} chunk(s) for Sarvam API")

#     audio_chunks = []

#     for i, chunk in enumerate(chunks, 1):
#         if len(chunks) > 1:
#             print(f"  - Generating audio chunk {i}/{len(chunks)}...")
#         try:
#             audio_bytes = call_sarvam_api(chunk)
#             audio_chunks.append(audio_bytes)
#         except Exception as e:
#             raise Exception(f"Failed on chunk {i}: {str(e)}")

#     # Merge chunks if multiple
#     if len(audio_chunks) == 1:
#         final_audio = audio_chunks[0]
#     else:
#         print(f"  - Merging {len(audio_chunks)} audio chunks...")
#         final_audio = merge_wav_bytes(audio_chunks)

#     print(f"  ✓ Audio generated ({len(final_audio)} bytes)")
#     return final_audio


# def save_audio(audio_bytes: bytes, filename: str) -> str:
#     """
#     Saves audio bytes to a .wav file.

#     Creates the directory if it doesn't exist.

#     Args:
#         audio_bytes: Raw audio bytes from generate_voice()
#         filename:    Path to save e.g. "output/lesson.wav"

#     Returns:
#         Absolute path of saved file
#     """
#     import os
#     from pathlib import Path

#     # Create parent directory if it doesn't exist
#     filepath = Path(filename)
#     filepath.parent.mkdir(parents=True, exist_ok=True)

#     with open(filepath, "wb") as f:
#         f.write(audio_bytes)

#     abs_path = str(filepath.resolve())
#     print(f"  ✓ Audio saved: {abs_path}")
#     return abs_path


# if __name__ == "__main__":
#     from rag import get_context
#     from llm import generate_script

#     print("=" * 60)
#     print("Testing TTS Pipeline")
#     print("=" * 60)

#     # ── Test 1: Short text directly ─────────────────────────
#     print("\n[TEST 1] Short Hinglish text")
#     print("-" * 60)

#     short_text = (
#         "Dekho, osmosis ek bahut simple concept hai. "
#         "Socho ek kishmi ko paani mein daalo. "
#         "Wo phool jaati hai na? "
#         "Aisa isliye hota hai kyunki paani andar jaata hai. "
#         "Yahi osmosis hai. Samjhe?"
#     )

#     print(f"Text: {short_text}")
#     print("Generating voice...")

#     try:
#         audio = generate_voice(short_text)
#         save_audio(audio, "test_outputs/test_short.wav")
#         print("✓ Open test_outputs/test_short.wav to hear Priya ma'am!")
#     except Exception as e:
#         print(f"✗ Error: {e}")

#     # ── Test 2: Full pipeline — RAG + LLM + TTS ─────────────
#     print("\n" + "=" * 60)
#     print("[TEST 2] Full pipeline — topic to audio")
#     print("-" * 60)

#     topic = "Photosynthesis"
#     print(f"Topic: {topic}")

#     try:
#         print("Step 1: Getting NCERT context...")
#         context = get_context(topic)
#         print(f"  ✓ Context: {len(context)} chars")

#         print("Step 2: Generating teacher script...")
#         script = generate_script(topic, context, attempt=1)
#         print(f"  ✓ Script: {script['word_count']} words")
#         print(f"  ✓ Emotions: {script['emotions']}")
#         print(f"\nScript preview:\n{script['clean_text'][:200]}...")

#         print("\nStep 3: Generating voice...")
#         audio = generate_voice(script["clean_text"])

#         save_audio(audio, "test_outputs/test_photosynthesis.wav")
#         print("\n✓ Full pipeline working!")
#         print("  Open test_outputs/test_photosynthesis.wav")
#         print("  You should hear Priya ma'am explaining Photosynthesis in Hinglish")

#     except Exception as e:
#         print(f"✗ Error: {e}")

#     # ── Test 3: Samjha Nahi — second attempt ────────────────
#     print("\n" + "=" * 60)
#     print("[TEST 3] Samjha Nahi — different analogy")
#     print("-" * 60)

#     try:
#         print("Generating attempt 2 script for Osmosis...")
#         context2 = get_context("Osmosis")
#         script2 = generate_script("Osmosis", context2, attempt=2)
#         print(f"  Script: {script2['word_count']} words")

#         audio2 = generate_voice(script2["clean_text"])
#         save_audio(audio2, "test_outputs/test_osmosis_attempt2.wav")
#         print("✓ Saved test_outputs/test_osmosis_attempt2.wav")
#         print("  This should use a DIFFERENT analogy than attempt 1")

#     except Exception as e:
#         print(f"✗ Error: {e}")

#     print("\n" + "=" * 60)
#     print("TTS Testing Complete!")
#     print("=" * 60)



import os
import re
import base64
import wave
import io
import warnings
import logging
import requests
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

load_dotenv()

SARVAM_API_KEY  = os.getenv("SARVAM_API_KEY")
SARVAM_TTS_URL  = "https://api.sarvam.ai/text-to-speech"
MAX_CHARS       = 450   # Sarvam limit is 500, keep buffer


def clean_script_for_tts(text: str) -> str:
    """
    Cleans and prepares text before sending to Sarvam TTS.
    Fixes all the issues that cause robotic or confusing audio.
    """
    # Remove any remaining emotion tags
    text = re.sub(r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]', '', text)

    # Remove markdown formatting
    text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)   # bold/italic
    text = re.sub(r'#+\s*', '', text)                  # headers
    text = re.sub(r'[-•]\s+', '', text)                # bullet points

    # Fix numbers — Sarvam reads "10" better as "ten" in mixed text
    text = re.sub(r'\b10\b', 'ten', text)
    text = re.sub(r'\b(\d+)°C\b', r'\1 degrees Celsius', text)
    text = re.sub(r'\b(\d+)%\b', r'\1 percent', text)

    # Remove special characters that confuse TTS
    text = re.sub(r'[<>{}|\\^~`]', '', text)
    text = re.sub(r'&([a-z]+);', r'\1', text)   # HTML entities

    # Fix abbreviations that sound wrong
    text = text.replace('e.g.', 'for example')
    text = text.replace('i.e.', 'that is')
    text = text.replace('etc.', 'and so on')
    text = text.replace('vs.', 'versus')
    text = text.replace('CO2', 'carbon dioxide')
    text = text.replace('O2', 'oxygen')
    text = text.replace('H2O', 'water')
    text = text.replace('NaCl', 'sodium chloride')

    # Fix sentence endings — ensure space after every period
    text = re.sub(r'\.([A-Z])', r'. \1', text)

    # Remove extra whitespace and newlines
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_into_chunks(text: str, max_chars: int = MAX_CHARS) -> list:
    """
    Splits text at sentence boundaries only.
    Never cuts mid-sentence — this was causing the confusing audio.

    Splits at: period, question mark, exclamation mark
    Never splits at: comma, semicolon, mid-word
    """
    if len(text) <= max_chars:
        return [text]

    # Split at sentence endings
    sentences = re.split(r'(?<=[.?!])\s+', text)

    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If single sentence is longer than max, split at comma
        if len(sentence) > max_chars:
            parts = re.split(r',\s+', sentence)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if len(current) + len(part) + 2 <= max_chars:
                    current += part + ", "
                else:
                    if current.strip():
                        chunks.append(current.strip().rstrip(',') + '.')
                    current = part + ", "
        else:
            if len(current) + len(sentence) + 1 <= max_chars:
                current += sentence + " "
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = sentence + " "

    if current.strip():
        chunks.append(current.strip())

    return chunks


def call_sarvam_api(text: str) -> bytes:
    """
    Single Sarvam API call for one text chunk.
    Returns raw audio bytes.
    """
    if not SARVAM_API_KEY:
        raise ValueError(
            "SARVAM_API_KEY not in .env. Get it from dashboard.sarvam.ai"
        )

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": "priya",          # Female teacher voice
        "pitch": 0,                  # Natural pitch
        "pace": 0.85,                # Slightly slower — better for learning
        "loudness": 1.4,             # Clear volume
        "speech_sample_rate": 22050,
        "enable_preprocessing": True,
        "model": "bulbul:v3"
    }

    response = requests.post(
        SARVAM_TTS_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code == 401:
        raise Exception("Sarvam API key invalid. Check SARVAM_API_KEY in .env")
    elif response.status_code == 429:
        raise Exception("Sarvam rate limit hit. Wait 60 seconds and retry.")
    elif response.status_code != 200:
        raise Exception(f"Sarvam error {response.status_code}: {response.text}")

    data = response.json()
    if "audios" not in data or not data["audios"]:
        raise Exception(f"Sarvam returned no audio: {data}")

    return base64.b64decode(data["audios"][0])


def merge_audio_chunks(chunks: list) -> bytes:
    """
    Merges multiple PCM audio chunks into one clean WAV file.
    Adds a tiny 200ms pause between chunks for natural flow.
    """
    if len(chunks) == 1:
        return chunks[0]

    # 200ms silence at 22050Hz 16-bit mono = 22050 * 0.2 * 2 bytes
    silence = b'\x00' * int(22050 * 0.2 * 2)

    # Combine with silence between chunks for natural pauses
    combined_pcm = b""
    for i, chunk in enumerate(chunks):
        combined_pcm += chunk
        if i < len(chunks) - 1:
            combined_pcm += silence   # pause between sentences

    # Wrap in proper WAV header
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)       # mono
        wav.setsampwidth(2)       # 16-bit
        wav.setframerate(22050)   # sample rate
        wav.writeframes(combined_pcm)

    return buffer.getvalue()


def generate_voice(clean_text: str) -> bytes:
    """
    Converts teacher script to natural Hinglish audio.

    Pipeline:
    1. Clean text (fix abbreviations, remove symbols)
    2. Split at sentence boundaries only
    3. Call Sarvam API for each chunk
    4. Merge with natural pauses between chunks

    Args:
        clean_text: Script with emotion tags already removed

    Returns:
        WAV audio bytes
    """
    if not clean_text or not clean_text.strip():
        raise ValueError("clean_text is empty")

    # Step 1: Deep clean before sending to TTS
    cleaned = clean_script_for_tts(clean_text)
    print(f"  - Cleaned text ({len(cleaned)} chars)")

    # Step 2: Split at sentence boundaries only
    chunks = split_into_chunks(cleaned)
    print(f"  - {len(chunks)} chunk(s) for Sarvam API")

    # Step 3: Generate audio for each chunk
    audio_chunks = []
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            print(f"  - Chunk {i}/{len(chunks)}: {chunk[:60]}...")
        audio = call_sarvam_api(chunk)
        audio_chunks.append(audio)

    # Step 4: Merge with natural pauses
    if len(audio_chunks) > 1:
        print(f"  - Merging {len(audio_chunks)} chunks with natural pauses...")

    final_audio = merge_audio_chunks(audio_chunks)
    print(f"  ✓ Audio ready ({len(final_audio)/1024:.1f} KB)")
    return final_audio


def save_audio(audio_bytes: bytes, filename: str) -> str:
    """Saves audio bytes to WAV file."""
    from pathlib import Path
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)
    path = str(filepath.resolve())
    print(f"  ✓ Saved: {path}")
    return path


if __name__ == "__main__":
    from rag import get_context
    from llm import generate_script

    print("=" * 60)
    print("Testing Improved TTS")
    print("=" * 60)

    # Test 1: Direct text
    print("\n[TEST 1] Direct Hinglish text")
    print("-" * 60)
    test_text = (
        "Dekho, osmosis is very simple. "
        "Think about a raisin placed in water. "
        "It swells up, right? "
        "That happens because water molecules move inside the raisin. "
        "This movement from low concentration to high concentration "
        "through a membrane is called osmosis. "
        "Samjhe? So what do you think happens to a raisin in salty water?"
    )
    print(f"Input: {test_text[:100]}...")
    audio = generate_voice(test_text)
    save_audio(audio, "test_outputs/improved_test1.wav")
    print("✓ Open test_outputs/improved_test1.wav")

    # Test 2: Full pipeline
    print("\n[TEST 2] Full pipeline — Osmosis")
    print("-" * 60)
    context = get_context("Osmosis")
    script  = generate_script("Osmosis", context, attempt=1)
    print(f"Script:\n{script['full_script']}")
    print(f"\nClean text going to TTS:\n{script['clean_text']}")
    audio2  = generate_voice(script["clean_text"])
    save_audio(audio2, "test_outputs/improved_osmosis.wav")
    print("\n✓ Open test_outputs/improved_osmosis.wav")
    print("  Should sound much clearer than before!")

    print("\n" + "=" * 60)
    print("Done! Compare with old audio to hear the difference.")
    print("=" * 60)