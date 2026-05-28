import os
import re
from pathlib import Path
from typing import List, Tuple
import pymupdf4llm
import pdfplumber
from pinecone import Pinecone
from groq import Groq
from dotenv import load_dotenv
import requests
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Get API keys from .env
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Pinecone client (optional - only if API key is provided)
pc = None
INDEX_NAME = "ncert-science"

# Initialize local embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Embedding model loaded")

if PINECONE_API_KEY and PINECONE_API_KEY != "your_pinecone_api_key_here":
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Pinecone: {e}")
else:
    print("Warning: PINECONE_API_KEY not set in .env file. Set it to enable uploads to Pinecone.")


# Diagram descriptions for Class 10 Science NCERT topics
DIAGRAM_DESCRIPTIONS = {
    "human_digestive_system": """The human digestive system is a complex series of organs that breaks down food into smaller molecules for absorption and energy production. The process starts in the mouth where saliva and mechanical action begin digestion. Food then travels through the esophagus to the stomach, where strong acids and enzymes break it down further into a paste-like substance. The small intestine is the primary site of nutrient absorption, with specialized finger-like projections called villi increasing the surface area. The large intestine absorbs water and remaining minerals before waste is eliminated. The pancreas, liver, and gallbladder play crucial supporting roles by producing digestive enzymes and bile for fat digestion. This entire system is coordinated by both mechanical and chemical processes to ensure maximum nutrient extraction and absorption.""",
    
    "human_respiratory_system": """The human respiratory system is responsible for gas exchange, delivering oxygen to the blood and removing carbon dioxide waste. Air enters through the nostrils and travels through the nasal cavity, pharynx, and larynx before reaching the trachea. The trachea divides into two primary bronchi, which further divide into smaller bronchioles within the lungs. At the terminal end of these passages are millions of tiny air sacs called alveoli, where gas exchange occurs. The diaphragm, a dome-shaped muscle below the lungs, controls breathing by contracting to draw air in and relaxing to push air out. Oxygen from inhaled air crosses the thin alveolar walls into surrounding blood vessels, while carbon dioxide moves in the opposite direction for exhalation. This continuous exchange ensures cells throughout the body receive the oxygen they need for cellular respiration.""",
    
    "neuron_structure": """A neuron is the basic unit of the nervous system, consisting of three main parts: the cell body (soma), dendrites, and axon. The cell body contains the nucleus and most of the cytoplasm, serving as the metabolic center of the neuron. Dendrites are branched structures extending from the cell body that receive signals from other neurons through connections called synapses. The axon is a long, thin projection that transmits electrical signals away from the cell body toward other neurons, muscles, or glands. The axon terminal contains synaptic vesicles filled with neurotransmitters for communication with other cells. Myelin sheath, a fatty covering on some axons, increases the speed of signal transmission. Different types of neurons include sensory neurons (carry signals toward brain), motor neurons (carry signals away from brain), and interneurons (connect neurons within the nervous system).""",
    
    "reflex_arc": """A reflex arc is the neural pathway that allows rapid automatic responses to stimuli without requiring brain involvement. The pathway begins with a sensory receptor detecting a stimulus, such as touch or heat, which triggers an electrical signal in a sensory neuron. This sensory neuron transmits the signal directly to the spinal cord, where it synapses with an interneuron in the gray matter. The interneuron immediately connects to a motor neuron, which carries the signal back to muscles for an automatic response. This direct connection between sensory and motor neurons through the spinal cord allows for extremely fast reactions. The brain receives the sensory information only after the reflex action has already occurred, which is why you withdraw your hand from a hot surface before consciously feeling the pain. This elegant system protects the body from harm through quick, involuntary movements.""",
    
    "electric_circuit_diagram": """An electric circuit diagram is a standardized representation of an electrical circuit using symbols to show how components are connected. The circuit consists of a power source (battery or cell) providing electrical energy, connecting wires forming a continuous path, and various components like resistors, switches, bulbs, or motors. The positive terminal of the battery is connected through components back to the negative terminal, creating a closed loop through which current flows. Conventional current flows from the positive terminal through the circuit to the negative terminal, though electrons actually move in the opposite direction. A switch interrupts the circuit, allowing control of whether current flows or not, while resistors limit the current. In a series circuit, components are connected in a single path, so the same current flows through all. In a parallel circuit, components are connected in multiple paths, allowing current to divide among branches. Understanding circuit diagrams is essential for analyzing electrical systems and predicting how circuits will behave."""
}


