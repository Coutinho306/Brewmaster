from core.config import CHROMA_PATH, COLLECTION, RAG_MODEL
from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

URLS = [
    "https://raw.githubusercontent.com/Coutinho306/Bees-Brewery-Pipeline/main/README.md",
    "https://raw.githubusercontent.com/Coutinho306/Bees-Brewery-Pipeline/main/MONITORING.md",
]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    add_start_index=True,
)

embeddings = OpenAIEmbeddings(model='text-embedding-3-small')

_existing = Chroma(persist_directory=CHROMA_PATH, collection_name=COLLECTION, embedding_function=embeddings)

if _existing._collection.count() > 0:
    vector_store = _existing
    print(f'Loaded existing collection — {vector_store._collection.count()} chunks')
else:
    # Only fetch from GitHub when the collection doesn't exist yet
    loader = WebBaseLoader(URLS)
    chunks = splitter.split_documents(loader.load())
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name=COLLECTION,
    )
    print(f'Built new collection — {vector_store._collection.count()} chunks')

@tool
def search_docs(query: str) -> str:
    """Search Bees-Brewery-Pipeline documentation reference."""
    results = vector_store.similarity_search(query, k=3)
    return '\n\n---\n\n'.join(
        f"[{r.metadata['source']}]\n{r.page_content}" for r in results
    )

rag_agent = create_agent(
    model=RAG_MODEL,
    tools=[search_docs],
    system_prompt="You are a helpful assistant that answers questions about the Bees-Brewery-Pipeline project. Always search the docs before answering.",
)

