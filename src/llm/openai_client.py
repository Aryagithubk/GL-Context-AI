from langchain_openai import ChatOpenAI
from src.llm.base import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7):
        logger.info(f"Initializing OpenAI Client with model: {model}")
        self.model_name = model
        try:
            self.llm = ChatOpenAI(
                api_key=api_key,
                model=model,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            return self.llm.invoke(prompt).content
        except Exception as e:
            logger.error(f"Error calling OpenAI: {e}")
            return "Error communicating with OpenAI."

    def get_model_name(self) -> str:
        return self.model_name
