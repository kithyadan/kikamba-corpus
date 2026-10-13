"""Polite HTTP: descriptive User-Agent, robots.txt, >=2s per-host rate limit, retries, file cache."""
from __future__ import annotations

import logging
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import config

log = logging.getLogger(__name__)


class RobotsDisallowed(Exception):
    pass


class PoliteSession:
    def __init__(self, min_interval: float = config.MIN_REQUEST_INTERVAL, user_agent: str = config.USER_AGENT):
        self.min_interval = min_interval
        self.user_agent = user_agent
        self.s = requests.Session()
        self.s.headers["User-Agent"] = user_agent
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _wait(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            delta = time.monotonic() - last
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
        self._last[host] = time.monotonic()

    def allowed(self, url: str) -> bool:
        u = urlparse(url)
        host = f"{u.scheme}://{u.netloc}"
        if host not in self._robots:
            self._wait(u.netloc)
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(host + "/robots.txt", timeout=30)
                ctype = r.headers.get("content-type", "")
                if r.status_code == 200 and "text/plain" in ctype:
                    rp.parse(r.text.splitlines())
                    self._robots[host] = rp
                else:
                    # 4xx / non-text (e.g. S3 XML error) => no robots policy published
                    self._robots[host] = None
            except requests.RequestException:
                self._robots[host] = None
        rp = self._robots[host]
        return True if rp is None else rp.can_fetch(self.user_agent, url)

    def get(self, url: str, *, retries: int = 3, stream: bool = False, **kw) -> requests.Response:
        if not self.allowed(url):
            raise RobotsDisallowed(url)
        host = urlparse(url).netloc
        err: Exception | None = None
        for attempt in range(retries):
            self._wait(host)
            try:
                r = self.s.get(url, timeout=kw.pop("timeout", 120), stream=stream, **kw)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
                r.raise_for_status()
                return r
            except requests.RequestException as e:
                err = e
                resp = getattr(e, "response", None)
                if resp is not None and resp.status_code in (401, 403, 404):
                    break
                time.sleep(min(60, 5 * 2**attempt))
        assert err is not None
        raise err

    def download(self, url: str, dest: Path, force: bool = False) -> Path:
        """Stream url to dest (cached: skipped if dest exists and is non-empty)."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0 and not force:
            return dest
        tmp = dest.with_suffix(dest.suffix + ".part")
        with self.get(url, stream=True) as r, open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.replace(dest)
        return dest


_session: PoliteSession | None = None


def session() -> PoliteSession:
    global _session
    if _session is None:
        _session = PoliteSession()
    return _session
