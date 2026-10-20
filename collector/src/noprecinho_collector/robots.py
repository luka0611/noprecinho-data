"""robots.txt rules for the source (plan v2 C11).

- real 404 / 410            -> allow all
- 200 + HTML page (soft 404) -> no rules -> allow all, but flagged so it gets logged
- 200 + text rules          -> parse; any Disallow that matches the search path for "*" or our UA -> disallowed
- 401 / 403                 -> disallow all (NO-GO)
- anything else             -> unknown -> treated as disallowed (stop and ask the owner)
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.robotparser import RobotFileParser


@dataclass(frozen=True)
class RobotsVerdict:
    allowed: bool
    status: int
    byte_length: int
    kind: str  # "missing" | "soft404" | "rules" | "forbidden" | "unknown"

    def summary(self) -> str:
        return f"robots.txt status={self.status} bytes={self.byte_length} kind={self.kind} allowed={self.allowed}"


def _looks_like_html(body: str, content_type: str) -> bool:
    head = body.lstrip()[:200].lower()
    return "html" in content_type.lower() or head.startswith("<!doctype") or head.startswith("<html")


def evaluate(status: int, body: str, content_type: str, user_agent: str, path: str) -> RobotsVerdict:
    size = len(body.encode("utf-8"))
    if status in (404, 410):
        return RobotsVerdict(True, status, size, "missing")
    if status in (401, 403):
        return RobotsVerdict(False, status, size, "forbidden")
    if status != 200:
        return RobotsVerdict(False, status, size, "unknown")
    if _looks_like_html(body, content_type):
        return RobotsVerdict(True, status, size, "soft404")
    parser = RobotFileParser()
    parser.parse(body.splitlines())
    bot_token = user_agent.split("/", 1)[0]
    allowed = parser.can_fetch(bot_token, path) and parser.can_fetch("*", path)
    return RobotsVerdict(allowed, status, size, "rules")
