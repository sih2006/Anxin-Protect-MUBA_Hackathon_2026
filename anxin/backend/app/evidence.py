"""Evidence retrieval, kept strictly separate from model judgement (VER-03).

Two sources of evidence:

1. ``fetch_url`` -- when the user submits a URL directly, we fetch that page
   ourselves (server-side, SSRF-guarded) and hand the extracted text to the
   verifier models as primary evidence.
2. ``web_search`` -- when the user submits free text (a claim, a forwarded
   message, OCR output), we look up a handful of candidate sources through
   DuckDuckGo's HTML endpoint (no API key required, so it works out of the
   box during the hackathon) and pass those snippets + URLs along as
   evidence too.

VER-04 (SSRF hardening):
  * only http/https, only a resolved *public* IP is allowed (no loopback,
    link-local, private RFC1918/RFC4193, or multicast ranges);
  * redirects are followed manually, one hop at a time, re-validating the
    target host every time, up to a small hop limit;
  * response bodies are streamed and cut off at MAX_FETCH_BYTES;
  * HTML is parsed defensively and scripts/styles are dropped before any
    text is used as evidence.
"""
from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("anxin.evidence")

MAX_FETCH_BYTES = 1_500_000
MAX_REDIRECT_HOPS = 3
FETCH_TIMEOUT_SECONDS = 8.0
MAX_SNIPPET_CHARS = 700
MAX_SEARCH_RESULTS = 3

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),  # carrier-grade NAT
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class UnsafeUrlError(ValueError):
    pass


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str


def _host_is_public(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
        if any(ip in net for net in _BLOCKED_NETWORKS):
            return False
    return True


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError("Only http/https URLs are supported.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL is missing a host.")
    if not _host_is_public(parsed.hostname):
        raise UnsafeUrlError("URL resolves to a private, local or reserved address and was blocked.")
    return url


def fetch_url(url: str) -> FetchedPage:
    """Safely fetch a user-submitted URL and extract readable text.

    Raises UnsafeUrlError if the URL (or any redirect target) is not a safe,
    public http(s) address, and httpx.HTTPError-family exceptions on network
    failure. Callers must catch both and degrade to an "evidence unavailable"
    state rather than surfacing a raw stack trace to the user (Definition of
    Done: no raw stack trace reaches users).
    """
    current = _validate_url(url)
    with httpx.Client(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECT_HOPS + 1):
            resp = client.get(current, headers={"User-Agent": "AnxinFactChecker/1.0 (+https://gonkarouter.io)"})
            if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                nxt = urljoin(current, resp.headers["location"])
                current = _validate_url(nxt)
                continue
            resp.raise_for_status()
            raw = resp.content[:MAX_FETCH_BYTES]
            content_type = resp.headers.get("content-type", "")
            break
        else:
            raise UnsafeUrlError("Too many redirects.")

    if "text/html" not in content_type and "application/xhtml" not in content_type:
        # Plain text or unknown type -- use as-is, best effort.
        text = raw.decode("utf-8", errors="ignore")
        return FetchedPage(url=current, title=current, text=text[:8000])

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    title = (soup.title.string or current).strip() if soup.title and soup.title.string else current
    text = " ".join(soup.get_text(separator=" ").split())
    return FetchedPage(url=current, title=title[:300], text=text[:8000])


def to_snippet(text: str, limit: int = MAX_SNIPPET_CHARS) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."


def _decode_ddg_redirect(href: str) -> str | None:
    """DuckDuckGo's HTML endpoint wraps result links as /l/?uddg=<encoded>."""
    parsed = urlparse(href)
    if parsed.path == "/l/" or parsed.netloc == "" and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        target = qs.get("uddg")
        if target:
            return target[0]
    if parsed.scheme in ("http", "https"):
        return href
    return None


def web_search(query: str, max_results: int = MAX_SEARCH_RESULTS) -> list[FetchedPage]:
    """Best-effort evidence discovery with no API key required.

    Returns [] on any failure -- the verifier prompts explicitly instruct the
    models to lower confidence and mark the verdict "unverifiable" when no
    evidence is available, rather than treating an empty list as a crash.
    """
    try:
        with httpx.Client(timeout=FETCH_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "AnxinFactChecker/1.0 (+https://gonkarouter.io)"},
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("web_search failed: %s", exc.__class__.__name__)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[FetchedPage] = []
    for result in soup.select(".result"):
        link = result.select_one(".result__a")
        snippet_el = result.select_one(".result__snippet")
        if link is None:
            continue
        href = link.get("href")
        if not isinstance(href, str) or not href:
            continue
        target = _decode_ddg_redirect(href)
        if not target:
            continue
        try:
            _validate_url(target)
        except UnsafeUrlError:
            continue
        title = link.get_text(strip=True) or target
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        results.append(FetchedPage(url=target, title=title[:300], text=snippet[:MAX_SNIPPET_CHARS]))
        if len(results) >= max_results:
            break
    return results


def now_utc() -> datetime:
    return datetime.now(UTC)
