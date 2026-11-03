# Places search utilities with LangChain tools
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

try:
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

    search_tool = DuckDuckGoSearchRun(
        api_wrapper=DuckDuckGoSearchAPIWrapper(max_results=10)
    )
    _SEARCH_TOOL_ERROR = None
except Exception as exc:
    search_tool = None
    _SEARCH_TOOL_ERROR = exc


def run_places_search(query: str) -> Dict[str, Any]:
    """Run a raw DuckDuckGo search query."""
    if search_tool is None:
        return {"error": f"Places search is unavailable: {_SEARCH_TOOL_ERROR}"}
    try:
        return {"query": query, "results": search_tool.run(query)}
    except Exception as e:
        return {"error": f"Places search failed: {e}"}


def search_places_tool(destination: str, num_results: int = 10) -> Dict[str, Any]:
    """Search the web for the top places to visit at a destination."""
    query = f"top {num_results} places to visit in {destination}"
    result = run_places_search(query)
    if result.get("error"):
        return result

    return {
        "destination": destination,
        "query": query,
        "results": result.get("results", ""),
    }


@tool
def search_places(destination: str, num_results: int = 10) -> Dict[str, Any]:
    """Search the web for the top places to visit at the destination."""
    return search_places_tool(destination, num_results)
