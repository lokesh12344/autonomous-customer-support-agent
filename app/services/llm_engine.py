"""LLM engine wrapper for Ollama local models."""

from typing import Optional
from langchain_ollama import ChatOllama

from app.utils.config import settings


class LLMEngine:
    """Wrapper class for interacting with Ollama-hosted local LLMs."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the LLM engine.
        
        Args:
            model_name: Name of the Ollama model (e.g., 'llama3', 'mistral')
        """
        self.model_name = model_name or settings.model_name
        self.base_url = settings.ollama_base_url
        self._llm = None
    
    def get_llm(self):
        """
        Get or create a ChatOllama instance.
        
        Returns:
            ChatOllama: LangChain-compatible Ollama chat model
        """
        if self._llm is None:
            self._llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.7,
            )
        return self._llm
    
    def invoke(self, prompt: str) -> str:
        """
        Simple invoke method for direct LLM calls.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            str: LLM response
        """
        llm = self.get_llm()
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)


# Global LLM engine instance
def get_llm(model_name: Optional[str] = None):
    """
    Factory function to get an LLM instance.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        ChatOllama: LangChain-compatible Ollama model
    """
    engine = LLMEngine(model_name=model_name)
    return engine.get_llm()


if __name__ == "__main__":
    # Test the LLM engine
    print("🧠 Testing LLM Engine...")
    engine = LLMEngine()
    print(f"Model: {engine.model_name}")
    print(f"Base URL: {engine.base_url}")
