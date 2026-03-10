from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


GITHUB_API_BASE = "https://api.github.com"


def _api_request(
    method: str,
    url: str,
    token: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8").strip()
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc}") from exc


def trigger_extract_workflow(
    repo: str,
    workflow_file: str,
    token: str,
    ref: str,
    run_all: bool,
    pbix_path: str,
    model_serialization: str,
) -> None:
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    payload = {
        "ref": ref,
        "inputs": {
            "runAll": str(run_all).lower(),
            "pbixPath": pbix_path,
            "modelSerialization": model_serialization,
        },
    }
    _api_request("POST", url, token, payload=payload)


def latest_workflow_run(repo: str, workflow_file: str, token: str) -> Dict[str, Any]:
    url = (
        f"{GITHUB_API_BASE}/repos/{repo}/actions/workflows/{workflow_file}/runs"
        "?per_page=1"
    )
    payload = _api_request("GET", url, token)
    runs = payload.get("workflow_runs", [])
    return runs[0] if runs else {}


def artifacts_for_run(repo: str, run_id: int, token: str) -> Dict[str, Any]:
    url = f"{GITHUB_API_BASE}/repos/{repo}/actions/runs/{run_id}/artifacts"
    return _api_request("GET", url, token)
