"""
Web search tool for LangChain integration with Jerry AI.

This tool provides web search capabilities to supplement Jerry's
knowledge with current information about renewable energy topics.
"""

import asyncio
from typing import Any
from urllib.parse import urlencode

try:
    import aiohttp
    from langchain_core.tools import Tool

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    Tool = None

from ..utils.logging import get_logger

logger = get_logger(__name__)


class WebSearchTool:
    """Web search tool for Jerry AI agent."""

    def __init__(
        self,
        search_engine: str = "duckduckgo",
        max_results: int = 5,
        timeout_seconds: int = 10,
    ):
        """Initialize the web search tool."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Required dependencies not available. "
                "Install with: pip install aiohttp langchain-core"
            )

        self.search_engine = search_engine
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Perform a web search and return results."""
        try:
            logger.info(f"Performing web search: {query}")

            if self.search_engine == "duckduckgo":
                return await self._search_duckduckgo(query)
            raise ValueError(f"Unsupported search engine: {self.search_engine}")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def _search_duckduckgo(self, query: str) -> list[dict[str, Any]]:
        """Search using DuckDuckGo Instant Answer API."""
        try:
            # DuckDuckGo Instant Answer API
            params = {
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1",
            }

            url = "https://api.duckduckgo.com/?" + urlencode(params)

            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_duckduckgo_results(data)
                    logger.warning(f"DuckDuckGo API returned status {response.status}")
                    return []

        except TimeoutError:
            logger.warning(f"Web search timed out after {self.timeout_seconds} seconds")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def _parse_duckduckgo_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse DuckDuckGo API response."""
        results = []

        # Abstract (main answer)
        if data.get("Abstract"):
            results.append(
                {
                    "title": data.get("AbstractText", "")[:100],
                    "content": data.get("Abstract", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": data.get("AbstractSource", ""),
                    "type": "abstract",
                }
            )

        # Answer (direct answer)
        if data.get("Answer"):
            results.append(
                {
                    "title": "Direct Answer",
                    "content": data.get("Answer", ""),
                    "url": "",
                    "source": data.get("AnswerType", ""),
                    "type": "answer",
                }
            )

        # Definition
        if data.get("Definition"):
            results.append(
                {
                    "title": "Definition",
                    "content": data.get("Definition", ""),
                    "url": data.get("DefinitionURL", ""),
                    "source": data.get("DefinitionSource", ""),
                    "type": "definition",
                }
            )

        # Related topics
        related_topics = data.get("RelatedTopics", [])
        for topic in related_topics[: self.max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": topic.get("Text", "")[:100],
                        "content": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "Related Topic",
                        "type": "related",
                    }
                )

        return results[: self.max_results]

    def create_langchain_tool(self) -> Any:
        """Create a LangChain tool from this web search tool."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("LangChain dependencies not available")

        async def search_wrapper(query: str) -> str:
            """Wrapper function for LangChain tool."""
            results = await self.search(query)

            if not results:
                return "No search results found."

            # Format results for the agent
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "").strip()
                content = result.get("content", "").strip()
                source = result.get("source", "").strip()
                url = result.get("url", "").strip()

                result_text = f"{i}. "
                if title:
                    result_text += f"{title}\n"
                if content:
                    result_text += f"   {content}\n"
                if source:
                    result_text += f"   Source: {source}\n"
                if url:
                    result_text += f"   URL: {url}\n"

                formatted_results.append(result_text.strip())

            return "\n\n".join(formatted_results)

        # Convert async function to sync for LangChain
        def sync_search(query: str) -> str:
            """Synchronous wrapper for LangChain."""
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(search_wrapper(query))

        return Tool(
            name="web_search",
            description=(
                "Search the web for current information about renewable energy, "
                "solar panels, batteries, energy markets, and related topics. "
                "Use this when you need up-to-date information beyond your training data. "
                "Input should be a clear search query."
            ),
            func=sync_search,
        )


def create_web_search_tool(
    search_engine: str = "duckduckgo", max_results: int = 5, timeout_seconds: int = 10
) -> Any | None:
    """Create a web search tool for Jerry AI agent."""
    try:
        search_tool = WebSearchTool(
            search_engine=search_engine,
            max_results=max_results,
            timeout_seconds=timeout_seconds,
        )
        return search_tool.create_langchain_tool()
    except ImportError as e:
        logger.warning(f"Cannot create web search tool: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating web search tool: {e}")
        return None


# Australian energy-specific search queries
class AustralianEnergySearchTool(WebSearchTool):
    """Specialized web search tool for Australian energy information."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def search_rebates(self, state: str) -> list[dict[str, Any]]:
        """Search for current rebates in a specific Australian state."""
        query = f"Australia {state} solar battery rebates incentives 2024 2025"
        return await self.search(query)

    async def search_tariffs(self, location: str) -> list[dict[str, Any]]:
        """Search for electricity tariffs and feed-in rates."""
        query = f"Australia {location} electricity tariffs feed-in rates 2024"
        return await self.search(query)

    async def search_installers(
        self, location: str, system_type: str
    ) -> list[dict[str, Any]]:
        """Search for certified installers in a location."""
        query = f"Australia {location} {system_type} installer CEC accredited certified"
        return await self.search(query)

    async def search_equipment(
        self, equipment_type: str, model: str = ""
    ) -> list[dict[str, Any]]:
        """Search for specific equipment information."""
        query = f"Australia {equipment_type} {model} review specifications warranty"
        return await self.search(query)

    def create_australian_energy_tool(self) -> Any:
        """Create a specialized tool for Australian energy searches."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("LangChain dependencies not available")

        async def australian_search_wrapper(query: str) -> str:
            """Wrapper for Australian energy searches."""
            # Enhance query with Australian context
            enhanced_query = f"Australia {query} renewable energy solar battery"
            results = await self.search(enhanced_query)

            if not results:
                return "No Australian energy information found."

            # Format results with Australian focus
            formatted_results = []
            for i, result in enumerate(results, 1):
                content = result.get("content", "").strip()
                source = result.get("source", "").strip()

                # Prioritize Australian sources
                if any(
                    term in content.lower()
                    for term in [
                        "australia",
                        "australian",
                        "aer",
                        "accc",
                        "clean energy council",
                    ]
                ):
                    formatted_results.insert(0, f"{i}. {content} (Source: {source})")
                else:
                    formatted_results.append(f"{i}. {content} (Source: {source})")

            return "\n\n".join(formatted_results[: self.max_results])

        def sync_australian_search(query: str) -> str:
            """Synchronous wrapper for LangChain."""
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(australian_search_wrapper(query))

        return Tool(
            name="australian_energy_search",
            description=(
                "Search for current Australian renewable energy information including "
                "rebates, tariffs, regulations, equipment reviews, and installer information. "
                "Automatically focuses on Australian context and sources. "
                "Input should be your search topic (e.g., 'NSW solar rebates', 'Tesla Powerwall pricing')."
            ),
            func=sync_australian_search,
        )
