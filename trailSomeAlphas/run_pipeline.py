import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import csv
import time
from pathlib import Path

import requests

# Ensure UTF-8 stdout on Windows to avoid UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
SKILLS_DIR = BASE_DIR / "skills"
FEATURE_ENGINEERING_DIR = SKILLS_DIR / "brain-data-feature-engineering"
FEATURE_IMPLEMENTATION_DIR = SKILLS_DIR / "brain-feature-implementation"
FEATURE_IMPLEMENTATION_SCRIPTS = FEATURE_IMPLEMENTATION_DIR / "scripts"

sys.path.insert(0, str(FEATURE_IMPLEMENTATION_SCRIPTS))
try:
    import ace_lib  # type: ignore
except Exception as exc:
    raise SystemExit(f"Failed to import ace_lib from {FEATURE_IMPLEMENTATION_SCRIPTS}: {exc}")
try:
    from validator import ExpressionValidator  # type: ignore
except Exception as exc:
    raise SystemExit(f"Failed to import ExpressionValidator from {FEATURE_IMPLEMENTATION_SCRIPTS}: {exc}")

def load_brain_credentials(config_path: Path) -> tuple[str, str]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    creds = data.get("BRAIN_CREDENTIALS", {})
    email = creds.get("email")
    password = creds.get("password")
    if not email or not password:
        raise ValueError("BRAIN_CREDENTIALS missing in config.json")
    return email, password

def load_brain_credentials_from_env_or_args(username: str | None, password: str | None, config_path: Path) -> tuple[str, str]:
    env_user = os.environ.get("BRAIN_USERNAME") or os.environ.get("BRAIN_EMAIL")
    env_pass = os.environ.get("BRAIN_PASSWORD")
    final_user = username or env_user
    final_pass = password or env_pass
    if final_user and final_pass:
        return final_user, final_pass
    return load_brain_credentials(config_path)

def start_brain_session(email: str, password: str):
    ace_lib.get_credentials = lambda: (email, password)
    return ace_lib.start_session()


def _record_llm_request(stage: str | None = None, model: str | None = None) -> None:
    counter_path = (os.environ.get("PIPELINE_LLM_COUNTER_PATH") or "").strip()
    if not counter_path:
        return
    event = {
        "at": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "stage": stage or os.environ.get("PIPELINE_LLM_COUNTER_STAGE", "generate"),
        "model": model or os.environ.get("MOONSHOT_MODEL", ""),
    }
    try:
        path = Path(counter_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass

def pick_first_present_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    # also try case-insensitive
    lower_map = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]
    return None


def select_dataset(datasets_df, data_category: str, dataset_id: str | None):
    if dataset_id:
        return dataset_id, None, None, datasets_df

    category_col = pick_first_present_column(
        datasets_df,
        ["category", "data_category", "dataCategory", "category_name", "dataCategory_name"],
    )

    filtered = datasets_df
    if category_col:
        filtered = datasets_df[datasets_df[category_col].astype(str).str.lower() == data_category.lower()]

    if filtered.empty:
        filtered = datasets_df

    id_col = pick_first_present_column(filtered, ["id", "dataset_id", "datasetId"])
    name_col = pick_first_present_column(filtered, ["name", "dataset_name", "datasetName"])
    desc_col = pick_first_present_column(filtered, ["description", "desc", "dataset_description"])

    if not id_col:
        raise ValueError("Unable to locate dataset id column from dataset list")

    row = filtered.iloc[0]
    return row[id_col], row.get(name_col) if name_col else None, row.get(desc_col) if desc_col else None, datasets_df


def build_field_summary(fields_df, max_fields: int | None = None):
    id_col = pick_first_present_column(fields_df, ["id", "field_id", "fieldId"])
    desc_col = pick_first_present_column(fields_df, ["description", "desc"])

    total = int(fields_df.shape[0])
    if max_fields is None:
        # Default: pass ALL fields to the prompt.
        subset = fields_df
    else:
        n = min(int(max_fields), total)
        subset = fields_df.head(n)

    rows = []
    for _, row in subset.iterrows():
        rows.append(
            {
                "id": row.get(id_col),
                "description": row.get(desc_col)
            }
        )
    return rows, fields_df.shape[0]


