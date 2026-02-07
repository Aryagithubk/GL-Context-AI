from duckduckgo_search import DDGS
from googlesearch import search as gsearch
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class WebSearch:
    def __init__(self):
        logger.info("Initializing Robust Web Search Tool.")
        # We don't need to instantiate DDGS usually unless we want a session, 
        # but let's just use the context manager in search_query for safety.

    def search_query(self, query: str, max_results: int = 5) -> str:
        """Executes a web search robustly."""
        results_text = ""
        
        # 1. Try DuckDuckGo
        try:
            logger.info(f"Attempting DuckDuckGo search for: {query}")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    for r in results:
                        results_text += f"- Title: {r.get('title')}\n  Link: {r.get('href')}\n  Snippet: {r.get('body')}\n\n"
                    logger.info(f"DuckDuckGo found {len(results)} results.")
                    return results_text
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}. Falling back to Google.")

        # 2. Fallback to Google Search
        try:
            logger.info(f"Attempting Google search for: {query}")
            # googlesearch-python returns a generator of URLs
            # Does not support 'advanced' in standard version, using simple `search`
            results = list(gsearch(query, num_results=max_results, advanced=True))
            
            if results:
                for r in results:
                     # Access attributes if using advanced=True, otherwise it's just a string URL
                    try:
                        title = r.title
                        desc = r.description
                        url = r.url
                        results_text += f"- Title: {title}\n  Link: {url}\n  Snippet: {desc}\n\n"
                    except:
                        # Fallback if 'advanced' fails and returns strings
                        results_text += f"- Link: {str(r)}\n\n"
                
                logger.info(f"Google found {len(results)} results.")
                return results_text

        except Exception as e:
            logger.error(f"Google search also failed: {e}")
        
        if not results_text:
            return "No search results found. The internet connection might be down or blocked."
            
        return results_text
