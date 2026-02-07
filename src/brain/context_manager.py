import os
import random
from typing import List
from langchain_core.documents import Document
from src.utils.logger import setup_logger
from src.llm.base import BaseLLMClient

logger = setup_logger(__name__)

class ContextManager:
    def __init__(self, llm_client: BaseLLMClient, data_dir: str, context_file: str):
        self.llm = llm_client
        self.data_dir = data_dir
        self.context_file = context_file

    def generate_context_summary(self):
        """Generates a summary of the uploaded documents for the Router."""
        logger.info("Generating Knowledge Base Context Summary...")
        
        # 1. Get file names
        if not os.path.exists(self.data_dir):
            logger.error("Data directory not found.")
            return

        files = []
        for root, _, filenames in os.walk(self.data_dir):
            for f in filenames:
                if not f.startswith('.'):
                    files.append(f)
        
        if not files:
            logger.warning("No files found to summarize.")
            return

        file_list = ", ".join(files[:10]) # Limit to top 10 files for prompt brevity
        logger.info(f"Files found: {file_list}")

        # 2. Ask LLM to summarize
        prompt = f"""You are a librarian managing a company knowledge base.
        Based on the following file names, write a short, 1-sentence description of what this knowledge base is about.
        E.g., "This knowledge base contains HR policies, engineering manuals, and financial reports."
        
        File Names: {file_list}
        
        Description:
        """
        
        summary = self.llm.generate(prompt).strip()
        logger.info(f"Generated Summary: {summary}")

        # 3. Store summary
        os.makedirs(os.path.dirname(self.context_file), exist_ok=True)
        with open(self.context_file, "w", encoding='utf-8') as f:
            f.write(summary)
        
        return summary

    def get_context(self) -> str:
        """Reads the stored context summary."""
        if os.path.exists(self.context_file):
            with open(self.context_file, "r", encoding='utf-8') as f:
                return f.read().strip()
        return "General Company Documents"
