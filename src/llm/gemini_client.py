from langchain_google_genai import ChatGoogleGenerativeAI
from src.llm.base import BaseLLMClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", temperature: float = 0.7):
        logger.info(f"Initializing Gemini Client with model: {model}")
        self.model_name = model
        try:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model,
                temperature=temperature,
                convert_system_message_to_human=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def generate(self, prompt: str) -> str:
        try:
            return self.llm.invoke(prompt).content
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "Error communicating with Gemini."

    def get_model_name(self) -> str:
        return self.model_name
