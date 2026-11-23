"""Online checks that the pinned fixtures still match the live services.

Run from the repository root: python tests/check_drift.py
The hosted tool list needs an Octen API key in OCTEN_API_KEY; without it that check is skipped.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCHEMA_URL = "https://antigravity.google/schemas/v1/plugin.json"
SERVER_URL = "https://mcp.octen.ai/mcp"
USER_AGENT = "octen-antigravity-plugin-drift-check"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, f"refusing to follow a redirect to {newurl}", headers, fp)


def fetch(url, data=None, headers=None, follow_redirects=True, decode=True):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    # Requests that carry the API key never follow redirects, so the key cannot reach another host.
    opener = urllib.request.build_opener() if follow_redirects else urllib.request.build_opener(NoRedirect)
    with opener.open(request, timeout=30) as response:
        body = response.read()
        return response.status, body.decode("utf-8") if decode else None


def mcp_result(body, request_id):
    """Return the JSON-RPC result for request_id from a JSON body or an SSE stream."""
    if not body.lstrip().startswith("{"):
        messages = []
        for event in re.split(r"\r?\n\r?\n", body):
            data = "\n".join(line[5:].lstrip() for line in event.splitlines() if line.startswith("data:"))
            if data:
                messages.append(json.loads(data))
    else:
        messages = [json.loads(body)]
    for message in messages:
        if message.get("id") == request_id:
            if "error" in message:
                raise RuntimeError(f"tools/list failed: {message['error']}")
            return message["result"]
    raise RuntimeError(f"no response with id {request_id} in the tools/list reply")


def check_schema():
    _, body = fetch(SCHEMA_URL)
    live = json.loads(body)
    pinned = json.loads((FIXTURES / "plugin.schema.json").read_text(encoding="utf-8"))
    if live != pinned:
        return [f"{SCHEMA_URL} changed; review it and update tests/fixtures/plugin.schema.json"]
    return []


def check_links():
    problems = []
    for name in ("README.md", "skills/octen-search-guide/SKILL.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for url in sorted(set(re.findall(r"https://[^\s)>`\"']+", text))):
            url = url.rstrip(".,;")
            if url == SERVER_URL:
                continue  # an MCP endpoint, not a page; it answers 401 without credentials
            try:
                status, _ = fetch(url, decode=False)
            except urllib.error.HTTPError as error:
                status = error.code
            except urllib.error.URLError as error:
                problems.append(f"{name}: {url} unreachable ({error.reason})")
                continue
            if status != 200:
                problems.append(f"{name}: {url} returned {status}")
    return problems


def check_tools():
    key = os.environ.get("OCTEN_API_KEY", "").strip()
    if not key:
        print("skip: OCTEN_API_KEY is not set, hosted tool list not checked")
        return []
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "x-api-key": key}
    names, cursor = [], None
    for page in range(1, 51):  # follow nextCursor; the cap only guards against a cursor that never ends
        params = {"cursor": cursor} if cursor else {}
        payload = json.dumps({"jsonrpc": "2.0", "id": page, "method": "tools/list", "params": params}).encode()
        _, body = fetch(SERVER_URL, data=payload, headers=headers, follow_redirects=False)
        result = mcp_result(body, page)
        names += [tool["name"] for tool in result["tools"]]
        cursor = result.get("nextCursor")
        if not cursor:
            break
    else:
        return ["tools/list kept returning nextCursor after 50 pages"]
    pinned = json.loads((FIXTURES / "hosted-tools.json").read_text(encoding="utf-8"))["tools"]
    if sorted(names) != sorted(pinned):
        added, removed = sorted(set(names) - set(pinned)), sorted(set(pinned) - set(names))
        return [f"hosted tools changed (added {added}, removed {removed}); update the fixture, README and the skill"]
    return []


def main():
    problems = []
    for check in (check_schema, check_links, check_tools):
        try:
            problems += check()
        except Exception as error:  # report it and keep running the other checks
            problems.append(f"{check.__name__} could not run: {type(error).__name__}: {error}")
    for problem in problems:
        print("FAIL:", problem)
    print("drift check:", "failed" if problems else "passed")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
