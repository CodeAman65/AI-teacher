import os
import re
import warnings
import logging
from pathlib import Path
from typing import List
import pymupdf4llm
import pdfplumber
from pinecone import Pinecone
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ncert-science")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Load embedding model — outputs REAL 384 dimensions, NO padding
print("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
print("✓ Embedding model loaded (384 dimensions)")

# ─────────────────────────────────────────────
# DIAGRAM DESCRIPTIONS — manually written for
# topics that don't extract well from PDFs
# ─────────────────────────────────────────────
DIAGRAM_DESCRIPTIONS = {
    "human_digestive_system": """The human digestive system breaks down food into smaller molecules.
    Mouth: saliva and teeth start digestion mechanically and chemically.
    Oesophagus: muscular tube that pushes food down using peristalsis.
    Stomach: HCl acid and pepsin enzyme break down proteins. Food becomes chyme.
    Small intestine: bile from liver breaks fats. Pancreatic juice digests all nutrients.
    Villi on inner walls absorb nutrients directly into the blood.
    Large intestine: absorbs water. Remaining waste becomes faeces.
    Anus: faeces expelled. Key point: digestion is both physical and chemical breakdown.""",

    "human_respiratory_system": """The human respiratory system exchanges oxygen and carbon dioxide.
    Air enters through nostrils, passes through nasal cavity, pharynx, larynx, trachea.
    Trachea splits into two bronchi going into each lung.
    Bronchi split further into bronchioles ending in tiny air sacs called alveoli.
    Alveoli: thin walls, rich blood supply — oxygen enters blood, CO2 leaves blood here.
    Diaphragm contracts to breathe in (inhale), relaxes to breathe out (exhale).
    Ribcage also moves up and out during inhalation to increase lung volume.
    Breathing rate increases during exercise because cells need more oxygen.""",

    "neuron_structure": """A neuron is the basic working unit of the nervous system.
    Cell body (soma): contains nucleus, controls all neuron functions.
    Dendrites: short branched extensions that receive signals from other neurons.
    Axon: long single fiber that carries signals AWAY from cell body.
    Myelin sheath: fatty covering on axon that speeds up signal transmission.
    Axon terminals: end of axon, releases neurotransmitters to next neuron.
    Synapse: tiny gap between two neurons where signals are passed chemically.
    Types: sensory neurons carry signals to brain, motor neurons carry from brain to muscles.""",

    "reflex_arc": """A reflex arc is the pathway of a reflex action — automatic response without thinking.
    Step 1: Receptor detects stimulus (e.g. touching hot object).
    Step 2: Sensory neuron carries signal TO spinal cord.
    Step 3: Relay neuron in spinal cord processes signal instantly.
    Step 4: Motor neuron carries signal FROM spinal cord to muscle.
    Step 5: Muscle contracts — hand pulls away immediately.
    Brain receives information AFTER the action has already happened.
    This protects the body from harm very quickly without waiting for brain.
    Example: knee-jerk reaction, blinking, pulling hand from flame.""",

    "electric_circuit": """An electric circuit is a closed path through which electric current flows.
    Components: battery (source of EMF), wires (conductors), bulb/resistor (load), switch.
    Current flows from positive terminal of battery through circuit to negative terminal.
    Switch open = circuit broken = no current flows = bulb off.
    Switch closed = complete circuit = current flows = bulb lights up.
    Series circuit: components connected one after another. Same current through all.
    If one component fails in series, entire circuit stops working.
    Parallel circuit: components connected in separate branches. Voltage same across all.
    If one component fails in parallel, others continue working.
    Ammeter measures current (connected in series). Voltmeter measures voltage (in parallel).""",

    "plant_cell_vs_animal_cell": """Plant cell and animal cell are both eukaryotic but have key differences.
    Plant cell has: cell wall (rigid, made of cellulose), chloroplasts (for photosynthesis),
    large central vacuole (stores water and maintains turgor pressure).
    Animal cell has: no cell wall, no chloroplasts, small vacuoles (many, not central).
    Both have: nucleus, mitochondria, cell membrane, ribosomes, endoplasmic reticulum, Golgi apparatus.
    Chloroplasts contain chlorophyll — the green pigment that captures sunlight for photosynthesis.
    Cell wall gives plant cells a fixed shape. Animal cells can change shape.""",

    "photosynthesis": """Photosynthesis is the process by which plants make food using sunlight.
    Equation: 6CO2 + 6H2O + sunlight energy → C6H12O6 (glucose) + 6O2
    Occurs in: chloroplasts, specifically in the thylakoid membranes and stroma.
    Chlorophyll absorbs sunlight (mainly red and blue wavelengths).
    Two stages: Light reactions (in thylakoids) — split water, release oxygen, produce ATP.
    Dark reactions / Calvin cycle (in stroma) — use ATP to convert CO2 into glucose.
    Inputs: carbon dioxide (from air through stomata), water (from roots), sunlight.
    Output: glucose (stored as starch) and oxygen (released through stomata).
    Factors affecting rate: light intensity, CO2 concentration, temperature.""",

    "human_heart": """The human heart is a muscular organ that pumps blood throughout the body.
    Four chambers: right atrium, right ventricle, left atrium, left ventricle.
    Right side: receives deoxygenated blood from body, sends it to lungs.
    Left side: receives oxygenated blood from lungs, pumps it to entire body.
    Valves prevent backflow of blood between chambers.
    Pulmonary circulation: right ventricle → lungs → left atrium (blood gets oxygen).
    Systemic circulation: left ventricle → body → right atrium (blood gives oxygen to cells).
    Heartbeat: atria contract first, then ventricles. One complete cycle = one heartbeat.
    Average heart rate: 70-80 beats per minute at rest."""
}


def get_embedding(text: str) -> List[float]:
    """Generate 384-dimensional embedding — NO padding, real dimensions."""
    embedding = embedding_model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text using pymupdf4llm for prose and pdfplumber for tables."""
    text = ""

    # Prose extraction
    try:
        print(f"  - Extracting prose...")
        text = pymupdf4llm.to_markdown(pdf_path)
    except Exception as e:
        print(f"  - pymupdf4llm error: {e}")

    # Table extraction
    try:
        print(f"  - Extracting tables...")
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    text += f"\n\n## Tables from page {page_idx + 1}:\n"
                    for table in tables:
                        if not table or not table[0]:
                            continue
                        text += "\n| " + " | ".join(
                            str(cell) if cell else "" for cell in table[0]
                        ) + " |\n"
                        text += "|" + "|".join(["---"] * len(table[0])) + "|\n"
                        for row in table[1:]:
                            text += "| " + " | ".join(
                                str(cell) if cell else "" for cell in row
                            ) + " |\n"
    except Exception as e:
        print(f"  - pdfplumber error: {e}")

    return text


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping word chunks."""
    words = text.split()
    chunks = []
    stride = chunk_size - overlap
    for i in range(0, len(words), stride):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def process_pdfs(knowledge_base_path: str) -> None:
    """Process all PDFs in knowledge_base folder and upload to Pinecone."""
    kb_path = Path(knowledge_base_path).resolve()

    if not kb_path.exists():
        print(f"Error: Path {kb_path} does not exist!")
        return

    pdf_files = list(kb_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {kb_path}")
        return

    print(f"Found {len(pdf_files)} PDF files")
    print("=" * 60)

    total_chunks = 0

    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{pdf_idx}/{len(pdf_files)}] Processing: {pdf_path.name}")

        text = extract_text_from_pdf(str(pdf_path))
        if not text.strip():
            print(f"  - No text extracted, skipping.")
            continue

        chunks = chunk_text(text)
        print(f"  - {len(chunks)} chunks created")

        vectors = []
        for i, chunk in enumerate(chunks):
            vec_id = f"{pdf_path.stem}_{i}"
            embedding = get_embedding(chunk)
            metadata = {
                "text": chunk,
                "filename": pdf_path.name,
                "chunk_id": i
            }
            vectors.append((vec_id, embedding, metadata))

            # Upsert in batches of 50
            if len(vectors) == 50:
                index.upsert(vectors=vectors)
                total_chunks += 50
                print(f"    - Uploaded {total_chunks} chunks so far...")
                vectors = []

        # Upload remaining
        if vectors:
            index.upsert(vectors=vectors)
            total_chunks += len(vectors)

        print(f"  ✓ Done: {pdf_path.name}")

    print("\n" + "=" * 60)
    print(f"✓ All PDFs processed. Total chunks uploaded: {total_chunks}")


def upload_diagrams() -> None:
    """Upload manually written diagram descriptions to Pinecone."""
    print("\n" + "=" * 60)
    print("Uploading diagram descriptions...")

    vectors = []
    for name, description in DIAGRAM_DESCRIPTIONS.items():
        embedding = get_embedding(description)
        metadata = {
            "text": description,
            "type": "diagram",
            "topic": name.replace("_", " ").title(),
            "filename": "diagrams"
        }
        vectors.append((f"diagram_{name}", embedding, metadata))

    index.upsert(vectors=vectors)
    print(f"✓ Uploaded {len(vectors)} diagram descriptions")


if __name__ == "__main__":
    print("=" * 60)
    print("NCERT Science Ingestion Pipeline")
    print("=" * 60)

    script_dir = Path(__file__).parent
    kb_path = script_dir.parent / "knowledge_base"

    process_pdfs(str(kb_path))
    upload_diagrams()

    print("\n" + "=" * 60)
    print("✓ Ingestion complete! Your Pinecone index is ready.")
    print("=" * 60)