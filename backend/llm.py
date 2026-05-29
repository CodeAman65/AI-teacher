import os
import re
import warnings
import logging
from dotenv import load_dotenv
from groq import Groq

# Suppress warnings
warnings.filterwarnings("ignore")
logging.getLogger("groq").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────────────────────────
# TEACHER SYSTEM PROMPT — This is the heart of the product.
# Spend time tweaking this if the output doesn't feel natural.
# ─────────────────────────────────────────────────────────────
TEACHER_SYSTEM_PROMPT = """
You are Priya ma'am, an enthusiastic and caring Class 10 Science teacher from India.
You have 10 years of experience making tough Science concepts feel easy and fun.

YOUR PERSONALITY:
- Warm, encouraging, never makes students feel stupid
- Gets genuinely excited about Science
- Celebrates when students understand something

YOUR LANGUAGE STYLE:
- Speak in natural Hinglish (mix of Hindi and English)
- Use these words naturally: dekho, sochte hain, samjhe, bilkul sahi, achha, 
  toh, matlab, actually, basically, yaad rakhna, ek baar
- NEVER use textbook language directly — always rephrase simply
- Short sentences. Easy words. Like you are talking, not reading.

YOUR EXPLANATION STRUCTURE:
- ALWAYS start paragraph 1 with a real-life example the student already knows
  (examples: chai, cricket, mobile phone, auto-rickshaw, AC, fridge, cooking,
   WhatsApp, YouTube, rain, river, mirror, candle, torch)
- Paragraph 2: explain the actual Science concept building on that example
- Paragraph 3: connect back to NCERT — what to remember for exams

FORMAT RULES — follow these EXACTLY:
- Exactly 3 paragraphs
- Total word count: 180 to 220 words
- End EVERY paragraph with exactly ONE emotion tag
- Choose emotion tag based on what fits naturally:
  [SMILE]         — when saying something warm or encouraging
  [NOD]           — when confirming a point or saying "right?"
  [CURIOUS]       — when asking the student to think
  [RAISE_EYEBROW] — when revealing something surprising
  [EXCITED]       — when the concept is really cool
  [PAUSE]         — when student needs a moment to absorb
- End the ENTIRE explanation with one simple question to check understanding
  (question should be easy, not scary — like "toh batao, samjhe na?")

EXAMPLE OUTPUT FORMAT:
Dekho, socho ek baar jab tum chai banate ho... [SMILE]
Ab isko Science se connect karte hain... [CURIOUS]
Toh NCERT mein yeh concept aise define hota hai... [NOD]
Ab batao — agar paani mein namak daalo toh kya hoga?
"""


def generate_script(topic: str, context: str, attempt: int = 1) -> dict:
    """
    Generates a teaching script for the given topic using Groq LLM.

    Args:
        topic:   Clean topic name e.g. "Osmosis", "Photosynthesis"
        context: NCERT text chunks retrieved from Pinecone RAG
        attempt: 1 = first explanation, 2+ = re-explanation with new analogy

    Returns:
        dict with keys:
            full_script  — complete script with emotion tags
            clean_text   — script with emotion tags removed (for TTS)
            emotions     — list of emotion tags found e.g. ["SMILE", "CURIOUS"]
            word_count   — total word count of clean_text
    """

    # Build user message
    if attempt == 1:
        user_message = f"""
Topic to explain: {topic}

NCERT Reference Content:
{context}

Now generate the teaching script following all format rules exactly.
"""
    else:
        user_message = f"""
Topic to explain: {topic}

NCERT Reference Content:
{context}

IMPORTANT: The student did not understand the previous explanation.
Use a COMPLETELY DIFFERENT real-life analogy this time.
Attempt number: {attempt}

Analogy suggestions for attempt {attempt}:
- Attempt 2: Use something from kitchen / cooking
- Attempt 3: Use cricket or a sport
- Attempt 4: Use mobile phone / technology
- Attempt 5: Use a story format

Now generate a fresh teaching script with a new analogy.
"""

    # Call Groq API
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",       # Fast, free, high quality
        max_tokens=500,
        temperature=0.75,                    # Slight creativity for natural Hinglish
        messages=[
            {
                "role": "system",
                "content": TEACHER_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    full_script = response.choices[0].message.content.strip()

    # Remove emotion tags for clean TTS text
    clean_text = re.sub(r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]', '', full_script)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Clean extra spaces

    # Extract all emotion tags found in order
    emotions = re.findall(r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]', full_script)

    word_count = len(clean_text.split())

    return {
        "full_script": full_script,
        "clean_text": clean_text,
        "emotions": emotions,
        "word_count": word_count
    }


if __name__ == "__main__":
    # ── Import RAG functions for testing ────────────────────
    from rag import normalize_query, get_context

    print("=" * 60)
    print("Testing LLM Script Generation")
    print("=" * 60)

    # ── Test 1: First attempt explanation ───────────────────
    print("\n[TEST 1] First explanation — Osmosis")
    print("-" * 60)

    topic = "Osmosis"
    context = get_context(topic)

    result = generate_script(topic, context, attempt=1)

    print(f"\nFULL SCRIPT (with emotion tags):")
    print(result["full_script"])
    print(f"\nEMOTIONS found: {result['emotions']}")
    print(f"WORD COUNT: {result['word_count']}")
    print(f"\nCLEAN TEXT (for TTS):")
    print(result["clean_text"])

    # ── Test 2: Samjha Nahi — second attempt ────────────────
    print("\n" + "=" * 60)
    print("[TEST 2] Samjha Nahi — attempt 2 (different analogy)")
    print("-" * 60)

    result2 = generate_script(topic, context, attempt=2)

    print(f"\nFULL SCRIPT (attempt 2):")
    print(result2["full_script"])
    print(f"\nEMOTIONS: {result2['emotions']}")
    print(f"WORD COUNT: {result2['word_count']}")

    # ── Test 3: Different topic ──────────────────────────────
    print("\n" + "=" * 60)
    print("[TEST 3] Different topic — Photosynthesis")
    print("-" * 60)

    topic2 = "Photosynthesis"
    context2 = get_context(topic2)
    result3 = generate_script(topic2, context2, attempt=1)

    print(f"\nFULL SCRIPT:")
    print(result3["full_script"])
    print(f"\nEMOTIONS: {result3['emotions']}")
    print(f"WORD COUNT: {result3['word_count']}")

    print("\n" + "=" * 60)
    print("✓ LLM Testing Complete!")
    print("=" * 60)