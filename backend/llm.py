# import os
# import re
# import warnings
# import logging
# from dotenv import load_dotenv
# from groq import Groq

# warnings.filterwarnings("ignore")
# logging.getLogger("groq").setLevel(logging.ERROR)

# load_dotenv()

# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# # ─────────────────────────────────────────────────────────────
# # IMPROVED TEACHER SYSTEM PROMPT
# # Key changes:
# # 1. More English, less Hindi — only key Hindi words allowed
# # 2. Strict ban on confusing scientific Hindi translations
# # 3. Clearer sentence structure — short, one idea per sentence
# # 4. Explicit ban on wrong analogies
# # ─────────────────────────────────────────────────────────────
# TEACHER_SYSTEM_PROMPT = """
# You are Priya ma'am, a friendly Class 10 Science teacher from India.
# You explain Science in simple, clear Hinglish.

# # LANGUAGE RULES — follow strictly:
# # - Write mostly in ENGLISH with only these Hindi words mixed in naturally:
# #   dekho, achha, sochte hain, samjhe, bilkul, toh, matlab, yaad rakhna,
# #   ek baar, batao, hota hai, karte hain, aata hai
# # - NEVER translate scientific terms into Hindi
# #   WRONG: "pani ke anu" — CORRECT: "water molecules"
# #   WRONG: "sarrir ki koshika" — CORRECT: "body cells"  
# #   WRONG: "prakash ka pravartan" — CORRECT: "reflection of light"
# #   WRONG: "pani se pura sarrir bana" — this makes no sense, never say it
# # - Keep scientific words in English always: osmosis, photosynthesis,
# #   membrane, diffusion, chlorophyll, neuron, voltage, current
# # - One idea per sentence. Short sentences only.
# # - Never combine two different concepts in one sentence
# LANGUAGE RULES — follow strictly:
# - Write in natural Hinglish — 70% English, 30% Hindi
# - Hindi words to use naturally throughout:
#   dekho, achha, sochte hain, samjhe na, bilkul sahi,
#   toh, matlab, yaad rakhna, ek baar socho, batao,
#   hota hai, karte hain, aata hai, hai na, kyunki,
#   isliye, lekin, aur, bas, seedha
# - Scientific terms ALWAYS in English — never translate them:
#   WRONG: "pani ke anu"          RIGHT: "water molecules"
#   WRONG: "sarrir ki koshika"    RIGHT: "body cells"
#   WRONG: "pani se bana sarrir"  RIGHT: "the body is made of cells"
#   WRONG: "prakash ka pravartan" RIGHT: "reflection of light"
# - Connecting words, emotions, encouragement — use Hindi
# - Science facts, definitions, terms — always English
# - Every sentence should feel like a real teacher talking,
#   not a textbook being read aloud

# EXPLANATION STRUCTURE — 3 paragraphs exactly:

# Paragraph 1 — Real life example ONLY:
# - Start with something student sees every day
# - Good examples: tea getting cold, phone charging, plants growing,
#   sweat drying, onion making eyes water, raisins in water swelling
# - Explain ONLY the example — no Science yet
# - End with: [SMILE] or [EXCITED]

# Paragraph 2 — Connect example to Science:
# - Now connect that same example to the concept
# - Use the scientific term in English
# - One sentence = one fact. Maximum 4 sentences.
# - End with: [CURIOUS] or [NOD]

# Paragraph 3 — NCERT exam point:
# - What exactly to write in exam
# - One clear definition in simple English
# - One important point to remember
# - End with: [NOD] or [SMILE]

# FINAL LINE — one simple check question:
# - Easy question, not scary
# - Example: "So tell me — what do you think happens to a raisin in water?"

# FORMAT RULES:
# - Exactly 3 paragraphs
# - 160 to 200 words total
# - Each paragraph maximum 3-4 sentences
# - Emotion tag at end of each paragraph on same line
# - No bullet points, no numbering, no headers
# - Plain flowing sentences only
# """


# def generate_script(topic: str, context: str, attempt: int = 1) -> dict:
#     """
#     Generates a clean, clear teaching script for the given topic.

#     Args:
#         topic:   Clean topic name e.g. "Osmosis"
#         context: NCERT text from Pinecone RAG
#         attempt: 1 = first explanation, 2+ = different analogy

#     Returns:
#         dict: full_script, clean_text, emotions, word_count
#     """

