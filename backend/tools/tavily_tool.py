# tools/tavily_tool.py
import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base_tool import BaseTool


TAVILY_ENDPOINT = "https://api.tavily.com/search"


def _build_session(timeout: float = 20.0, total_retries: int = 3) -> requests.Session:
    """
    Create a requests session with sane defaults: retries on transient failures and a default timeout.
    """
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.request = _timeout_wrapper(session.request, timeout)  # type: ignore
    return session


def _timeout_wrapper(request_fn, timeout: float):
    def wrapped(method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout
        return request_fn(method, url, **kwargs)
    return wrapped


@dataclass
class TavilyOptions:
    """
    Common Tavily options with safe defaults.
    See: https://docs.tavily.com (names kept to Tavily API where possible).
    """
    search_depth: str = "basic"          # "basic" or "advanced"
    max_results: int = 5                 # 1..10 typical
    include_answer: bool = True          # include synthesized answer
    include_images: bool = False         # include image URLs (if any)
    include_raw_content: bool = False    # include raw page text
    topic: Optional[str] = None          # "news" | "general"
    days: Optional[int] = None           # recency filter in days
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None


class TavilySearchTool(BaseTool):
    """
    Strands tool: Tavily web search.
    """

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return (
            "Search the live web using Tavily. "
            "Args: query (str, required), search_depth ('basic'|'advanced')='basic', "
            "max_results (int)=5, include_answer (bool)=True, include_images (bool)=False, "
            "include_raw_content (bool)=False, topic ('news'|'general')=None, days (int)=None, "
            "include_domains (List[str])=None, exclude_domains (List[str])=None. "
            "Returns a dict with keys: 'query','answer','results' (list of {title,url,content,score})."
        )

    def _get_api_key(self) -> str:
        key = os.getenv("TAVILY_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Add it to your environment or .env file."
            )
        return key

    def _payload_from_args(self, query: str, opts: TavilyOptions) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "api_key": self._get_api_key(),
            "query": query,
            "search_depth": opts.search_depth,
            "max_results": opts.max_results,
            "include_answer": opts.include_answer,
            "include_images": opts.include_images,
            "include_raw_content": opts.include_raw_content,
        }
        if opts.topic:
            payload["topic"] = opts.topic
        if opts.days is not None:
            payload["days"] = opts.days
        if opts.include_domains:
            payload["include_domains"] = opts.include_domains
        if opts.exclude_domains:
            payload["exclude_domains"] = opts.exclude_domains
        return payload

    def _call_tavily(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = _build_session()
        resp = session.post(TAVILY_ENDPOINT, json=payload)
        # Try to parse JSON even on non-2xx to surface better errors
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            # If still here, re-raise
            raise

        if resp.status_code >= 400:
            # Tavily often returns {"error": "..."} or similar
            message = data.get("error") or data
            raise RuntimeError(f"Tavily error {resp.status_code}: {message}")

        return data

    def _normalize(self, tavily_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the Tavily response for the LLM/tool consumer.
        Keeps the most useful, compact fields.
        """
        # Tavily returns keys like: 'answer', 'results' (list with title, url, content, score, ...), 'query'
        results = tavily_json.get("results") or []
        norm_results = []
        for r in results:
            norm_results.append(
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "score": r.get("score"),
                    # Keep raw if caller requested include_raw_content; else content above suffices
                }
            )

        return {
            "query": tavily_json.get("query"),
            "answer": tavily_json.get("answer"),
            "results": norm_results,
            # Surface images only if present
            "images": tavily_json.get("images") or None,
            # Keep the raw response for debugging if needed (comment out in prod)
            # "_raw": tavily_json,
        }

    def execute(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = True,
        include_images: bool = False,
        include_raw_content: bool = False,
        topic: Optional[str] = None,
        days: Optional[int] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a Tavily web search.

        Parameters
        ----------
        query : str
            The search query (required).
        search_depth : str
            'basic' (faster) or 'advanced' (deeper browsing).
        max_results : int
            Maximum number of results to return (typical 1..10).
        include_answer : bool
            Include a synthesized answer in the response.
        include_images : bool
            Include image URLs if available.
        include_raw_content : bool
            Include raw page text (larger payload).
        topic : Optional[str]
            'news' for news-focused search, 'general' otherwise.
        days : Optional[int]
            Limit results to the past N days (recency filter).
        include_domains / exclude_domains : Optional[List[str]]
            Whitelist/blacklist domains.

        Returns
        -------
        dict
            { 'query': str, 'answer': Optional[str], 'results': List[...], 'images': Optional[List[str]] }
        """
        if not query or not query.strip():
            raise ValueError("query is required and cannot be empty.")

        opts = TavilyOptions(
            search_depth=search_depth,
            max_results=max_results,
            include_answer=include_answer,
            include_images=include_images,
            include_raw_content=include_raw_content,
            topic=topic,
            days=days,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )

        payload = self._payload_from_args(query=query.strip(), opts=opts)
        data = self._call_tavily(payload)
        return self._normalize(data)
