from langchain_anthropic import ChatAnthropic
from src.llm.base import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", temperature: float = 0.7):
        logger.info(f"Initializing Anthropic Client with model: {model}")
        self.model_name = model
        try:
            self.llm = ChatAnthropic(
                api_key=api_key,
                model=model,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            return self.llm.invoke(prompt).content
        except Exception as e:
            logger.error(f"Error calling Anthropic: {e}")
            return "Error communicating with Anthropic."

    def get_model_name(self) -> str:
        return self.model_name
