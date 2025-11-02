import chromadb
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- 1. Connect to your ChromaDB server ---
client = chromadb.HttpClient(host='localhost', port=8000)

  # --- 2. Create or get a "collection" (like a database table) ---
collection_name = "knowledge_base"
try:
    collection = client.get_collection(name=collection_name)
    print(f"Using existing collection: {collection_name}")
except:
    collection = client.create_collection(name=collection_name)
    print(f"Created new collection: {collection_name}")

# --- 3. Load Documents ---
data_folder = "my_documents"
all_docs = []
for filename in os.listdir(data_folder):
    filepath = os.path.join(data_folder, filename)
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(filepath)
        all_docs.extend(loader.load())
    elif filename.endswith(".txt"):
        loader = TextLoader(filepath)
        all_docs.extend(loader.load())
print(f"Loaded {len(all_docs)} document pages.")

# --- 4. Split Documents into Chunks ---
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(all_docs)
print(f"Split into {len(splits)} text chunks.")

# --- 5. Add to ChromaDB ---
# We will add them in batches of 100
for i in range(0, len(splits), 100):
    batch = splits[i:i+100]

    ids = [f"chunk_{i+j}" for j in range(len(batch))]
    documents = [doc.page_content for doc in batch]
    metadatas = [doc.metadata for doc in batch]

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Added batch {int(i/100) + 1} to ChromaDB.")

print("✅ Ingestion complete!")