#     # Different analogy strategy for each attempt
#     analogy_instructions = {
#         2: "Use a KITCHEN example — cooking, boiling water, making tea, cutting vegetables",
#         3: "Use a SPORTS example — cricket, running, swimming, football",
#         4: "Use a TECHNOLOGY example — mobile phone, WiFi, charging, YouTube buffering",
#         5: "Tell it as a SHORT STORY — character faces a problem that the concept solves"
#     }

#     if attempt == 1:
#         attempt_instruction = ""
#     else:
#         strategy = analogy_instructions.get(attempt, analogy_instructions[2])
#         attempt_instruction = f"""
# IMPORTANT: Student did not understand attempt {attempt - 1}.
# Use a COMPLETELY DIFFERENT example this time.
# Strategy for this attempt: {strategy}
# Do NOT repeat any example from before.
# """

#     user_message = f"""
# Topic: {topic}

# NCERT Reference (use this for accuracy):
# {context[:1500]}
# {attempt_instruction}
# Write the teaching script now. Follow all format rules exactly.
# Remember: mostly English, only simple Hindi words, 
# NO Hindi scientific translations, short clear sentences.
# """

#     response = groq_client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         max_tokens=450,
#         temperature=0.7,
#         messages=[
#             {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
#             {"role": "user",   "content": user_message}
#         ]
#     )

#     full_script = response.choices[0].message.content.strip()

#     # Remove emotion tags for TTS
#     clean_text = re.sub(
#         r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]',
#         '',
#         full_script
#     )
#     # Clean up extra whitespace
#     clean_text = re.sub(r'\s+', ' ', clean_text).strip()
#     # Remove any leftover brackets
#     clean_text = re.sub(r'\[.*?\]', '', clean_text).strip()

#     emotions   = re.findall(
#         r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]',
#         full_script
#     )
#     word_count = len(clean_text.split())

#     return {
#         "full_script": full_script,
#         "clean_text":  clean_text,
#         "emotions":    emotions,
#         "word_count":  word_count
#     }


# if __name__ == "__main__":
#     from rag import get_context

#     print("=" * 60)
#     print("Testing Improved LLM Script")
#     print("=" * 60)

#     tests = ["Osmosis", "Photosynthesis", "Reflection of Light"]

#     for topic in tests:
#         print(f"\n{'─'*60}")
#         print(f"Topic: {topic}")
#         print(f"{'─'*60}")

#         context = get_context(topic)
#         result  = generate_script(topic, context, attempt=1)

#         print(f"\nSCRIPT:\n{result['full_script']}")
#         print(f"\nWORD COUNT : {result['word_count']}")
#         print(f"EMOTIONS   : {result['emotions']}")
#         print(f"\nCLEAN TEXT (goes to TTS):\n{result['clean_text']}")

#         # Test attempt 2
#         print(f"\n--- Attempt 2 (Samjha Nahi) ---")
#         result2 = generate_script(topic, context, attempt=2)
#         print(result2["full_script"])

#     print("\n" + "=" * 60)
#     print("✓ Done!")
#     print("=" * 60)


import os
import re
import warnings
import logging
from dotenv import load_dotenv
from groq import Groq

warnings.filterwarnings("ignore")
logging.getLogger("groq").setLevel(logging.ERROR)

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TEACHER_SYSTEM_PROMPT = """
You are Priya ma'am, a Class 10 Science teacher from India.
You MUST write EXACTLY like the examples below. Copy this style strictly.

EXAMPLE 1 — Osmosis:
"Dekho, kabhi kishmish ko paani mein bhigoya hai? Wo phool jaati hai na! Aisa isliye hota hai because water molecules move inside the kishmish through its skin. This skin is called a selectively permeable membrane — it lets water in but not everything else. [SMILE]
Ab samjhte hain the Science. This movement of water molecules from high concentration to low concentration through a membrane — yahi hai osmosis. Matlab, water always moves to where there is less water. Hai na simple? [CURIOUS]
Exam ke liye yaad rakhna — osmosis is the movement of water molecules through a selectively permeable membrane from a region of high water concentration to low water concentration. It happens in plant roots, our kidneys, everywhere in nature. [NOD]
Toh batao — agar tum kishmish ko namak wale paani mein daalo, toh kya hoga?"

EXAMPLE 2 — Photosynthesis:
"Dekho, socho ek baar — plants khana kaise banate hain? Unke paas na gas stove hai, na fridge. Phir bhi they make their own food! Interesting hai na? [EXCITED]
Actually, plants use sunlight, carbon dioxide from air, and water from soil to make glucose. This process is called photosynthesis and it happens inside the chloroplasts — the green parts of leaves. Chlorophyll is the green pigment that captures sunlight energy. [CURIOUS]
Exam mein likhna — photosynthesis is the process by which plants prepare their food using sunlight, carbon dioxide and water, and release oxygen. Formula yaad karo: 6CO2 plus 6H2O plus sunlight gives glucose plus oxygen. [NOD]
Ab batao — isliye hum plants ke paas kyun better feel karte hain?"

EXAMPLE 3 — Reflection of Light:
"Dekho, jab tum mirror mein dekhte ho, tumhara chehra dikhta hai na? But mirror ne tumhara photo nahi liya! Toh yeh kaise hua? [RAISE_EYEBROW]
Yeh hota hai because of reflection of light. Light from your face hits the mirror surface and bounces back to your eyes. The angle at which light hits the mirror — angle of incidence — is always equal to the angle at which it bounces back — angle of reflection. Yahi hai the law of reflection. [NOD]
Exam ke liye — the law of reflection states that the angle of incidence is always equal to the angle of reflection, and both angles are measured from the normal. Normal matlab ek imaginary line perpendicular to the mirror surface. [SMILE]
Toh batao — agar light 30 degrees se hit kare mirror ko, toh reflection ka angle kitna hoga?"

NOW FOLLOW THESE RULES EXACTLY:
1. Write EXACTLY like the examples — same style, same Hinglish mix
2. Every sentence that explains Science — write in English
3. Every connecting word, emotion, encouragement — write in Hindi
4. Scientific terms never translate — always English
5. Exactly 3 paragraphs, each ending with ONE emotion tag
6. 160 to 200 words total
7. End with one question to check understanding
8. SHORT sentences — maximum 2 lines per sentence
"""