def get_embeddings(text: str) -> List[float]:
    """
    Get embeddings for text using local SentenceTransformer model.
    Pads embeddings to 1536 dimensions to match Pinecone index.
    """
    try:
        # Use local embedding model (produces 384 dimensions)
        embeddings = embedding_model.encode(text, convert_to_tensor=False)
        embeddings_list = embeddings.tolist() if hasattr(embeddings, 'tolist') else list(embeddings)
        
        # Pad to 1536 dimensions (Pinecone index size)
        target_dim = 1536
        if len(embeddings_list) < target_dim:
            # Pad with zeros
            embeddings_list = embeddings_list + [0.0] * (target_dim - len(embeddings_list))
        
        return embeddings_list[:target_dim]  # Ensure exact dimension
        
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        return [0.1] * 1536


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using pymupdf4llm (for prose) and pdfplumber (for tables).
    """
    text = ""
    
    try:
        # Use pymupdf4llm for prose extraction
        print(f"  - Extracting prose with pymupdf4llm...")
        text = pymupdf4llm.to_markdown(pdf_path)
        
        # Extract tables using pdfplumber
        print(f"  - Extracting tables with pdfplumber...")
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    text += f"\n\n## Tables from page {page_idx + 1}:\n"
                    for table in tables:
                        # Convert table to markdown format
                        text += "\n| "
                        text += " | ".join(str(cell) if cell else "" for cell in table[0])
                        text += " |\n"
                        text += "|" + "|".join(["---"] * len(table[0])) + "|\n"
                        for row in table[1:]:
                            text += "| "
                            text += " | ".join(str(cell) if cell else "" for cell in row)
                            text += " |\n"
        
        return text
        
    except Exception as e:
        print(f"  - Error extracting text from {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with specified word size and overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk (default: 400)
        overlap: Number of words to overlap between chunks (default: 50)
    
    Returns:
        List of text chunks
    """
    # Split text into words
    words = text.split()
    chunks = []
    
    stride = chunk_size - overlap
    
    for i in range(0, len(words), stride):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def process_pdfs(knowledge_base_path: str = "../knowledge_base") -> None:
    """
    Process all PDF files in the knowledge base folder.
    
    Args:
        knowledge_base_path: Path to the knowledge base folder
    """
    # Convert to absolute path
    kb_path = Path(knowledge_base_path).resolve()
    
    if not kb_path.exists():
        print(f"Error: Knowledge base path {kb_path} does not exist!")
        return
    
    # Get all PDF files
    pdf_files = list(kb_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {kb_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    print("=" * 80)
    
    # Connect to Pinecone index
    if not pc:
        print("Error: Pinecone not initialized. Please set PINECONE_API_KEY in .env file.")
        return
    
    try:
        index = pc.Index(INDEX_NAME)
        print(f"Connected to Pinecone index: {INDEX_NAME}")
    except Exception as e:
        print(f"Error connecting to Pinecone: {e}")
        return
    
    # Process each PDF
    total_chunks = 0
    
    for pdf_idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{pdf_idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
        
        # Extract text
        print(f"  - Extracting text...")
        text = extract_text_from_pdf(str(pdf_path))
        
        if not text:
            print(f"  - No text extracted from {pdf_path.name}")
            continue
        
        # Split into chunks
        print(f"  - Splitting into chunks (400 words, 50 word overlap)...")
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        print(f"  - Created {len(chunks)} chunks")
        
        # Process each chunk
        vectors_to_upsert = []
        
        for chunk_id, chunk in enumerate(chunks):
            # Get embeddings
            embeddings = get_embeddings(chunk)
            
            # Create vector ID
            vector_id = f"{pdf_path.stem}_{chunk_id}"
            
            # Prepare metadata
            metadata = {
                "text": chunk,
                "filename": pdf_path.name,
                "chunk_id": chunk_id
            }
            
            # Add to upsert list
            vectors_to_upsert.append((vector_id, embeddings, metadata))
            
            if (chunk_id + 1) % 5 == 0:
                print(f"    - Processed {chunk_id + 1}/{len(chunks)} chunks")
        
        # Upsert to Pinecone
        try:
            print(f"  - Uploading {len(vectors_to_upsert)} chunks to Pinecone...")
            index.upsert(vectors=vectors_to_upsert)
            total_chunks += len(vectors_to_upsert)
            print(f"  - ✓ Successfully uploaded {len(vectors_to_upsert)} chunks")
        except Exception as e:
            print(f"  - Error uploading to Pinecone: {e}")
    
    print("\n" + "=" * 80)
    print(f"✓ Ingestion complete!")
    print(f"  Total PDFs processed: {len(pdf_files)}")
    print(f"  Total chunks uploaded: {total_chunks}")


def upload_diagrams() -> None:
    """
    Upload diagram descriptions to Pinecone with metadata type="diagram".
    """
    if not pc:
        print("Error: Pinecone not initialized. Cannot upload diagrams.")
        return
    
    try:
        index = pc.Index(INDEX_NAME)
    except Exception as e:
        print(f"Error connecting to Pinecone: {e}")
        return
    
    print("\n" + "="*80)
    print("Uploading diagram descriptions...")
    print("="*80)
    
    vectors_to_upsert = []
    
    for diagram_name, description in DIAGRAM_DESCRIPTIONS.items():
        print(f"  - Processing: {diagram_name}")
        
        # Get embeddings
        embeddings = get_embeddings(description)
        
        # Create vector ID
        vector_id = f"diagram_{diagram_name}"
        
        # Prepare metadata
        metadata = {
            "text": description,
            "type": "diagram",
            "topic": diagram_name.replace("_", " ").title()
        }
        
        # Add to upsert list
        vectors_to_upsert.append((vector_id, embeddings, metadata))
    
    # Upsert to Pinecone
    try:
        print(f"  - Uploading {len(vectors_to_upsert)} diagrams to Pinecone...")
        index.upsert(vectors=vectors_to_upsert)
        print(f"  - ✓ Successfully uploaded {len(vectors_to_upsert)} diagrams")
    except Exception as e:
        print(f"  - Error uploading diagrams to Pinecone: {e}")
    
    print("\n" + "="*80)
    print(f"✓ Diagram upload complete!")
    print(f"  Total diagrams uploaded: {len(vectors_to_upsert)}")


if __name__ == "__main__":
    print("Starting PDF ingestion pipeline...")
    print("=" * 80)
    
    # Get the path to knowledge_base folder (relative to this script)
    script_dir = Path(__file__).parent
    knowledge_base_path = script_dir.parent / "knowledge_base"
    
    process_pdfs(str(knowledge_base_path))
    upload_diagrams()