def read_text_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def build_allowed_metric_suffixes(fields_df, max_suffixes: int = 300) -> list[str]:
    """Derive a practical list of placeholder candidates from dataset field ids.

    `implement_idea.py` matches `{variable}` by searching for that substring in the
    field id and then using the *base* (everything before first occurrence) to
    align the other variables. In practice, good placeholders tend to be the
    trailing 2-5 underscore-joined tokens.
    """

    id_col = pick_first_present_column(fields_df, ["id", "field_id", "fieldId"])
    if not id_col:
        return []

    field_ids = fields_df[id_col].dropna().astype(str).tolist()
    dataset_code = detect_dataset_code(field_ids)

    counts: dict[str, int] = {}
    for raw in field_ids:
        parts = [p for p in str(raw).split("_") if p]
        if len(parts) < 2:
            continue

        # Collect suffix candidates from the tail.
        # Prefer multi-token names, but allow single-token suffixes when they're
        # specific enough (e.g., "inventories").
        # IMPORTANT: never allow the "suffix" to equal the full id (that would
        # encourage the LLM to emit {full_field_id}, violating the suffix-only rule).
        for n in range(1, min(6, len(parts))):
                suffix = "_".join(parts[-n:])
                # Filter out overly-generic / numeric suffixes
                if suffix.replace("_", "").isdigit():
                    continue
                if dataset_code and suffix.lower().startswith(dataset_code.lower() + "_"):
                    continue
                if n == 1 and len(suffix) < 8:
                    continue
                if len(suffix) < 6:
                    continue
                counts[suffix] = counts.get(suffix, 0) + 1

    # Prefer suffixes that show up multiple times and have underscores
    ranked = sorted(
        counts.items(),
        key=lambda kv: (kv[1], kv[0].count("_"), len(kv[0])),
        reverse=True,
    )

    suffixes: list[str] = []
    for suffix, _ in ranked:
        if suffix not in suffixes:
            suffixes.append(suffix)
        if len(suffixes) >= max_suffixes:
            break
    return suffixes


def build_allowed_suffixes_from_ids(dataset_ids: list[str], max_suffixes: int = 300) -> list[str]:
    """Build suffix candidates from downloaded dataset ids.

    This is used to normalize/validate templates for `implement_idea.py`.
    """

    counts: dict[str, int] = {}
    for raw in dataset_ids:
        parts = [p for p in str(raw).split("_") if p]
        if len(parts) < 2:
            continue
        for n in range(1, 6):
            if len(parts) >= n:
                suffix = "_".join(parts[-n:])
                if suffix.replace("_", "").isdigit():
                    continue
                if n == 1 and len(suffix) < 8:
                    continue
                if len(suffix) < 6:
                    continue
                counts[suffix] = counts.get(suffix, 0) + 1

    ranked = sorted(
        counts.items(),
        key=lambda kv: (kv[1], kv[0].count("_"), len(kv[0])),
        reverse=True,
    )

    suffixes: list[str] = []
    for suffix, _ in ranked:
        if suffix not in suffixes:
            suffixes.append(suffix)
        if len(suffixes) >= max_suffixes:
            break
    return suffixes


def detect_dataset_code(dataset_ids: list[str]) -> str | None:
    if not dataset_ids:
        return None
    counts: dict[str, int] = {}
    for fid in dataset_ids:
        tok = (str(fid).split("_", 1)[0] or "").strip()
        if tok:
            counts[tok] = counts.get(tok, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]

def ensure_metadata_block(markdown_text: str, dataset_id: str, region: str, delay: int) -> str:
    """Ensure the ideas markdown contains the metadata block used by the pipeline."""

    has_dataset = re.search(r"^\*\*Dataset\*\*:\s*\S+", markdown_text, flags=re.MULTILINE) is not None
    has_region = re.search(r"^\*\*Region\*\*:\s*\S+", markdown_text, flags=re.MULTILINE) is not None
    has_delay = re.search(r"^\*\*Delay\*\*:\s*\d+", markdown_text, flags=re.MULTILINE) is not None
    if has_dataset and has_region and has_delay:
        return markdown_text

    block = [
        "",
        f"**Dataset**: {dataset_id}",
        f"**Region**: {region}",
        f"**Delay**: {delay}",
        "",
    ]

    lines = markdown_text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines[:10]):
        if line.strip():
            insert_at = i + 1
            break
    new_lines = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(new_lines).lstrip("\n")

def compress_to_known_suffix(var: str, allowed_suffixes: list[str]) -> str | None:
    v = var.lower()
    for sfx in sorted(allowed_suffixes, key=len, reverse=True):
        if v.endswith(sfx.lower()):
            return sfx
    return None

def placeholder_is_reasonably_matchable(var: str, dataset_ids: list[str]) -> bool:
    """Heuristic check that a placeholder is likely to match real ids.

    We avoid treating very short tokens as valid unless they match a token boundary.
    """

    v = var
    if len(v) <= 3:
        pat = re.compile(rf"(^|_){re.escape(v)}(_|$)", flags=re.IGNORECASE)
        return any(pat.search(str(fid)) for fid in dataset_ids)
    return any(v in str(fid) for fid in dataset_ids)

def normalize_template_placeholders(
    template: str,
    dataset_ids: list[str],
    allowed_suffixes: list[str],
    dataset_code: str | None,
) -> tuple[str, bool]:
    """Normalize placeholders to suffix-only form, without dataset-specific aliasing.

    - Strips dataset code prefix (e.g. fnd72_*) when present.
    - Compresses placeholders to the longest known suffix.
    - Returns (normalized_template, is_valid).
    """

    vars_in_template = re.findall(r"\{([A-Za-z0-9_]+)\}", template)
    if not vars_in_template:
        return template, False

    mapping: dict[str, str] = {}
    for var in set(vars_in_template):
        new_var = var
        if dataset_code and new_var.lower().startswith(dataset_code.lower() + "_"):
            new_var = new_var[len(dataset_code) + 1 :]

        compressed = compress_to_known_suffix(new_var, allowed_suffixes)
        if compressed:
            new_var = compressed

        mapping[var] = new_var

    normalized = template
    for src, dst in mapping.items():
        normalized = normalized.replace("{" + src + "}", "{" + dst + "}")

    # Validate: every placeholder should look matchable in real ids.
    vars_after = re.findall(r"\{([A-Za-z0-9_]+)\}", normalized)
    ok = all(placeholder_is_reasonably_matchable(v, dataset_ids) for v in vars_after)
    return normalized, ok

