import json
import chromadb
from sentence_transformers import SentenceTransformer
import warnings

# Suppress a common warning from sentence_transformers
warnings.filterwarnings("ignore", category=FutureWarning, module="sentence_transformers.SentenceTransformer")

# --- Configuration ---
CHUNKS_FILE = "gem5_docs_chunks2.json"
DB_PATH = "gem5_chroma_db_v3"
COLLECTION_NAME = "gem5_documentation_v3"
MODEL_NAME = "all-MiniLM-L6-v2" # A good, fast, and popular model

def main():
    # 1. Load the processed chunks
    print(f"Loading processed chunks from {CHUNKS_FILE}...")
    try:
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {CHUNKS_FILE} was not found.")
        print("Please run the scraper.py and chunker.py scripts first.")
        return

    # 2. Initialize the embedding model
    print(f"Initializing sentence-transformer model: {MODEL_NAME}...")
    # This will download the model from the internet on the first run
    model = SentenceTransformer(MODEL_NAME)
    print("✅ Model loaded successfully.")

    # 3. Initialize the ChromaDB client
    # This will create a directory on your disk to store the database
    print(f"Initializing ChromaDB client at: {DB_PATH}...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # 4. Create or get the collection
    print(f"Getting or creating ChromaDB collection: {COLLECTION_NAME}...")
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    print("✅ Collection ready.")

    # 5. Prepare data for ChromaDB
    # We need to create lists of IDs, the documents (text), and metadatas
    print("Preparing data for embedding and storage...")
    
    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    documents = [chunk['text'] for chunk in all_chunks]
    metadatas = [chunk['metadata'] for chunk in all_chunks]
    
    # 6. Generate embeddings and add to the collection
    # The model.encode() function can take a while, especially the first time.
    # The library provides a progress bar by default which is very helpful.
    print(f"Generating embeddings for {len(documents)} chunks... (This may take a while)")
    
    embeddings = model.encode(documents, show_progress_bar=True)
    
    print("Adding data to the collection in batches...")
    
    # Add data to ChromaDB in batches to be efficient
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end_index = i + batch_size
        print(f"  - Adding batch {i//batch_size + 1}...")
        
        collection.add(
            ids=ids[i:end_index],
            embeddings=embeddings[i:end_index].tolist(), # ChromaDB expects a list
            documents=documents[i:end_index],
            metadatas=metadatas[i:end_index]
        )

    print("\n🎉 Success! All chunks have been embedded and stored in ChromaDB.")
    print(f"Total documents in collection: {collection.count()}")

if __name__ == "__main__":
    main()