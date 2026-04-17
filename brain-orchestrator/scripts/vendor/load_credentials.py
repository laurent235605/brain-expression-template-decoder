from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class BrainCredentials:
    username: str
    password: str
    brain_api_url: str = "https://api.worldquantbrain.com"
    brain_url: str = "https://platform.worldquantbrain.com"


def _read_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def load_credentials(
    *,
    skill_dir: Path,
    config_filename: str = "config.json",
    allow_env: bool = True,
    allow_home_secrets: bool = True,
) -> BrainCredentials:
    """Load credentials without printing secrets.

    Priority:
      1) env vars (if allow_env)
      2) skill-local config.json
      3) ~/secrets/platform-brain.json (if allow_home_secrets)

    Supported env vars:
      - BRAIN_USERNAME or BRAIN_EMAIL
      - BRAIN_PASSWORD
      - BRAIN_API_URL (optional)
      - BRAIN_URL (optional)
    """

    env_username = ""
    env_password = ""
    brain_api_url = os.environ.get("BRAIN_API_URL", "https://api.worldquantbrain.com")
    brain_url = os.environ.get("BRAIN_URL", "https://platform.worldquantbrain.com")

    if allow_env:
        env_username = os.environ.get("BRAIN_USERNAME", os.environ.get("BRAIN_EMAIL", ""))
        env_password = os.environ.get("BRAIN_PASSWORD", "")

    if env_username and env_password:
        return BrainCredentials(
            username=env_username,
            password=env_password,
            brain_api_url=brain_api_url,
            brain_url=brain_url,
        )

    cfg_path = skill_dir / config_filename
    cfg = _read_json_file(cfg_path)

    username = (cfg.get("username") or cfg.get("email") or "").strip()
    password = (cfg.get("password") or "").strip()
    brain_api_url = (cfg.get("BRAIN_API_URL") or brain_api_url).strip() or brain_api_url
    brain_url = (cfg.get("BRAIN_URL") or brain_url).strip() or brain_url

    if username and password:
        return BrainCredentials(username=username, password=password, brain_api_url=brain_api_url, brain_url=brain_url)

    if allow_home_secrets:
        home_secret_path = Path.home() / "secrets" / "platform-brain.json"
        secret = _read_json_file(home_secret_path)
        username = (secret.get("email") or secret.get("username") or "").strip()
        password = (secret.get("password") or "").strip()
        if username and password:
            return BrainCredentials(
                username=username,
                password=password,
                brain_api_url=brain_api_url,
                brain_url=brain_url,
            )

    raise RuntimeError(
        "Missing BRAIN credentials. Provide either: "
        "(1) env vars BRAIN_USERNAME/BRAIN_EMAIL + BRAIN_PASSWORD, or "
        f"(2) {cfg_path} with username/password, or "
        "(3) ~/secrets/platform-brain.json with email/password. "
        "See config.example.json for the expected schema."
    )
