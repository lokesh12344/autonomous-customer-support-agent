"""RAG (Retrieval-Augmented Generation) tools for the ReAct agent."""

from typing import List, Dict, Any
from langchain.tools import tool

from app.services.vectorstore import get_vectorstore


@tool
def semantic_search_faq(query: str, n_results: int = 3) -> str:
    """
    Perform semantic search on the FAQ knowledge base.
    
    Args:
        query: The search query from the user
        n_results: Number of relevant FAQs to return
        
    Returns:
        String containing relevant FAQ answers
    """
    try:
        vectorstore = get_vectorstore()
        results = vectorstore.query(query, n_results=n_results)
        
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            return "No relevant FAQ entries found. Please contact support for assistance."
        
        # Format the results
        formatted_results = []
        for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0]), 1):
            # Lower distance = more similar
            relevance = "High" if distance < 0.5 else "Medium" if distance < 1.0 else "Low"
            formatted_results.append(f"{i}. [Relevance: {relevance}]\n{doc}\n")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error searching FAQ: {str(e)}"


@tool
def search_product_documentation(query: str, n_results: int = 2) -> str:
    """
    Search product documentation using semantic search.
    
    Args:
        query: The documentation query
        n_results: Number of relevant docs to return
        
    Returns:
        Relevant documentation snippets
    """
    try:
        vectorstore = get_vectorstore()
        # Search with metadata filter for documentation type
        results = vectorstore.query(query, n_results=n_results)
        
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            return "No relevant documentation found. Please visit our documentation portal or contact support."
        
        # Format the results
        formatted_results = []
        for i, doc in enumerate(results["documents"][0], 1):
            formatted_results.append(f"Documentation #{i}:\n{doc}\n")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error searching documentation: {str(e)}"


# Export tools as a list for easy registration
rag_tools = [
    semantic_search_faq,
    search_product_documentation,
]
