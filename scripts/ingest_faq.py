#!/usr/bin/env python3
"""
Ingest FAQ documents into Chroma vector store.
"""

from pathlib import Path
import re

from app.services.vectorstore import get_vectorstore


def load_faq_markdown(file_path: str) -> list:
    """
    Load and parse FAQ markdown file into individual Q&A pairs.
    
    Args:
        file_path: Path to the FAQ markdown file
        
    Returns:
        List of tuples (question, answer, category)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by ## headers (categories)
    sections = re.split(r'^## (.+)$', content, flags=re.MULTILINE)
    
    qa_pairs = []
    current_category = "General"
    
    for i in range(1, len(sections), 2):
        if i < len(sections):
            current_category = sections[i].strip()
            section_content = sections[i + 1] if i + 1 < len(sections) else ""
            
            # Split by ### Q: (questions)
            qa_items = re.split(r'###\s+Q:\s+(.+?)\n', section_content)
            
            for j in range(1, len(qa_items), 2):
                if j < len(qa_items):
                    question = qa_items[j].strip()
                    answer_block = qa_items[j + 1] if j + 1 < len(qa_items) else ""
                    
                    # Extract answer (everything after A:)
                    answer_match = re.search(r'A:\s+(.+?)(?=###|$)', answer_block, re.DOTALL)
                    if answer_match:
                        answer = answer_match.group(1).strip()
                        qa_pairs.append((question, answer, current_category))
    
    return qa_pairs


def ingest_faqs(faq_file: str = "data/faq.md"):
    """
    Ingest FAQ documents into the vector store.
    
    Args:
        faq_file: Path to FAQ markdown file
    """
    print("📚 Loading FAQ documents...")
    
    # Load FAQs
    qa_pairs = load_faq_markdown(faq_file)
    print(f"  ✅ Loaded {len(qa_pairs)} Q&A pairs")
    
    # Get vector store
    vectorstore = get_vectorstore()
    collection = vectorstore.get_or_create_collection()
    
    print("\n🔄 Ingesting into Chroma...")
    
    # Prepare documents
    documents = []
    metadatas = []
    ids = []
    
    for i, (question, answer, category) in enumerate(qa_pairs, 1):
        # Combine question and answer for better context
        doc_text = f"Q: {question}\nA: {answer}"
        documents.append(doc_text)
        metadatas.append({
            "category": category,
            "question": question,
            "type": "faq"
        })
        ids.append(f"faq_{i}")
    
    # Add to collection
    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"  ✅ Successfully ingested {len(documents)} documents")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return
    
    # Show statistics
    print("\n📊 Vector Store Statistics:")
    count = collection.count()
    print(f"  📄 Total documents: {count}")
    
    # Show categories
    categories = set(m["category"] for m in metadatas)
    print(f"  🏷️  Categories: {', '.join(sorted(categories))}")
    
    print("\n✅ FAQ ingestion completed!")
    print("\n💡 Test queries:")
    print("  - How do I get a refund?")
    print("  - What is your shipping policy?")
    print("  - How do I reset my password?")


def test_search(query: str, n_results: int = 3):
    """
    Test semantic search on ingested FAQs.
    
    Args:
        query: Search query
        n_results: Number of results to return
    """
    print(f"\n🔍 Testing search: '{query}'")
    print("=" * 60)
    
    vectorstore = get_vectorstore()
    results = vectorstore.query(query, n_results=n_results)
    
    if results and results.get("documents") and len(results["documents"][0]) > 0:
        for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0]), 1):
            print(f"\nResult {i} (distance: {distance:.3f}):")
            print(doc[:200] + "..." if len(doc) > 200 else doc)
    else:
        print("No results found.")


def main():
    """Main ingestion function."""
    print("🌱 Starting FAQ Ingestion...\n")
    
    # Check if FAQ file exists
    faq_path = Path("data/faq.md")
    if not faq_path.exists():
        print(f"❌ FAQ file not found: {faq_path}")
        print("Please create data/faq.md with FAQ content.")
        return
    
    # Ingest FAQs
    ingest_faqs(str(faq_path))
    
    # Run test searches
    print("\n" + "=" * 60)
    print("Running test searches...")
    print("=" * 60)
    
    test_queries = [
        "How do I get a refund?",
        "What payment methods do you accept?",
        "How long does shipping take?"
    ]
    
    for query in test_queries:
        test_search(query, n_results=2)


if __name__ == "__main__":
    main()