def build_prompt(
    dataset_id: str,
    dataset_name: str | None,
    dataset_description: str | None,
    data_category: str,
    region: str,
    delay: int,
    universe: str,
    data_type: str,
    fields_summary: list[dict],
    field_count: int,
    feature_engineering_skill_md: str,
    feature_implementation_skill_md: str,
    allowed_metric_suffixes: list[str],
    allowed_operators,
    system_prompt_override: str | None = None,
):
    def _render_prompt_template(template: str, mapping: dict[str, str]) -> str:
        rendered = str(template or "")
        for key, value in mapping.items():
            rendered = rendered.replace("{{" + key + "}}", str(value or ""))
        return rendered

    # NOTE: The user requested that we DO NOT invent our own system prompt.
    # Instead, we embed the two skill specs as the authoritative instructions.
    prompt_lines = [
            "You are executing two skills in sequence:",
            "1) brain-data-feature-engineering",
            "2) brain-feature-implementation",
            "The following SKILL.md documents are authoritative; follow them exactly.",
            "",
            "--- SKILL.md (brain-data-feature-engineering) ---",
            feature_engineering_skill_md.strip(),
            "",
            "--- SKILL.md (brain-feature-implementation) ---",
            feature_implementation_skill_md.strip(),
            "------"
            f'"allowed_operators": {allowed_operators}',
            "-------",
            f'"allowed_placeholders": {allowed_metric_suffixes}',
            "",
        ]

    if str(data_type).upper() == "VECTOR":
        prompt_lines.append(
            "since all the following the data is vector type data, before you do any process, you should choose a vector operator to generate its statistical feature to use, the data cannot be directly use. for example, if datafieldA and datafieldB are vector type data, you can use vec_avg(datafieldA) -  vec_avg(datafieldB), where vec_avg() operator is used to generate the average of the data on a certain date. similarly, vector type operator can only be used on the vector type operator directly and cannot be nested, for example vec_avg(vec_sum(datafield)) is a false use."
        )
        vector_ops: list[str] = []
        if isinstance(allowed_operators, list):
            for op in allowed_operators:
                if not isinstance(op, dict):
                    continue
                category = str(op.get("category") or "").strip().lower()
                name = str(op.get("name") or "").strip()
                if category == "vector" and name:
                    vector_ops.append(name)

        if vector_ops:
            vector_ops = sorted(set(vector_ops), key=lambda x: x.lower())
        else:
            vector_ops = ["vec_avg", "vec_sum", "vec_max", "vec_min", "vec_std", "vec_count"]

        prompt_lines.append("the available vector operators are: " + ", ".join(vector_ops))

    prompt_lines.extend(
        [
            "CRITICAL OUTPUT RULES (to ensure implement_idea.py can generate expressions):",
            "- Every Implementation Example MUST be a Python format template using {variable}.",
            "- Every {variable} MUST come from the allowed_placeholders list provided in user content.",
            "- When you implement ideas, ONLY use operators from allowed_operators provided.",
            "- Do NOT include dataset codes/prefixes/horizons in {variable} (suffix-only).",
            "- If you show raw field ids in tables, use backticks `like_this`, NOT {braces}.",
            "- Include these metadata lines verbatim somewhere near the top:",
            "  **Dataset**: <dataset_id>",
            "  **Region**: <region>",
            "  **Delay**: <delay>",
        ]
    )

    system_prompt = "\n".join(prompt_lines)

    if system_prompt_override:
        vector_hint = ""
        vector_ops_line = ""
        if str(data_type).upper() == "VECTOR":
            vector_hint = (
                "since all the following the data is vector type data, before you do any process, you should choose a vector operator to generate its statistical feature to use, the data cannot be directly use. for example, if datafieldA and datafieldB are vector type data, you can use vec_avg(datafieldA) -  vec_avg(datafieldB), where vec_avg() operator is used to generate the average of the data on a certain date. similarly, vector type operator can only be used on the vector type operator directly and cannot be nested, for example vec_avg(vec_sum(datafield)) is a false use."
            )
            vector_ops = []
            if isinstance(allowed_operators, list):
                for op in allowed_operators:
                    if not isinstance(op, dict):
                        continue
                    category = str(op.get("category") or "").strip().lower()
                    name = str(op.get("name") or "").strip()
                    if category == "vector" and name:
                        vector_ops.append(name)
            if vector_ops:
                vector_ops = sorted(set(vector_ops), key=lambda x: x.lower())
            else:
                vector_ops = ["vec_avg", "vec_sum", "vec_max", "vec_min", "vec_std", "vec_count"]
            vector_ops_line = "the available vector operators are: " + ", ".join(vector_ops)

        system_prompt = _render_prompt_template(
            system_prompt_override,
            {
                "FEATURE_ENGINEERING_SKILL_MD": feature_engineering_skill_md.strip(),
                "FEATURE_IMPLEMENTATION_SKILL_MD": feature_implementation_skill_md.strip(),
                "ALLOWED_OPERATORS_JSON": json.dumps(allowed_operators, ensure_ascii=False),
                "ALLOWED_PLACEHOLDERS_JSON": json.dumps(allowed_metric_suffixes, ensure_ascii=False),
                "VECTOR_DATA_HINT": vector_hint,
                "VECTOR_OPERATORS_LINE": vector_ops_line,
            },
        )

    user_prompt = {
        "instructions": {
            "output_format": "Fill OUTPUT_TEMPLATE.md with concrete content.",
            "implementation_examples": (
                "Each Implementation Example must be a template with {variable} placeholders. "
                "Use only placeholders from allowed_placeholders. "
                "Use suffix-only names; do not include dataset code/prefix/horizon."
            ),
            "no_code_fences": True,
            "do_not_invent_placeholders": True,
        },
        "dataset_context": {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "dataset_description": dataset_description,
            "category": data_category,
            "region": region,
            "delay": delay,
            "universe": universe,
            "field_count": field_count,
        },

        "fields": fields_summary,
    }
    # print(user_prompt) #for debug
    # print(system_prompt) #for debug
    return system_prompt, json.dumps(user_prompt, ensure_ascii=False, indent=2)


