import os
import warnings
import logging
from dotenv import load_dotenv
from groq import Groq
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Suppress all warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

# Initialize Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Pinecone
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pinecone_client.Index(
    os.getenv("PINECONE_INDEX_NAME", "ncert-science")
)

# Load embedding model — same model used in ingest.py
# MUST be the same model, outputs 384 dimensions
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✓ Embedding model ready")


def normalize_query(raw_input: str) -> str:
    """
    Converts messy student input into a clean NCERT topic name using Groq.

    Examples:
        "osmosis kya h bro"         → "Osmosis"
        "photosynthesis explain kr" → "Photosynthesis"
        "light ka reflection"       → "Reflection of Light"
        "respiration class 10"      → "Respiration"
    """
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=30,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a topic extractor for NCERT Class 10 Science. "
                    "Given any student question in Hindi, English, or Hinglish, "
                    "return ONLY the clean English topic name. "
                    "Nothing else. No punctuation. No explanation. Just the topic. "
                    "Examples:\n"
                    "osmosis kya h bro → Osmosis\n"
                    "photosynthesis explain kr → Photosynthesis\n"
                    "light ka reflection → Reflection of Light\n"
                    "current electricity → Electric Current\n"
                    "nervous system explain → Nervous System\n"
                    "acid base reaction → Acids Bases and Salts"
                )
            },
            {
                "role": "user",
                "content": raw_input
            }
        ]
    )
    return response.choices[0].message.content.strip()


def get_context(topic: str) -> str:
    """
    Embeds the topic and retrieves top 5 matching NCERT chunks from Pinecone.

    Args:
        topic: Clean topic name (e.g. "Osmosis", "Photosynthesis")

    Returns:
        Combined text of top 5 matching chunks as one string
    """
    # Generate embedding — 384 dimensions, same as ingest.py
    topic_embedding = embedding_model.encode(
        topic, convert_to_tensor=False
    ).tolist()

    # Query Pinecone for top 5 most relevant chunks
    results = pinecone_index.query(
        vector=topic_embedding,
        top_k=5,
        include_metadata=True
    )

    # Combine all matching chunks
    chunks = []
    for match in results.get("matches", []):
        text = match.get("metadata", {}).get("text", "")
        if text:
            chunks.append(text)

    combined = "\n\n".join(chunks)
    return combined.strip()


def get_context_with_scores(topic: str) -> list:
    """
    Same as get_context but returns list of (text, score) tuples.
    Useful for debugging match quality.
    """
    topic_embedding = embedding_model.encode(
        topic, convert_to_tensor=False
    ).tolist()

    results = pinecone_index.query(
        vector=topic_embedding,
        top_k=5,
        include_metadata=True
    )

    output = []
    for match in results.get("matches", []):
        text = match.get("metadata", {}).get("text", "")
        score = match.get("score", 0)
        if text:
            output.append((text, round(score, 4)))

    return output


if __name__ == "__main__":
    print("=" * 60)
    print("Testing RAG Pipeline")
    print("=" * 60)

    # ── Test 1: normalize_query ──────────────────────────────
    print("\n[TEST 1] normalize_query()")
    print("-" * 60)

    test_inputs = [
        "osmosis kya h bro",
        "photosynthesis explain kr",
        "respiration biology class 10",
        "Newton ka pehla law",
        "acid aur base mein difference",
    ]

    for raw in test_inputs:
        try:
            result = normalize_query(raw)
            print(f"  '{raw}'")
            print(f"   → '{result}'\n")
        except Exception as e:
            print(f"  '{raw}'")
            print(f"   → ERROR: {e}\n")

    # ── Test 2: get_context ──────────────────────────────────
    print("\n[TEST 2] get_context() with match scores")
    print("-" * 60)

    test_topics = [
        "Osmosis",
        "Photosynthesis",
        "Electric Current",
        "Nervous System",
    ]

    for topic in test_topics:
        print(f"\nTopic: '{topic}'")
        try:
            results = get_context_with_scores(topic)
            if results:
                print(f"  Found {len(results)} matches:")
                for i, (text, score) in enumerate(results, 1):
                    print(f"  [{i}] Score: {score} | Preview: {text[:120].strip()}...")
            else:
                print("  No matches found — check if ingest.py was run successfully")
        except Exception as e:
            print(f"  ERROR: {e}")

    # ── Test 3: Full pipeline ────────────────────────────────
    print("\n[TEST 3] Full pipeline — messy input to context")
    print("-" * 60)

    messy_input = "osmosis kya h bro"
    print(f"Student types: '{messy_input}'")

    try:
        clean = normalize_query(messy_input)
        print(f"After normalize: '{clean}'")

        context = get_context(clean)
        print(f"Context retrieved: {len(context)} characters")
        print(f"Preview: {context[:300]}...")
        print("\n✓ Full pipeline working correctly!")
    except Exception as e:
        print(f"ERROR in pipeline: {e}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)