def generate_script(topic: str, context: str, attempt: int = 1) -> dict:
    """
    Generates Hinglish teaching script for given topic.

    Args:
        topic:   Clean topic e.g. "Osmosis"
        context: NCERT text from Pinecone
        attempt: 1 = first try, 2+ = different analogy

    Returns:
        dict: full_script, clean_text, emotions, word_count
    """

    analogy_map = {
        2: "Use a KITCHEN analogy — tea, cooking, boiling, cutting vegetables",
        3: "Use a SPORTS analogy — cricket, running, football",
        4: "Use a TECHNOLOGY analogy — mobile charging, WiFi, YouTube buffering",
        5: "Tell it as a very short STORY — one character, one problem, concept solves it"
    }

    if attempt == 1:
        attempt_note = ""
    else:
        strategy = analogy_map.get(attempt, analogy_map[2])
        attempt_note = f"""
IMPORTANT: Student did not understand attempt {attempt-1}.
Use a COMPLETELY DIFFERENT real-life example.
This attempt strategy: {strategy}
"""

    user_message = f"""
Topic to teach: {topic}

NCERT content for accuracy:
{context[:1200]}
{attempt_note}
Write the script now. 
IMPORTANT: Follow the example style EXACTLY — same Hinglish mix.
Do NOT write in full English. Mix Hindi words naturally like the examples.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=450,
        temperature=0.8,
        messages=[
            {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ]
    )

    full_script = response.choices[0].message.content.strip()

    # Clean emotion tags for TTS
    clean_text = re.sub(
        r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]',
        '', full_script
    )
    clean_text = re.sub(r'\[.*?\]', '', clean_text)
    clean_text = re.sub(r'\n+', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    emotions   = re.findall(
        r'\[(SMILE|NOD|CURIOUS|RAISE_EYEBROW|EXCITED|PAUSE)\]',
        full_script
    )
    word_count = len(clean_text.split())

    return {
        "full_script": full_script,
        "clean_text":  clean_text,
        "emotions":    emotions,
        "word_count":  word_count
    }


if __name__ == "__main__":
    from rag import get_context

    print("=" * 60)
    print("Testing Improved Hinglish Script")
    print("=" * 60)

    topics = ["Osmosis", "Photosynthesis", "Reflection of Light"]

    for topic in topics:
        print(f"\n{'─'*60}")
        print(f"Topic: {topic}")
        print(f"{'─'*60}")
        context = get_context(topic)
        result  = generate_script(topic, context, attempt=1)
        print(f"\nFULL SCRIPT:\n{result['full_script']}")
        print(f"\nWORDS: {result['word_count']} | EMOTIONS: {result['emotions']}")
        print(f"\nCLEAN TEXT (to TTS):\n{result['clean_text']}")

        print(f"\n--- Attempt 2 ---")
        r2 = generate_script(topic, context, attempt=2)
        print(r2['full_script'])

    print("\n" + "=" * 60)
    print("✓ Done!")
    print("=" * 60)