def _vector_ratio_from_datafields_df(datafields_df) -> float:
    if datafields_df is None or getattr(datafields_df, "empty", True):
        return 0.0
    dtype_col = pick_first_present_column(datafields_df, ["type", "dataType", "data_type"])
    if not dtype_col:
        return 0.0
    counts = datafields_df[dtype_col].astype(str).value_counts().to_dict()
    vector_count = counts.get("VECTOR", 0)
    total = sum(counts.values())
    return (vector_count / total) if total else 0.0


def filter_operators_df(operators_df, keep_vector: bool):
    """Apply user-confirmed operator filters.

    Rules:
    - Keep only scope == REGULAR
    - Drop category == Group
    - Keep category == Vector only if keep_vector is True
    - Drop names matching /rank|neutral|normal|scal/i
    """

    df = operators_df.copy()

    name_col = pick_first_present_column(df, ["name", "operator", "op", "id"])
    scope_col = pick_first_present_column(df, ["scope", "scopes"])
    category_col = pick_first_present_column(df, ["category", "group", "type"])
    desc_col = pick_first_present_column(df, ["description", "desc", "help", "doc", "documentation"])
    definition_col = pick_first_present_column(df, ["definition", "syntax"])

    if scope_col:
        df = df[df[scope_col].astype(str).str.upper() == "REGULAR"]

    if category_col:
        df = df[df[category_col].astype(str).str.lower() != "group"]
        if not keep_vector:
            df = df[df[category_col].astype(str).str.lower() != "vector"]

    if name_col:
        banned = re.compile(r"(?:rank|neutral|normal|scal|zscore)", flags=re.IGNORECASE)
        df = df[~df[name_col].astype(str).str.contains(banned, na=False)]

        # de-dup by operator name
        df = df.drop_duplicates(subset=[name_col]).reset_index(drop=True)

    cols = [c for c in [name_col, category_col, scope_col, desc_col, definition_col] if c]
    allowed = []
    for _, row in df.iterrows():
        item = {
            "name": row.get(name_col) if name_col else None,
            "category": row.get(category_col) if category_col else None,
            "scope": row.get(scope_col) if scope_col else None,
            "description": row.get(desc_col) if desc_col else None,
            "definition": row.get(definition_col) if definition_col else None,
        }
        # drop None keys to keep prompt compact
        allowed.append({k: v for k, v in item.items() if v is not None})

    return df, allowed, cols

def call_moonshot(api_key: str, model: str, system_prompt: str, user_prompt: str, timeout_s: int = 120):
    base_url = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],

        # Default to streaming so the user can observe model progress.
        "stream": True,
    }

    retries = int(os.environ.get("MOONSHOT_RETRIES", "2"))
    backoff_s = float(os.environ.get("MOONSHOT_RETRY_BACKOFF", "2"))

    def _stream_sse_and_collect(resp: requests.Response) -> str:
        """Read OpenAI-compatible SSE stream and print deltas live.

        Still returns the full accumulated assistant content so existing callers
        (which expect a string) keep working.
        """

        content_parts: list[str] = []
        thinking_parts: list[str] = []
        thinking = False

        # Ensure requests doesn't try to decode as bytes.
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                break

            try:
                event = json.loads(data_str)
            except Exception:
                continue

            choices = event.get("choices") or []
            if not choices:
                continue
            choice0 = choices[0] if isinstance(choices[0], dict) else None
            if not choice0:
                continue

            delta = choice0.get("delta") or {}
            if not isinstance(delta, dict):
                delta = {}

            # Moonshot/Kimi exposes reasoning tokens as `reasoning_content`.
            reasoning = delta.get("reasoning_content")
            if reasoning:
                if not thinking:
                    thinking = True
                    print("=============开始思考=============", flush=True)
                thinking_parts.append(str(reasoning))
                print(str(reasoning), end="", flush=True)

            piece = delta.get("content")
            if piece:
                if thinking:
                    thinking = False
                    print("\n=============思考结束=============", flush=True)
                content_parts.append(str(piece))
                print(str(piece), end="", flush=True)

            finish_reason = choice0.get("finish_reason")
            if finish_reason:
                break

        # If the stream ended while still "thinking", close the marker cleanly.
        if thinking:
            print("\n=============思考结束=============", flush=True)

        return "".join(content_parts)

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            _record_llm_request(stage=os.environ.get("PIPELINE_LLM_COUNTER_STAGE", "generate"), model=model)
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s, stream=True)
            resp.encoding = "utf-8"
            if resp.status_code >= 300:
                raise RuntimeError(f"Moonshot API error {resp.status_code}: {resp.text}")

            # Prefer SSE streaming when available.
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "text/event-stream" in ctype or payload.get("stream"):
                return _stream_sse_and_collect(resp)

            data = resp.json()
            break
        except KeyboardInterrupt as exc:
            raise RuntimeError(
                "Moonshot/Kimi 流式响应在等待过程中被中断。"
                "常见原因是手动 Ctrl+C、父进程要求停止，或长连接期间本地网络中断。"
            ) from exc
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt >= retries:
                raise
            time.sleep(backoff_s * (2**attempt))
        except requests.exceptions.RequestException as exc:
            # Other request-layer issues: retry a bit, but don't loop forever.
            last_exc = exc
            if attempt >= retries:
                raise
            time.sleep(backoff_s * (2**attempt))
    else:
        raise last_exc or RuntimeError("Moonshot request failed")

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Unexpected Moonshot response: {data}") from exc
def save_ideas_report(content: str, region: str, delay: int, dataset_id: str) -> Path:
    output_dir = FEATURE_ENGINEERING_DIR / "output_report"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{region}_delay{delay}_{dataset_id}_ideas.md"
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path

def extract_templates(markdown_text: str) -> list[str]:
    """Extract implementation templates from idea markdown.

    For pipeline robustness, this function returns ONLY the template strings.
    The recommended, higher-fidelity parser is `extract_template_blocks()`,
    which returns both template + idea text per **Concept** block.
    """

    blocks = extract_template_blocks(markdown_text)
    templates = [b["template"] for b in blocks if b.get("template")]
    return sorted(set(t.strip() for t in templates if t and t.strip()))


def extract_template_blocks(markdown_text: str) -> list[dict[str, str]]:
    """Parse **Concept** blocks and extract {template, idea}.

    A "block" is a section that starts with a line like:
      **Concept**: ...
    and contains a line like:
      - **Implementation Example**: `...`

    Output:
      [{"template": <string>, "idea": <string>}, ...]

    Notes:
    - `template` is taken from inside backticks when present; otherwise uses the
      remainder of the line after ':'.
    - `idea` is the rest of the block text (including the concept line and
      bullets) excluding the implementation example line.
    """

    concept_re = re.compile(r"^\*\*Concept\*\*\s*:\s*(.*)\s*$")
    impl_re = re.compile(r"\*\*Implementation Example\*\*\s*:\s*(.*)$", flags=re.IGNORECASE)
    backtick_re = re.compile(r"`([^`]*)`")
    boundary_re = re.compile(r"^(?:-{3,}|#{1,6}\s+.*)\s*$")

    lines = markdown_text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []

    def _flush():
        nonlocal current
        if current:
            # Trim leading/trailing blank lines in block.
            while current and not current[0].strip():
                current.pop(0)
            while current and not current[-1].strip():
                current.pop()
            if current:
                blocks.append(current)
        current = []

    for line in lines:
        if concept_re.match(line.strip()):
            _flush()
            current = [line]
            continue

        # If we are inside a concept block and hit a section boundary (e.g. '---', '### Q2'),
        # close the block so unrelated headings don't get included in the idea text.
        if current and boundary_re.match(line.strip()):
            _flush()
            continue

        if current:
            current.append(line)

    _flush()

    out: list[dict[str, str]] = []
    for block_lines in blocks:
        template: str | None = None
        impl_line_idx: int | None = None

        # Find the implementation example line (or its continuation).
        for i, raw in enumerate(block_lines):
            m = impl_re.search(raw)
            if not m:
                continue

            impl_line_idx = i
            tail = (m.group(1) or "").strip()

            # Case 1: template is in backticks on the same line.
            bt = backtick_re.search(tail)
            if bt:
                template = bt.group(1).strip()
                break

            # Case 2: tail itself is the template.
            if tail and ("{" in tail and "}" in tail):
                template = tail.strip().strip("`")
                break

            # Case 3: template is on the next non-empty line, often in backticks.
            for j in range(i + 1, min(i + 4, len(block_lines))):
                nxt = block_lines[j].strip()
                if not nxt:
                    continue
                bt2 = backtick_re.search(nxt)
                if bt2:
                    template = bt2.group(1).strip()
                    break
                if "{" in nxt and "}" in nxt:
                    template = nxt.strip().strip("`")
                    break
            break

        if not template or "{" not in template or "}" not in template:
            continue

        # idea = all block text except the implementation example line itself.
        idea_lines: list[str] = []
        for i, raw in enumerate(block_lines):
            if impl_line_idx is not None and i == impl_line_idx:
                continue
            idea_lines.append(raw)

        idea = "\n".join(idea_lines).strip()
        out.append({"template": template.strip(), "idea": idea})

    return out

def load_dataset_ids_from_csv(dataset_csv_path: Path) -> list[str]:
    if not dataset_csv_path.exists():
        return []
    ids: list[str] = []
    with dataset_csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "id" not in (reader.fieldnames or []):
            return []
        for row in reader:
            v = (row.get("id") or "").strip()
            if v:
                ids.append(v)
    return ids

def safe_dataset_id(dataset_id: str) -> str:
    return "".join([c for c in dataset_id if c.isalnum() or c in ("-", "_")])

def run_script(args_list: list[str], cwd: Path):
    result = subprocess.run(args_list, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Command failed: "
            + " ".join(args_list)
            + f"\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout


def delete_path_if_exists(path: Path):
    """Best-effort delete a file or directory."""

    try:
        if not path.exists():
            return
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    except Exception:
        # Best-effort cleanup only; rerun should still proceed.
        return

def main():
    parser = argparse.ArgumentParser(description="Run feature engineering + implementation pipeline")
    parser.add_argument("--data-category", required=True, help="Dataset category (e.g., analyst, fundamental)")
    parser.add_argument("--region", required=True, help="Region (e.g., USA, GLB, EUR)")
    parser.add_argument("--delay", required=True, type=int, help="Delay (0 or 1)")
    parser.add_argument("--universe", default="TOP3000", help="Universe (default: TOP3000)")
    parser.add_argument("--dataset-id", required=True, help="Dataset id (required)")
    parser.add_argument("--instrument-type", default="EQUITY", help="Instrument type (default: EQUITY)")
    parser.add_argument(
        "--data-type",
        default="MATRIX",
        choices=["MATRIX", "VECTOR"],
        help="Data type to request from BRAIN datafields (MATRIX or VECTOR). Default: MATRIX",
    )
    parser.add_argument("--ideas-file", default=None, help="Use existing ideas markdown instead of generating")
    parser.add_argument(
        "--regen-ideas",
        action="store_true",
        help="Force regenerating ideas markdown even if the default ideas file already exists",
    )
    parser.add_argument("--moonshot-api-key", default=None, help="Moonshot API key (prefer env MOONSHOT_API_KEY)")
    parser.add_argument("--moonshot-model", default="kimi-k2.5", help="Moonshot model (default: k2.5)")
    parser.add_argument("--username", default=None, help="BRAIN username/email (override config/env)")
    parser.add_argument("--password", default=None, help="BRAIN password (override config/env)")
    parser.add_argument(
        "--max-fields",
        type=int,
        default=None,
        help="If set, pass TOP N fields to LLM; if omitted, randomly sample 50 (or all if <50)",
    )
    parser.add_argument(
        "--no-operators-in-prompt",
        action="store_true",
        help="Do not include allowed_operators in the idea-generation prompt",
    )
    parser.add_argument(
        "--max-operators",
        type=int,
        default=300,
        help="Max filtered operators to include in prompt (default: 300)",
    )

    args = parser.parse_args()

    config_path = FEATURE_IMPLEMENTATION_DIR / "config.json"
    email, password = load_brain_credentials_from_env_or_args(args.username, args.password, config_path)
    session = start_brain_session(email, password)

    # Always rerun cleanly: remove prior generated artifacts so we never reuse stale ideas/data.
    # - If --ideas-file is provided, we treat it as user-managed input and do NOT delete it.
    # - We DO delete the dataset-specific folder under feature-implementation/data.
    if not args.ideas_file:
        default_ideas = (
            FEATURE_ENGINEERING_DIR
            / "output_report"
            / f"{args.region}_delay{args.delay}_{args.dataset_id}_ideas.md"
        )
        delete_path_if_exists(default_ideas)

    guessed_dataset_folder = f"{safe_dataset_id(args.dataset_id)}_{args.region}_delay{args.delay}"
    guessed_dataset_dir = FEATURE_IMPLEMENTATION_DIR / "data" / guessed_dataset_folder
    delete_path_if_exists(guessed_dataset_dir)

    ideas_path = None
    if args.ideas_file:
        ideas_path = Path(args.ideas_file).resolve()
        if not ideas_path.exists():
            raise FileNotFoundError(f"Ideas file not found: {ideas_path}")
    else:
        # Always regenerate ideas (never reuse an existing markdown report).
        datasets_df = ace_lib.get_datasets(
            session,
            instrument_type=args.instrument_type,
            region=args.region,
            delay=args.delay,
            universe=args.universe,
            theme="ALL",
        )

        dataset_name = None
        dataset_description = None
        id_col = pick_first_present_column(datasets_df, ["id", "dataset_id", "datasetId"])
        name_col = pick_first_present_column(datasets_df, ["name", "dataset_name", "datasetName"])
        desc_col = pick_first_present_column(datasets_df, ["description", "desc", "dataset_description"])
        if id_col:
            matched = datasets_df[datasets_df[id_col].astype(str) == str(args.dataset_id)]
            if not matched.empty:
                row = matched.iloc[0]
                dataset_name = row.get(name_col) if name_col else None
                dataset_description = row.get(desc_col) if desc_col else None

        fields_df = ace_lib.get_datafields(
            session,
            instrument_type=args.instrument_type,
            region=args.region,
            delay=args.delay,
            universe=args.universe,
            dataset_id=args.dataset_id,
            data_type=args.data_type,
        )

        # --- Field blacklist injection --------------------------------
        # If pipeline_runner or an external caller sets
        # PIPELINE_FIELD_BLACKLIST_JSON to a JSON file produced by
        # brain-orchestrator/scripts/build_field_blacklist.py, drop every
        # blacklisted field from fields_df before we build the prompt.
        # This prevents the LLM from ever seeing zombie fields.
        _bl_path = os.environ.get("PIPELINE_FIELD_BLACKLIST_JSON", "").strip()
        if _bl_path:
            try:
                with open(_bl_path, "r", encoding="utf-8") as _fh:
                    _bl_payload = json.load(_fh)
                _bl_ids = {
                    str(b.get("id"))
                    for b in (_bl_payload.get("blacklist") or [])
                    if b.get("id")
                }
                if _bl_ids and "id" in fields_df.columns:
                    _before = len(fields_df)
                    fields_df = fields_df[~fields_df["id"].astype(str).isin(_bl_ids)].reset_index(drop=True)
                    print(
                        f"[field-blacklist] applied {_bl_path}: "
                        f"dropped {_before - len(fields_df)} fields "
                        f"(kept {len(fields_df)})",
                        file=sys.stderr,
                    )
            except Exception as _exc:
                print(f"[field-blacklist] skipped — load failed: {_exc}", file=sys.stderr)

        feature_engineering_skill_md = read_text_optional(FEATURE_ENGINEERING_DIR / "SKILL.md")
        feature_implementation_skill_md = read_text_optional(FEATURE_IMPLEMENTATION_DIR / "SKILL.md")
        allowed_metric_suffixes = build_allowed_metric_suffixes(fields_df, max_suffixes=300)

        allowed_operators = []
        if not args.no_operators_in_prompt:
            try:
                operators_df = ace_lib.get_operators(session)
                requested_vector = str(args.data_type).upper() == "VECTOR"
                detected_vector = _vector_ratio_from_datafields_df(fields_df) > 0.5
                keep_vector = requested_vector or detected_vector
                _, allowed_ops, _ = filter_operators_df(operators_df, keep_vector=keep_vector)
                if args.max_operators is not None and args.max_operators > 0:
                    allowed_operators = allowed_ops[: args.max_operators]
                else:
                    allowed_operators = allowed_ops
            except Exception as exc:
                print(f"Warning: failed to fetch/filter operators; continuing without operators in prompt. Error: {exc}", file=sys.stderr)

        api_key = (
            args.moonshot_api_key
            or os.environ.get("MOONSHOT_API_KEY")
        )
        if not api_key:
            raise ValueError("Moonshot API key missing. Set MOONSHOT_API_KEY or pass --moonshot-api-key")

        # Start with all fields; on token-limit errors halve and retry.
        current_max_fields = args.max_fields  # None means all
        max_token_retries = 5
        report = None
        for token_attempt in range(max_token_retries + 1):
            fields_summary, field_count = build_field_summary(fields_df, max_fields=current_max_fields)
            n_fields_in_prompt = len(fields_summary)

            system_prompt, user_prompt = build_prompt(
                dataset_id=args.dataset_id,
                dataset_name=dataset_name,
                dataset_description=dataset_description,
                data_category=args.data_category,
                region=args.region,
                delay=args.delay,
                universe=args.universe,
                data_type=args.data_type,
                fields_summary=fields_summary,
                field_count=field_count,
                feature_engineering_skill_md=feature_engineering_skill_md,
                feature_implementation_skill_md=feature_implementation_skill_md,
                allowed_metric_suffixes=allowed_metric_suffixes,
                allowed_operators=allowed_operators,
                system_prompt_override=(os.environ.get("PIPELINE_GENERATE_SYSTEM_PROMPT") or "").strip() or None,
            )

            try:
                report = call_moonshot(api_key, args.moonshot_model, system_prompt, user_prompt)
                break
            except Exception as exc:
                err_msg = str(exc).lower()
                is_token_error = any(kw in err_msg for kw in ("token", "context_length", "too long", "too large", "413", "400"))
                if is_token_error and n_fields_in_prompt > 10:
                    current_max_fields = max(10, n_fields_in_prompt // 2)
                    print(
                        f"[token-limit] Reducing fields from {n_fields_in_prompt} to {current_max_fields} "
                        f"(attempt {token_attempt + 1}/{max_token_retries})",
                        file=sys.stderr,
                    )
                    continue
                raise

        if report is None:
            raise RuntimeError("Failed to get LLM response after reducing fields.")
        # Save first, then normalize placeholders after dataset download.
        ideas_path = save_ideas_report(report, args.region, args.delay, args.dataset_id)

    ideas_text = ideas_path.read_text(encoding="utf-8")

    # Ensure metadata exists for downstream parsing/reuse.
    ideas_text = ensure_metadata_block(ideas_text, dataset_id=args.dataset_id, region=args.region, delay=args.delay)
    ideas_path.write_text(ideas_text, encoding="utf-8")

    # Parse metadata
    dataset_id_match = re.search(r"\*\*Dataset\*\*:\s*(\S+)", ideas_text)
    dataset_id = dataset_id_match.group(1) if dataset_id_match else args.dataset_id

    # Download dataset for implementation
    fetch_script = FEATURE_IMPLEMENTATION_SCRIPTS / "fetch_dataset.py"
    run_script(
        [
            sys.executable,
            str(fetch_script),
            "--datasetid",
            dataset_id,
            "--region",
            args.region,
            "--delay",
            str(args.delay),
            "--universe",
            args.universe,
            "--instrument-type",
            args.instrument_type,
            "--data-type",
            args.data_type,
        ],
        cwd=FEATURE_IMPLEMENTATION_SCRIPTS,
    )

    dataset_folder = f"{safe_dataset_id(dataset_id)}_{args.region}_delay{args.delay}"

    # If the ideas file references a different dataset id than the CLI args,
    # ensure we also clean that dataset folder before fetching.
    if dataset_folder != guessed_dataset_folder:
        delete_path_if_exists(FEATURE_IMPLEMENTATION_DIR / "data" / dataset_folder)

    dataset_csv_path = FEATURE_IMPLEMENTATION_DIR / "data" / dataset_folder / f"{dataset_folder}.csv"
    if not dataset_csv_path.exists():
        raise RuntimeError(
            "Dataset CSV was not created by fetch_dataset.py. "
            f"Expected: {dataset_csv_path}"
        )
    dataset_ids = load_dataset_ids_from_csv(dataset_csv_path)
    allowed_suffixes = build_allowed_suffixes_from_ids(dataset_ids, max_suffixes=300) if dataset_ids else []
    dataset_code = detect_dataset_code(dataset_ids) if dataset_ids else None

    # Extract {template, idea} pairs from **Concept** blocks.
    block_pairs = extract_template_blocks(ideas_text)
    if not block_pairs:
        raise ValueError("No **Concept** blocks with **Implementation Example** found in the ideas file.")

    normalized_pairs: list[tuple[str, str]] = []
    for item in block_pairs:
        t = str(item.get("template") or "").strip()
        idea_text = str(item.get("idea") or "").strip()
        if not t:
            continue

        if dataset_ids and allowed_suffixes:
            normalized_t, ok = normalize_template_placeholders(t, dataset_ids, allowed_suffixes, dataset_code)
            if not ok:
                continue
            normalized_pairs.append((normalized_t, idea_text))
        else:
            # No dataset ids to validate against; pass through.
            normalized_pairs.append((t, idea_text))

    if not normalized_pairs:
        raise ValueError("No valid templates remain after normalization/validation.")

    # De-dup by template; keep the first non-empty idea.
    template_to_idea: dict[str, str] = {}
    for t, idea_text in normalized_pairs:
        if t not in template_to_idea or (not template_to_idea[t] and idea_text):
            template_to_idea[t] = idea_text

    templates = sorted(template_to_idea.keys())

    implement_script = FEATURE_IMPLEMENTATION_SCRIPTS / "implement_idea.py"

    for template in templates:
        idea_text = template_to_idea.get(template, "")
        run_script(
            [
                sys.executable,
                str(implement_script),
                "--template",
                template,
                "--dataset",
                dataset_folder,
                "--idea",
                idea_text,
            ],
            cwd=FEATURE_IMPLEMENTATION_SCRIPTS,
        )

    merge_script = FEATURE_IMPLEMENTATION_SCRIPTS / "merge_expression_list.py"
    run_script(
        [
            sys.executable,
            str(merge_script),
            "--dataset",
            dataset_folder,
        ],
        cwd=FEATURE_IMPLEMENTATION_SCRIPTS,
    )

    final_path = FEATURE_IMPLEMENTATION_DIR / "data" / dataset_folder / "final_expressions.json"
    if final_path.exists():
        try:
            raw = json.loads(final_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Failed to read final expressions: {final_path}. Error: {exc}")

        expressions = raw if isinstance(raw, list) else []
        validator = ExpressionValidator()
        valid_expressions: list[str] = []
        invalid_count = 0
        for expr in expressions:
            if not isinstance(expr, str) or not expr.strip():
                invalid_count += 1
                continue
            result = validator.check_expression(expr.strip())
            if result.get("valid"):
                valid_expressions.append(expr.strip())
            else:
                invalid_count += 1

        final_path.write_text(json.dumps(valid_expressions, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"Filtered invalid expressions: {invalid_count}")
    else:
        print(f"Warning: final_expressions.json not found: {final_path}")

    print(f"Ideas report: {ideas_path}")
    print(f"Expressions: {FEATURE_IMPLEMENTATION_DIR / 'data' / dataset_folder / 'final_expressions.json'}")


if __name__ == "__main__":
    main()
