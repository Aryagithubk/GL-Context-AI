from src.llm.base import BaseLLMClient
from src.llm.ollama import OllamaClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LLMFactory:
    @staticmethod
    def create_llm(config: dict) -> BaseLLMClient:
        provider = config['llm']['active_provider'].lower()
        default_params = config['llm']['default_params']
        
        logger.info(f"Factory creating LLM for provider: {provider}")

        if provider == "ollama":
            p_config = config['llm']['providers']['ollama']
            return OllamaClient(
                model_name=p_config['model'],
                temperature=default_params.get('temperature', 0.1),
                base_url=p_config.get('base_url', "http://localhost:11434")
            )
        
        elif provider == "openai":
            try:
                from src.llm.openai_client import OpenAIClient
                p_config = config['llm']['providers']['openai']
                return OpenAIClient(
                    api_key=p_config['api_key'],
                    model=p_config['model'],
                    temperature=default_params.get('temperature', 0.7)
                )
            except ImportError:
                logger.error("OpenAI dependencies not installed.")
                raise
        
        elif provider == "gemini":
            try:
                from src.llm.gemini_client import GeminiClient
                p_config = config['llm']['providers']['gemini']
                return GeminiClient(
                    api_key=p_config['api_key'],
                    model=p_config['model'],
                    temperature=default_params.get('temperature', 0.7)
                )
            except ImportError:
                logger.error("Gemini dependencies not installed.")
                raise
                
        elif provider == "anthropic":
            try:
                from src.llm.anthropic_client import AnthropicClient
                p_config = config['llm']['providers']['anthropic']
                return AnthropicClient(
                    api_key=p_config['api_key'],
                    model=p_config['model'],
                    temperature=default_params.get('temperature', 0.7)
                )
            except ImportError:
                logger.error("Anthropic dependencies not installed.")
                raise

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
