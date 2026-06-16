import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

from .models import SourceDocument


API_URL = "https://ja.wikipedia.org/w/api.php"
LICENSE_NAME = "CC BY-SA 4.0"


class WikipediaClient:
    def __init__(
        self,
        user_agent: str,
        delay_seconds: float = 0.5,
        timeout_seconds: float = 20.0,
    ) -> None:
        normalized_user_agent = user_agent.strip()
        has_contact = "@" in normalized_user_agent or "http" in normalized_user_agent
        if not normalized_user_agent or "(" not in normalized_user_agent or not has_contact:
            raise ValueError(
                "Wikimedia User-Agent must include an app name and contact "
                "email or URL, for example: PatternLab/0.1 (you@example.com)"
            )
        self.user_agent = normalized_user_agent
        self.delay_seconds = max(0.0, delay_seconds)
        self.timeout_seconds = timeout_seconds

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urllib.parse.urlencode(
            {"format": "json", "formatversion": "2", **params},
            doseq=True,
        )
        request = urllib.request.Request(
            f"{API_URL}?{query}",
            headers={"User-Agent": self.user_agent},
        )
        payload = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(
                    request, timeout=self.timeout_seconds
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as error:
                if error.code not in {429, 503} or attempt == 2:
                    raise
                retry_after = error.headers.get("Retry-After")
                wait_seconds = (
                    float(retry_after) if retry_after else float(2 ** attempt)
                )
                time.sleep(min(60.0, max(1.0, wait_seconds)))
        if payload is None:
            raise RuntimeError("Wikipedia request failed without a response")
        time.sleep(self.delay_seconds)
        if "error" in payload:
            raise RuntimeError(payload["error"].get("info", "Wikipedia error"))
        return payload

    def category_titles(self, category: str, limit: int = 50) -> List[str]:
        title = category if category.startswith("Category:") else f"Category:{category}"
        titles: List[str] = []
        continuation = None
        while len(titles) < limit:
            params: Dict[str, Any] = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": title,
                "cmnamespace": "0",
                "cmlimit": min(50, limit - len(titles)),
            }
            if continuation:
                params["cmcontinue"] = continuation
            payload = self._request(params)
            titles.extend(
                member["title"]
                for member in payload.get("query", {}).get(
                    "categorymembers", []
                )
            )
            continuation = payload.get("continue", {}).get("cmcontinue")
            if not continuation:
                break
        return titles[:limit]

    def fetch_titles(self, titles: Iterable[str]) -> List[SourceDocument]:
        requested = [title.strip() for title in titles if title.strip()]
        documents: List[SourceDocument] = []
        for offset in range(0, len(requested), 20):
            batch = requested[offset:offset + 20]
            payload = self._request(
                {
                    "action": "query",
                    "prop": "extracts|info|revisions",
                    "titles": "|".join(batch),
                    "explaintext": "1",
                    "exsectionformat": "plain",
                    "inprop": "url",
                    "rvprop": "ids|timestamp",
                    "redirects": "1",
                }
            )
            for page in payload.get("query", {}).get("pages", []):
                if page.get("missing"):
                    continue
                revision = (page.get("revisions") or [{}])[0]
                documents.append(
                    SourceDocument(
                        source_kind="wikipedia-ja",
                        title=page["title"],
                        url=page.get("canonicalurl") or page.get("fullurl", ""),
                        revision_id=str(revision.get("revid", "unknown")),
                        fetched_at=datetime.now(timezone.utc).isoformat(),
                        license_name=LICENSE_NAME,
                        attribution=(
                            f"Wikipedia contributors, {page['title']}"
                        ),
                        text=page.get("extract", ""),
                        metadata={
                            "revision_timestamp": revision.get("timestamp"),
                            "api": API_URL,
                        },
                    )
                )
        return documents
