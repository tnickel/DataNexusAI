import os
import urllib.request
import json
from typing import List, Dict, Any


class LocalQwenLLMClient:
    """
    Inference Client for Local Qwen2.5 Models via Ollama / vLLM.
    Generates DSGVO-compliant responses without external cloud dependencies.
    """

    def __init__(
        self,
        model_name: str = None,
        ollama_base_url: str = None
    ):
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or self._detect_best_installed_model()

    def _detect_best_installed_model(self) -> str:
        """Detects installed models from local Ollama service."""
        try:
            url = f"{self.ollama_base_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "DataNexusAI/1.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Priority matching for installed models on user's system
                for target in ["qwen2.5-coder:14b", "qwen2.5-coder:32b", "qwen3-coder:30b", "qwen-mirofish:latest", "deepseek-r1:8b", "qwen2.5-coder:7b"]:
                    if target in models:
                        return target
                        
                if models:
                    return models[0]
        except Exception:
            pass
            
        return "qwen2.5-coder:14b"

    def generate_rag_response(self, user_query: str, retrieved_contexts: List[str]) -> str:
        """
        Formats system & context prompt and generates LLM answer via local Ollama.
        """
        context_str = "\n\n".join([f"[Kontext {i+1}]: {ctx}" for i, ctx in enumerate(retrieved_contexts)])
        
        prompt = (
            f"Du bist ein intelligenter DataNexus AI Assistent.\n"
            f"Beantworte die folgende Frage präzise und wahrheitsgemäß auf Deutsch unter Verwendung des bereitgestellten Kontexts:\n\n"
            f"KONTEXT:\n{context_str}\n\n"
            f"FRAGE: {user_query}\n\n"
            f"ANTWORT:"
        )

        try:
            # Live HTTP request to local Ollama API
            url = f"{self.ollama_base_url}/api/generate"
            payload = json.dumps({
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "Keine Antwort vom Modell erhalten.")
        except Exception as e:
            # Fallback error response
            return (
                f"[Lokale Inferenz] Modell '{self.model_name}' bei {self.ollama_base_url} aufgerufen. "
                f"Status/Fehler: {str(e)}. "
                f"Kontext (1. Treffer): {retrieved_contexts[0][:150]}..." if retrieved_contexts else "Keine passenden Dokumente."
            )
