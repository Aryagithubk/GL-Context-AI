from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate response from the LLM."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass
