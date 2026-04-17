import pandas as pd
from pathlib import Path
import argparse
import sys
import re
import json
import time
import itertools


def _safe_filename_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")


def _parse_dataset_folder_parts(dataset_folder_name: str) -> tuple[str, str, str] | None:
    """Parse '<datasetId>_<REGION>_delay<DELAY>' into (datasetId, REGION, DELAY).

    Returns None if parsing fails.
    """

    name = str(dataset_folder_name)
    marker = "_delay"
    pos = name.rfind(marker)
    if pos == -1:
        return None

    prefix = name[:pos]
    delay_str = name[pos + len(marker) :]
    if not delay_str.isdigit():
        return None

    region_pos = prefix.rfind("_")
    if region_pos == -1:
        return None

    dataset_id = prefix[:region_pos]
    region = prefix[region_pos + 1 :]
    if not dataset_id or not region:
        return None

    return dataset_id, region, delay_str

def load_data(dataset_name=None):
    script_dir = Path(__file__).resolve().parent
    workspace_dir = script_dir.parent
    
    if not dataset_name:
        data_root = workspace_dir / "data"
        if not data_root.exists():
            print("Error: Data directory not found.", file=sys.stderr)
            sys.exit(1)
            
        subdirs = [d for d in data_root.iterdir() if d.is_dir()]
        
        if len(subdirs) == 1:
            dataset_name = subdirs[0].name
            print(f"Auto-detected dataset: {dataset_name}", file=sys.stderr)
        elif len(subdirs) > 1:
            print("Error: Multiple datasets found. Please specify --dataset.", file=sys.stderr)
            print("Available datasets:", file=sys.stderr)
            for d in subdirs:
                print(f"  {d.name}", file=sys.stderr)
            sys.exit(1)
        else:
            print("Error: No dataset folders found inside data directory.", file=sys.stderr)
            sys.exit(1)

    dataset_dir = workspace_dir / "data" / dataset_name
    data_path = dataset_dir / f"{dataset_name}.csv"
    
    print(f"Loading data from {data_path}...", file=sys.stderr)
    try:
        df = pd.read_csv(data_path)
        return df, dataset_dir
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}. Please run fetch_dataset.py first.", file=sys.stderr)
        sys.exit(1)

def extract_keys_from_template(template):
    return re.findall(r'\{([A-Za-z0-9_]+)\}', template)


def _matches_metric(field_id: str, metric: str) -> bool:
    """Return True if field_id is a plausible match for metric.

    For very short metrics, require token-boundary matches to avoid accidental
    matches (e.g. 'ta' in 'total').
    """

    fid = str(field_id)
    m = str(metric)
    if len(m) <= 3:
        return re.search(rf"(^|_){re.escape(m)}(_|$)", fid, flags=re.IGNORECASE) is not None
    return m in fid


def _common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i

def match_single_horizon_auto(df, template):
    """Generate expressions from a template by matching each {variable} to dataset field ids.

    Previous behavior required all variables to share an identical "base prefix".
    That is often too strict for datasets with mixed naming conventions.

    New behavior:
    - Build candidate lists per metric.
    - Iterate over a limited set of primary candidates.
    - For each primary candidate, pick the closest-looking candidates for other metrics
      (by common prefix length), but DO NOT require the same base.
    - Combine candidates (capped) and render expressions.
    """

    metrics = extract_keys_from_template(template)
    if not metrics:
        print("Error: No variables found in template (use {variable} format).", file=sys.stderr)
        return []

    metrics = sorted(metrics, key=len, reverse=True)
    primary = metrics[0]

    ids = df["id"].dropna().astype(str).tolist()

    # Build candidates per metric
    candidates_by_metric: dict[str, list[str]] = {}
    for m in metrics:
        cands = [fid for fid in ids if _matches_metric(fid, m)]
        # de-dup while preserving order
        seen = set()
        uniq = []
        for x in cands:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        candidates_by_metric[m] = uniq

    if not candidates_by_metric.get(primary):
        return []
    for m in metrics[1:]:
        if not candidates_by_metric.get(m):
            return []

    MAX_PRIMARY_CANDIDATES = 30
    MAX_SECONDARY_CHOICES = 8
    MAX_EXPRESSIONS = 5000

    results = []
    seen_expr = set()

    primary_candidates = candidates_by_metric[primary][:MAX_PRIMARY_CANDIDATES]
    for primary_id in primary_candidates:
        # For each secondary metric, choose best candidates by similarity to primary_id
        chosen_by_metric: dict[str, list[str]] = {primary: [primary_id]}
        for m in metrics[1:]:
            cands = candidates_by_metric[m]
            ranked = sorted(cands, key=lambda fid: _common_prefix_len(primary_id, fid), reverse=True)
            chosen_by_metric[m] = ranked[:MAX_SECONDARY_CHOICES]

        # Combine candidates across metrics
        metric_order = metrics
        pools = [chosen_by_metric[m] for m in metric_order]
        for combo in itertools.product(*pools):
            field_map = dict(zip(metric_order, combo))
            try:
                expr = template.format(**field_map)
            except Exception:
                continue
            if expr in seen_expr:
                continue
            seen_expr.add(expr)
            results.append(("flex", expr))
            if len(results) >= MAX_EXPRESSIONS:
                return results

    return results

def main():
    parser = argparse.ArgumentParser(description="Generate Alpha Expressions based on patterns")
    parser.add_argument("--template", required=True, help="Python format string (e.g. '{st_dev} / abs({mean})')")
    parser.add_argument("--dataset", help="Name of the dataset folder. Auto-detected if only one exists.")
    parser.add_argument(
        "--idea",
        default="",
        help="Optional natural-language description of what this template represents.",
    )
    
    args = parser.parse_args()
    
    df, dataset_dir = load_data(args.dataset)
    
    results = match_single_horizon_auto(df, args.template)
        
    # Output
    expression_list = []
    if not results:
        print("No matching expressions found.")
    else:
        print(f"Generated {len(results)} expressions:\n")
        # print(f"{'Context':<30} | Expression")
        # print("-" * 120)
        
        for context, expr in results:
            # print(f"{context:<30} | {expr}")
            expression_list.append(expr)
            
    # Save results to JSON (Always save for debugging)
    # Use nanosecond precision to avoid collisions when called in a tight loop.
    timestamp = time.time_ns()
    json_output = {
        "template": args.template,
        "idea": args.idea,
        "expression_list": expression_list
    }
    
    parts = _parse_dataset_folder_parts(dataset_dir.name)
    if parts:
        dataset_id, region, delay_str = parts
        prefix = f"{_safe_filename_component(dataset_id)}_{_safe_filename_component(region)}_{_safe_filename_component(delay_str)}"
    else:
        # Fallback: keep output stable even if dataset folder naming differs.
        prefix = _safe_filename_component(dataset_dir.name) or "dataset"

    output_file = dataset_dir / f"{prefix}_idea_{timestamp}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=4, ensure_ascii=False)
        print(f"\nSaved idea configuration to: {output_file}")
    except Exception as e:
        print(f"Error saving JSON: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
